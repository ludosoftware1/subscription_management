from django.apps import AppConfig


class EmailAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.email_app' # Mantém o nome do módulo para evitar conflitos de importação
    label = 'email' # Diz ao Django para usar 'email' como o rótulo para migrações
