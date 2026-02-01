from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.decorators import user_passes_test

def group_required(*group_names, login_url='account_login'):
    """
    Decorator para views que requer que o usuário seja membro de pelo menos um dos grupos especificados.
    Redireciona para a página de login se o usuário não estiver autenticado.
    Levanta PermissionDenied se o usuário estiver autenticado, mas não pertencer aos grupos.
    """
    def check_perms(user):
        if not user.is_authenticated:
            return False
        
        if user.is_superuser or user.groups.filter(name__in=group_names).exists():
            return True
        
        raise PermissionDenied
        
    return user_passes_test(check_perms, login_url=login_url)


class GroupRequiredMixin(AccessMixin):
    """
    Mixin para Class-Based Views que restringe o acesso a usuários em grupos específicos.
    """
    groups_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.groups_required is None:
            raise ValueError(
                f"{self.__class__.__name__} está usando GroupRequiredMixin, "
                "mas não definiu o atributo 'groups_required'."
            )

        user_groups = set(g.name for g in request.user.groups.all())
        required_groups = set(self.groups_required)

        if not user_groups.intersection(required_groups) and not request.user.is_superuser:
            # Retorna uma resposta 403 Forbidden
            return self.handle_no_permission()
            
        return super().dispatch(request, *args, **kwargs)
