import qrcode
import base64
from io import BytesIO
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def qr_from_text(text, size=6, border=1):
    """
    Gera uma imagem de QR Code em base64 a partir de um texto.
    Uso: {% qr_from_text 'meu texto' size=10 %}
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return mark_safe(f'<img src="data:image/png;base64,{img_str}" alt="QR Code">')