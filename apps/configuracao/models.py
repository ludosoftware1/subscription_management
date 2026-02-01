from django.db import models
from auditlog.models import LogEntry
from django.utils.html import format_html
from .models_configuracao import ConfiguracaoSite, ConfiguracaoEmail

class AuditLogEntry(LogEntry):
    """
    Um proxy para o LogEntry do django-auditlog.
    Permite adicionar métodos customizados sem criar uma nova tabela no banco.
    """
    class Meta:
        proxy = True

# Exporta ConfiguracaoSite e ConfiguracaoEmail para manter compatibilidade com imports existentes
__all__ = ['AuditLogEntry', 'ConfiguracaoSite', 'ConfiguracaoEmail']
