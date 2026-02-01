from django.shortcuts import redirect
from django.urls import reverse

class LockScreenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Só aplica o middleware se o usuário estiver autenticado
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Caminhos que devem ser permitidos mesmo com a tela bloqueada
        allowed_paths = [
            reverse('pages:unlock_screen'),
            reverse('account_logout'),
        ]

        # Se a sessão está bloqueada e o usuário não está em uma página permitida, redireciona
        if request.session.get('is_locked') and request.path not in allowed_paths:
            return redirect('pages:unlock_screen')

        response = self.get_response(request)
        return response


class CacheControlMiddleware:
    """
    Middleware para controlar o cache das respostas HTTP.
    Adiciona headers apropriados para evitar cache de páginas HTML em produção.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Verifica se é uma resposta HTML (páginas)
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            # Headers para impedir cache das páginas HTML
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response
