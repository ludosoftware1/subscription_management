from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Notificacao

@login_required
def api_notificacoes_nao_lidas(request):
    """
    Retorna as notificações não lidas do usuário em formato JSON.
    """
    notificacoes = Notificacao.objects.filter(destinatario=request.user, lida=False)
    
    data = {
        'count': notificacoes.count(),
        'notificacoes': [
            {
                'id': n.id,
                'titulo': n.titulo,
                'mensagem': n.mensagem,
                'timestamp': n.timestamp.strftime('%d de %b, %Y %H:%M'),
                'url': n.get_absolute_url()
            }
            for n in notificacoes[:5] # Limita a 5 para não sobrecarregar o dropdown
        ]
    }
    return JsonResponse(data)

@login_required
@require_POST
def api_marcar_como_lida(request):
    """
    Marca todas as notificações do usuário como lidas.
    """
    Notificacao.objects.filter(destinatario=request.user, lida=False).update(lida=True)
    return JsonResponse({'status': 'ok'})

