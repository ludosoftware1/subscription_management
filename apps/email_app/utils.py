import json
import requests
import uuid
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from .models import EmailLog
from apps.configuracao.models import ConfiguracaoSite, ConfiguracaoEmail

def send_templated_email(template_name, subject, to_email, context, request=None, attachments=None):
    """
    Envia um e-mail utilizando um template HTML e a API externa de notificação.
    Busca as configurações de SMTP do banco de dados.
    """
    if attachments is None:
        attachments = []

    try:
        # Busca as configurações de e-mail do banco de dados
        
        config_email = ConfiguracaoEmail.objects.first()
        if not config_email:
            log = EmailLog.objects.create(
                internal_id=uuid.uuid4(),
                to=[to_email],
                sender="sistema@example.com", # Remetente genérico para o log
                subject=subject,
                body="Configurações de e-mail não encontradas no banco de dados.",
                status='failed',
                details="Não foi possível enviar o e-mail: Configurações de e-mail não encontradas no banco de dados."
            )
            print(f"ERRO: Configurações de e-mail não encontradas no banco de dados. Log ID: {log.pk}")
            return False

        SMTP_HOST = config_email.smtp_host
        SMTP_PORT = config_email.smtp_port
        SMTP_USER = config_email.smtp_user
        SMTP_PASSWORD = config_email.smtp_password

        # Renderiza o template HTML com o contexto fornecido
        # Adiciona o prefixo 'email/' se não estiver presente
        if not template_name.startswith('email/'):
            template_path = f'email/{template_name}'
        else:
            template_path = template_name
        
        html_body = render_to_string(template_path, context)

        # Configurações da API externa
        NOTIFICATION_API_URL = 'https://notification-center.onrender.com/api/v1/email/send-email'
        # O token de autorização da API será lido das configurações do Django (settings.py)
        API_AUTH_TOKEN = settings.API_AUTH_TOKEN
        # O webhook_token será lido das configurações do Django (settings.py)
        WEBHOOK_TOKEN = settings.NOTIFICATION_WEBHOOK_TOKEN

        # Cria um log de e-mail
        log = EmailLog.objects.create(
            internal_id=uuid.uuid4(),
            to=[to_email],
            sender=SMTP_USER,
            subject=subject,
            body=html_body,
            status='sending'
        )

        callback_url = None
        if request:
            callback_url = request.build_absolute_uri(reverse('email:email_callback', kwargs={'internal_id': log.internal_id}))
        
        payload = {
            "to": [to_email],
            "subject": subject,
            "body": "", # Adicionado campo 'body' conforme documentação da API
            "html_body": html_body,
            "smtp_config": {
                "smtp_host": SMTP_HOST,
                "smtp_port": SMTP_PORT,
                "smtp_user": SMTP_USER,
            "smtp_password": SMTP_PASSWORD
            },
            "callback_url": callback_url,
            "webhook_token": WEBHOOK_TOKEN # Adiciona o webhook_token ao payload
        }

        if attachments:
            payload['attachments'] = attachments

        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_AUTH_TOKEN}' # Reintroduz o cabeçalho Authorization
        }
        
        print(f"DEBUG: Enviando requisição para {NOTIFICATION_API_URL}")
        print(f"DEBUG: Headers: {headers}")
        print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}") # Imprime o payload formatado
        
        response = requests.post(NOTIFICATION_API_URL, headers=headers, data=json.dumps(payload))
        
        response.raise_for_status() # Levanta um erro para status de resposta HTTP ruins (4xx ou 5xx)

        log.details = response.text
        log.save()
        return True

    except requests.exceptions.RequestException as e:
        print(f"ERRO CRÍTICO ao enviar e-mail para {to_email} (RequestException): {e}")
        if 'log' in locals():
            log.status = 'failed'
            log.details = str(e)
            log.save()
        return False
    except Exception as e:
        print(f"ERRO CRÍTICO inesperado ao enviar e-mail para {to_email} (Exception): {e}")
        if 'log' in locals():
            log.status = 'failed'
            log.details = str(e)
            log.save()
        return False
