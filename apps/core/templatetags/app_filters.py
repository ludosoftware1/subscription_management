from django import template

register = template.Library()

@register.filter
def get_app_label(obj):
    """Retorna o app_label de um objeto de modelo."""
    return obj._meta.app_label

@register.filter
def get_model_name(obj):
    """Retorna o model_name de um objeto de modelo."""
    return obj._meta.model_name