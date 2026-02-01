from django.apps import AppConfig
from django.db.models.signals import post_migrate

def criar_grupo_administrador(sender, **kwargs):
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='administrador')

class ConfiguracaoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.configuracao'

    def ready(self):
        post_migrate.connect(criar_grupo_administrador, sender=self)
