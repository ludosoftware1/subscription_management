from .models_configuracao import ConfiguracaoSite

def configuracao_site(request):
    configuracao, created = ConfiguracaoSite.objects.get_or_create(pk=1)
    return {'configuracao_site': configuracao}
