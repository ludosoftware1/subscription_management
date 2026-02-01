import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='json_format')
def json_format(value):
    """
    Extrai a mensagem de uma string JSON ou retorna o valor original.
    """
    try:
        data = json.loads(value)
        if isinstance(data, dict) and 'message' in data:
            return data['message']
        return value
    except (json.JSONDecodeError, TypeError):
        return value
