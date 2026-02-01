from .models_configuracao import ConfiguracaoSite

def get_configuracao_site():
    configuracao, created = ConfiguracaoSite.objects.get_or_create(pk=1)
    return configuracao
