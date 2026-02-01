from django.apps import AppConfig


class RelatoriosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.relatorios'

    def ready(self):
        # Registrar modelos para auditoria
        from auditlog.registry import auditlog
        from .models import HistoricoRelatorio

        auditlog.register(HistoricoRelatorio)
