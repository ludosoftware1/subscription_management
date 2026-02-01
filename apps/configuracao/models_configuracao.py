from django.db import models

class ConfiguracaoSite(models.Model):
    logo_principal = models.ImageField(upload_to='configuracao/', blank=True, null=True, help_text="Logo principal do sistema.")
    favicon = models.FileField(upload_to='configuracao/', blank=True, null=True, help_text="Ícone do navegador (favicon).")
    logo_login = models.ImageField(upload_to='configuracao/', blank=True, null=True, help_text="Imagem de fundo para a tela de login.")
    subtitulo_login = models.CharField(max_length=200, blank=True, null=True, help_text="Frase exibida abaixo da logo na tela de login.")

    # Informações institucionais da prefeitura
    nome_prefeitura = models.CharField(max_length=200, blank=True, null=True, help_text="Nome completo da prefeitura.")
    endereco_prefeitura = models.TextField(blank=True, null=True, help_text="Endereço completo da prefeitura.")
    telefone_prefeitura = models.CharField(max_length=50, blank=True, null=True, help_text="Telefone da prefeitura.")
    cnpj_prefeitura = models.CharField(max_length=20, blank=True, null=True, help_text="CNPJ da prefeitura.")
    email_prefeitura = models.EmailField(blank=True, null=True, help_text="E-mail institucional da prefeitura.")

    footer_text1 = models.CharField(max_length=200, blank=True, null=True, help_text="Texto do rodapé (linha 1).")
    footer_text2 = models.CharField(max_length=200, blank=True, null=True, help_text="Texto do rodapé (linha 2).")

    def __str__(self):
        return "Configurações do Site"

    class Meta:
        verbose_name = "Configuração do Site"
        verbose_name_plural = "Configurações do Site"


class ConfiguracaoEmail(models.Model):
    """
    Modelo para armazenar as configurações de e-mail/SMTP do sistema.
    """
    smtp_host = models.CharField(
        max_length=255,
        default='smtp.hostinger.com',
        help_text="Servidor SMTP (ex: smtp.gmail.com, smtp.hostinger.com)"
    )
    smtp_port = models.IntegerField(
        default=587,
        help_text="Porta do servidor SMTP (ex: 587 para TLS, 465 para SSL, 25 para não criptografado)"
    )
    smtp_user = models.EmailField(
        max_length=255,
        help_text="Usuário/e-mail para autenticação SMTP"
    )
    smtp_password = models.CharField(
        max_length=255,
        help_text="Senha para autenticação SMTP"
    )
    use_tls = models.BooleanField(
        default=True,
        help_text="Usar TLS (Transport Layer Security)"
    )
    use_ssl = models.BooleanField(
        default=False,
        help_text="Usar SSL (Secure Sockets Layer)"
    )
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Configurações de E-mail"

    class Meta:
        verbose_name = "Configuração de E-mail"
        verbose_name_plural = "Configurações de E-mail"
