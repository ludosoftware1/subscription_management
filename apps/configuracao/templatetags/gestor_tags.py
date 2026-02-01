from django import template
from datetime import timedelta
import locale

register = template.Library()

@register.filter
def format_duration(value):
    """
    Formata uma duração (timedelta) em um formato legível.
    Exemplo: 2h 30m 15s
    """
    if not isinstance(value, timedelta):
        return value

    total_seconds = int(value.total_seconds())
    if total_seconds < 0:
        return "N/A"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:  # Sempre mostrar segundos se for 0 e não houver outras partes
        parts.append(f"{seconds}s")

    return " ".join(parts)

@register.filter
def format_currency(value):
    """
    Formata um valor numérico como moeda brasileira (R$).
    Exemplo: 1234.56 -> R$ 1.234,56
    """
    if value is None:
        return "R$ 0,00"

    try:
        # Tenta configurar locale para pt_BR
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except locale.Error:
            # Fallback se locale não estiver disponível
            pass

        # Converte para float se necessário
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        elif hasattr(value, '__float__'):
            value = float(value)

        # Formata como moeda
        formatted = locale.currency(value, grouping=True, symbol='R$ ')
        return formatted
    except (ValueError, TypeError):
        return f"R$ {value}"

@register.filter
def format_number(value, decimals=2):
    """
    Formata um número com separadores brasileiros.
    Exemplo: 1234.56 -> 1.234,56
    """
    if value is None:
        return "0,00"

    try:
        # Converte para float se necessário
        if isinstance(value, str):
            value = float(value.replace(',', '.'))
        elif hasattr(value, '__float__'):
            value = float(value)

        # Formata com separadores brasileiros
        formatted = f"{value:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return str(value)
