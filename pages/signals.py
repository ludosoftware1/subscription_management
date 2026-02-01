from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from auditlog.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from apps.core.models import UserSession

User = get_user_model()

# Definindo a nova ação de LOGIN. Usaremos o número 3.
LOGIN_ACTION = 3

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Cria um registro na trilha de auditoria e uma UserSession sempre que um usuário faz login.
    """
    # Obtém o ContentType para o modelo User
    user_content_type = ContentType.objects.get_for_model(user)

    # Cria registro na trilha de auditoria
    LogEntry.objects.create(
        actor=user,
        content_type=user_content_type,
        object_pk=user.pk,
        object_repr=str(user),
        action=LOGIN_ACTION, # Ação customizada para Login
        additional_data={'ip': request.META.get('REMOTE_ADDR')},
    )

    # Cria registro da sessão do usuário
    UserSession.objects.create(
        user=user,
        session_key=request.session.session_key,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Registra o logout do usuário atualizando a sessão ativa.
    """
    if hasattr(request, 'session') and request.session.session_key:
        try:
            # Encontra a sessão ativa mais recente do usuário
            session = UserSession.objects.filter(
                user=user,
                session_key=request.session.session_key,
                is_active=True
            ).latest('login_time')

            # Marca a sessão como inativa
            session.end_session()
        except UserSession.DoesNotExist:
            # Se não encontrar uma sessão ativa, não faz nada
            pass
