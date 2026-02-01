import json
import requests
import uuid
import base64
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import EmailLog
from .forms import EmailTestForm
from .utils import send_templated_email

class TestEmailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = EmailTestForm()
        logs = EmailLog.objects.all().order_by('-created_at')
        return render(request, 'email/test_page.html', {'form': form, 'logs': logs})

    def post(self, request, *args, **kwargs):
        form = EmailTestForm(request.POST, request.FILES)
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            template_name = form.cleaned_data['template_name']
            observacao = form.cleaned_data['observacao']
            attachment = request.FILES.get('attachment')

            # Assunto fixo para e-mails de teste
            fixed_subject = f"E-mail de Teste - {template_name.replace('.html', '').replace('_', ' ').title()}"

            # Criar contexto genérico para o template
            class MockRequerente:
                def get_full_name(self):
                    return "Requerente de Teste"
                @property
                def username(self):
                    return "requerente.teste"

            class MockSolicitacao:
                requerente = MockRequerente()
                nome_evento = "Evento de Teste (Solicitação)"
                protocolo = "SOL-12345"
                data_solicitacao = "DD/MM/AAAA"
                status_solicitacao = "Aprovada"

            class MockInscricao:
                cidadao = MockRequerente() # Reutilizando MockRequerente para o cidadão da inscrição
                nome_evento = "Evento de Teste (Inscrição)"
                numero_inscricao = "INS-67890"
                data_inscricao = "DD/MM/AAAA"
                status_inscricao = "Confirmada"

            context = {
                'nome_usuario': 'Usuário de Teste',
                'nome_evento': 'Evento de Teste',
                'data_evento': 'DD/MM/AAAA',
                'local_evento': 'Local de Teste',
                'link_confirmacao': 'http://link.de.confirmacao/teste',
                'motivo_reprovacao': observacao if observacao else 'Motivo genérico de reprovação.',
                'pendencias': observacao if observacao else 'Pendências genéricas a serem resolvidas.',
                'observacao': observacao,
                'protocolo': 'ABC-12345',
                'link_acompanhamento': 'http://link.de.acompanhamento/teste',
                'nome_cidadao': 'Cidadão de Teste',
                'nome_gestor': 'Gestor de Teste',
                'data_solicitacao': 'DD/MM/AAAA',
                'status_solicitacao': 'Em Análise',
                'link_inscricao': 'http://link.de.inscricao/teste',
                'data_inscricao': 'DD/MM/AAAA',
                'numero_inscricao': 'INS-67890',
                'link_detalhes_evento': 'http://link.de.detalhes/teste',
                'nome_comerciante': 'Comerciante de Teste',
                'cnpj_comerciante': 'XX.XXX.XXX/XXXX-XX',
                'email_suporte': 'suporte@ludosoftware.com.br',
                'telefone_suporte': '(XX) XXXX-XXXX',
                'endereco_empresa': 'Endereço da Empresa, Cidade - UF',
                'site_empresa': request.build_absolute_uri('/') if request else 'http://site.de.teste/',
                'ano_atual': '2025',
                'logo_url': request.build_absolute_uri('/static/images/logo-dark.png') if request else 'http://logo.url/teste.png', # Exemplo de URL de logo
                'alvara_url': 'http://alvara.url/teste.pdf', # Exemplo de URL de alvará
                'solicitacao': MockSolicitacao(),
                'inscricao': MockInscricao(),
            }

            # Adicionar anexo se existir
            attachments = []
            if attachment:
                encoded_content = base64.b64encode(attachment.read()).decode('utf-8')
                attachments.append({
                    "filename": attachment.name,
                    "content": encoded_content
                })

            success = send_templated_email(
                template_name=template_name,
                subject=fixed_subject,
                to_email=to_email,
                context=context,
                request=request,
                attachments=attachments
            )

            if success:
                messages.success(request, f"E-mail de teste '{template_name}' para {to_email} enfileirado com sucesso!")
            else:
                messages.error(request, f"Falha ao enfileirar o e-mail de teste '{template_name}' para {to_email}.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo '{form[field].label}': {error}")
        
        return redirect('email:test_email_page')

test_email_page = TestEmailView.as_view()

@csrf_exempt
def email_callback(request, internal_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log = EmailLog.objects.get(internal_id=internal_id)
            log.job_id = data.get('job_id')
            log.status = data.get('status', 'unknown')
            log.details = json.dumps(data)
            log.save()
            return JsonResponse({'status': 'success'})
        except (json.JSONDecodeError, EmailLog.DoesNotExist, Exception) as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def resend_email(request, log_id):
    try:
        log = EmailLog.objects.get(id=log_id)
        if not log.internal_id:
            log.internal_id = uuid.uuid4()
        log.status = 'sending'
        log.details = 'Reenviando...'
        log.save()

        # Busca as configurações de e-mail do banco de dados
        from apps.configuracao.models import ConfiguracaoEmail
        try:
            config_email = ConfiguracaoEmail.objects.get(pk=1)
            SMTP_HOST = config_email.smtp_host
            SMTP_PORT = config_email.smtp_port
            SMTP_USER = config_email.smtp_user
            SMTP_PASSWORD = config_email.smtp_password
        except ConfiguracaoEmail.DoesNotExist:
            messages.error(request, "Configurações de e-mail não encontradas. Configure em Configurações > Configurações de E-mail.")
            return redirect('email:test_email_page')

        url = 'https://notification-center.onrender.com/api/v1/email/send-email'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': 'Bearer 3VzEMlLoZGJvx8OGOz2RhTdGLIIXo6LjKiqwf6gKTdscrJkXIC656cCmsjotHrRu'
        }
        
        callback_url = request.build_absolute_uri(reverse('email:email_callback', kwargs={'internal_id': log.internal_id}))

        payload = {
            "to": log.to,
            "subject": log.subject,
            "body": log.body,
            "smtp_config": {
                "smtp_host": SMTP_HOST,
                "smtp_port": SMTP_PORT,
                "smtp_user": SMTP_USER,
                "smtp_password": SMTP_PASSWORD
            },
            "callback_url": callback_url,
            "webhook_token": "token-de-teste"
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            log.details = response.text
            log.save()
            messages.success(request, f"E-mail para {log.to[0]} reenviado para a fila.")
        except requests.exceptions.RequestException as e:
            log.status = 'failed'
            log.details = str(e)
            log.save()
            messages.error(request, f"Erro de conexão ao tentar reenviar o e-mail: {e}")
            
    except EmailLog.DoesNotExist:
        messages.error(request, "Log de e-mail não encontrado.")

    return redirect('email:test_email_page')
