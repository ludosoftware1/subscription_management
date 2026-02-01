from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from apps.email_app.utils import send_templated_email # Importar a função
from django.template.loader import render_to_string # Importar para renderizar o assunto

class MyAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        """
        Sobrescreve o método send_mail do allauth para usar nossa função customizada.
        """
        # O allauth passa o template_prefix como 'account/email/password_reset_key'
        # O assunto é geralmente construído a partir do template_prefix
        subject_template_name = f"{template_prefix}_subject.txt"
        subject = render_to_string(subject_template_name, context).strip()
        
        template_name = "email/password_reset_email.html"
        
        custom_context = {
            'user': context['user'],
            'reset_link': context['password_reset_url'], # allauth fornece 'password_reset_url'
        }

        send_templated_email(
            template_name=template_name,
            subject=subject,
            to_email=email,
            context=custom_context,
            request=context.get('request') # allauth pode passar o request no contexto
        )

    def get_login_redirect_url(self, request):
        """
        Redireciona o usuário para a página inicial após o login.
        """
        return '/'
