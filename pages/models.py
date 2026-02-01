from django.db import models
from auditlog.models import LogEntry
from django.utils.html import format_html

class AuditLogEntry(LogEntry):
    """
    Um proxy para o LogEntry do django-auditlog.
    Permite adicionar métodos customizados sem criar uma nova tabela no banco.
    """
    class Meta:
        proxy = True

