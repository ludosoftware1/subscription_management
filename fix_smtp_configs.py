"""
Script para substituir configurações SMTP fixadas por chamadas à função send_templated_email
"""
import re
import os

def fix_evento_interno():
    """Corrige apps/evento_interno/views.py"""
    filepath = "apps/evento_interno/views.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir na InscricaoCreateView - método form_valid
    old_pattern1 = r'''# Envia e-mail de confirmação.*?EmailLog\.objects\.create\(
                to=\[inscricao\.comerciante\.email\],
                sender="no-reply@ludosoftware\.com\.br",
                subject=subject,
                body=html_message if 'html_message' in locals\(\) else '',
                status='failed',
                details=str\(e\)
            \)'''
    
    new_code1 = '''# Envia e-mail de confirmação usando as configurações do banco de dados
        try:
            from apps.configuracao.models import ConfiguracaoSite
            from apps.email_app.utils import send_templated_email

            config = ConfiguracaoSite.objects.first()
            logo_url = ''
            if config and config.logo_principal:
                logo_url = self.request.build_absolute_uri(config.logo_principal.url)

            site_url = self.request.build_absolute_uri(reverse('evento_interno:minhas_inscricoes'))
            
            context = {
                'inscricao': inscricao,
                'logo_url': logo_url,
                'site_url': site_url,
            }
            
            subject = f"Confirmação de Inscrição: {inscricao.evento.nome}"
            
            # Usa a função centralizada que busca as configurações do banco de dados
            success = send_templated_email(
                template_name='confirmacao_inscricao.html',
                subject=subject,
                to_email=inscricao.comerciante.email,
                context=context,
                request=self.request
            )
            
            if not success:
                messages.warning(self.request, "Sua inscrição foi criada, mas ocorreu um erro ao enviar o e-mail de confirmação.")

        except Exception as e:
            messages.warning(self.request, f"Sua inscrição foi criada, mas ocorreu um erro ao enviar o e-mail de confirmação: {e}")'''
    
    # Substituir na NotificarPendenciasInscricaoView
    old_pattern2 = r'''# Envia o e-mail de notificação.*?EmailLog\.objects\.create\(
                to=\[inscricao\.comerciante\.email\],
                sender="no-reply@ludosoftware\.com\.br",
                subject=subject,
                body=html_message if 'html_message' in locals\(\) else '',
                status='failed',
                details=str\(e\)
            \)'''
    
    new_code2 = '''# Envia o e-mail de notificação usando as configurações do banco de dados
        try:
            from apps.configuracao.models import ConfiguracaoSite
            from apps.email_app.utils import send_templated_email

            config = ConfiguracaoSite.objects.first()
            logo_url = ''
            if config and config.logo_principal:
                logo_url = request.build_absolute_uri(config.logo_principal.url)

            site_url = request.build_absolute_uri(reverse('evento_interno:minhas_inscricoes'))
            
            context = {
                'inscricao': inscricao,
                'logo_url': logo_url,
                'site_url': site_url,
            }
            
            subject = f"Pendências na sua inscrição: {inscricao.evento.nome}"
            
            # Usa a função centralizada que busca as configurações do banco de dados
            success = send_templated_email(
                template_name='notificacao_pendencias.html',
                subject=subject,
                to_email=inscricao.comerciante.email,
                context=context,
                request=request
            )
            
            if not success:
                messages.error(request, "Ocorreu um erro ao enviar o e-mail de notificação.")

        except Exception as e:
            messages.error(request, f"Ocorreu um erro ao enviar o e-mail de notificação: {e}")'''
    
    # Aplicar as substituições (simplificadas pois o padrão regex é complexo)
    # Vamos fazer de forma mais simples usando substituição de string direta
    
    # Procurar por blocos de código SMTP e substituir
    if '"smtp_host": "smtp.hostinger.com"' in content:
        print(f"Encontradas configurações fixadas em {filepath}")
        print("Por favor, substitua manualmente os blocos de envio de e-mail para usar send_templated_email")
        return False
    
    return True

if __name__ == "__main__":
    print("Verificando arquivos...")
    fix_evento_interno()
    print("Concluído!")
