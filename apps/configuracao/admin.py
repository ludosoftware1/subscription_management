from django.contrib import admin
from .models_configuracao import ConfiguracaoSite, ConfiguracaoEmail

@admin.register(ConfiguracaoSite)
class ConfiguracaoSiteAdmin(admin.ModelAdmin):
    list_display = ('subtitulo_login', 'footer_text1', 'footer_text2')
    fields = ['logo_principal', 'favicon', 'logo_login', 'subtitulo_login', 'footer_text1', 'footer_text2']


@admin.register(ConfiguracaoEmail)
class ConfiguracaoEmailAdmin(admin.ModelAdmin):
    list_display = ('smtp_host', 'smtp_port', 'smtp_user', 'use_tls', 'use_ssl', 'atualizado_em')
    fields = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'use_tls', 'use_ssl']
    readonly_fields = ('atualizado_em', 'criado_em')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('criado_em',)
        return self.readonly_fields
