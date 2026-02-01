from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models_configuracao import ConfiguracaoSite, ConfiguracaoEmail
from .forms import ConfiguracaoSiteForm, ConfiguracaoEmailForm
from django.http import HttpResponseRedirect, JsonResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def remover_imagem(request, campo):
    configuracao = get_object_or_404(ConfiguracaoSite, pk=1)
    if hasattr(configuracao, campo):
        field = getattr(configuracao, campo)
        if field:
            field.delete(save=True)
            messages.success(request, f'A imagem do campo "{campo.replace("_", " ").title()}" foi removida.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def configuracao_site(request):
    configuracao, created = ConfiguracaoSite.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = ConfiguracaoSiteForm(request.POST, request.FILES, instance=configuracao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações salvas com sucesso!')
            return redirect('configuracao:configuracao_site')
    else:
        form = ConfiguracaoSiteForm(instance=configuracao)

    context = {
        'form': form,
        'configuracao': configuracao,
        'title': 'Configuração do Site',
        'pagetitle': 'Configurações'
    }
    return render(request, 'configuracao/configuracao_site.html', context)


def configuracao_email(request):
    """
    View para gerenciar as configurações de e-mail/SMTP do sistema.
    """
    configuracao, created = ConfiguracaoEmail.objects.get_or_create(pk=1)

    if request.method == 'POST':
        form = ConfiguracaoEmailForm(request.POST, instance=configuracao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de e-mail salvas com sucesso!')
            return redirect('configuracao:configuracao_email')
        else:
            messages.error(request, 'Erro ao salvar as configurações. Verifique os campos.')
    else:
        form = ConfiguracaoEmailForm(instance=configuracao)

    context = {
        'form': form,
        'configuracao': configuracao,
        'title': 'Configurações de E-mail',
        'pagetitle': 'Configurações de E-mail'
    }
    return render(request, 'configuracao/configuracao_email.html', context)


def testar_conexao_smtp(request):
    """
    View para testar a conexão SMTP com as configurações atuais.
    Retorna JSON com o resultado do teste.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        configuracao = ConfiguracaoEmail.objects.get(pk=1)
    except ConfiguracaoEmail.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Configurações de e-mail não encontradas. Por favor, configure primeiro.'
        }, status=404)
    
    server = None
    try:
        # Log de debug das configurações (sem mostrar senha completa)
        print(f"=== Testando SMTP ===")
        print(f"Host: {configuracao.smtp_host}")
        print(f"Porta: {configuracao.smtp_port}")
        print(f"Usuário: {configuracao.smtp_user}")
        print(f"TLS: {configuracao.use_tls}")
        print(f"SSL: {configuracao.use_ssl}")
        print(f"Senha (primeiros 3 chars): {configuracao.smtp_password[:3]}...")
        
        # Tenta estabelecer conexão com o servidor SMTP
        if configuracao.use_ssl:
            print("Conectando com SSL...")
            server = smtplib.SMTP_SSL(configuracao.smtp_host, configuracao.smtp_port, timeout=10)
            print("Conexão SSL estabelecida")
        else:
            print("Conectando sem SSL...")
            server = smtplib.SMTP(configuracao.smtp_host, configuracao.smtp_port, timeout=10)
            print("Conexão estabelecida")
            server.set_debuglevel(1)  # Ativa debug do SMTP
            server.ehlo()
            print("EHLO enviado")
            if configuracao.use_tls:
                print("Iniciando TLS...")
                server.starttls()
                print("TLS iniciado")
                server.ehlo()
                print("EHLO após TLS enviado")
        
        # Tenta fazer login
        print(f"Tentando login com usuário: {configuracao.smtp_user}")
        server.login(configuracao.smtp_user, configuracao.smtp_password)
        print("Login bem-sucedido!")
        
        # Tenta enviar um e-mail de teste para o próprio usuário
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Teste de Conexão SMTP'
        msg['From'] = configuracao.smtp_user
        msg['To'] = configuracao.smtp_user
        
        texto = 'Este é um e-mail de teste para verificar a conexão SMTP.'
        html = f'''
        <html>
            <body>
                <h2>Teste de Conexão SMTP</h2>
                <p>Este é um e-mail de teste enviado pelo sistema para verificar a conexão SMTP.</p>
                <p><strong>Configurações testadas:</strong></p>
                <ul>
                    <li>Servidor: {configuracao.smtp_host}</li>
                    <li>Porta: {configuracao.smtp_port}</li>
                    <li>Usuário: {configuracao.smtp_user}</li>
                    <li>TLS: {'Sim' if configuracao.use_tls else 'Não'}</li>
                    <li>SSL: {'Sim' if configuracao.use_ssl else 'Não'}</li>
                </ul>
                <p>Se você recebeu este e-mail, a conexão SMTP está funcionando corretamente!</p>
            </body>
        </html>
        '''
        
        part1 = MIMEText(texto, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        print("Enviando e-mail de teste...")
        server.sendmail(configuracao.smtp_user, configuracao.smtp_user, msg.as_string())
        print("E-mail enviado com sucesso!")
        server.quit()
        
        return JsonResponse({
            'success': True,
            'message': f'Conexão SMTP testada com sucesso! Um e-mail de teste foi enviado para {configuracao.smtp_user}'
        })
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"Erro de autenticação SMTP: {e}")
        error_msg = str(e)
        if 'Username and Password not accepted' in error_msg:
            return JsonResponse({
                'success': False,
                'message': 'Erro de autenticação: Usuário e/ou senha incorretos. Verifique também se você precisa ativar "acesso a apps menos seguros" ou usar uma senha de aplicativo específica.'
            }, status=400)
        return JsonResponse({
            'success': False,
            'message': f'Erro de autenticação SMTP. Detalhes: {error_msg}'
        }, status=400)
    except smtplib.SMTPConnectError as e:
        print(f"Erro de conexão SMTP: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao conectar ao servidor SMTP. Verifique o host e porta. Detalhes: {str(e)}'
        }, status=400)
    except smtplib.SMTPException as e:
        print(f"Erro SMTP genérico: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro SMTP: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"Erro inesperado: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Erro inesperado: {str(e)}'
        }, status=500)
    finally:
        if server:
            try:
                server.quit()
            except:
                pass
