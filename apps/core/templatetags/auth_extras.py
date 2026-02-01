from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica se um usuário pertence a um grupo específico.
    Uso no template: {% if user|has_group:"nome_do_grupo" %}
    """
    if user.is_authenticated:
        return user.groups.filter(name=group_name).exists()
    return False
