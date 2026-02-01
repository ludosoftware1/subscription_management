import uuid
import qrcode
import io
import base64


def gerar_codigo_verificacao():
    """
    Gera um código de verificação alfanumérico único de 32 caracteres.
    Utiliza o UUID4 e o retorna como uma string hexadecimal.
    """
    return uuid.uuid4().hex


def gerar_qr_code_base64(data_to_encode):
    """
    Gera uma imagem de QR Code a partir de uma string e a retorna como uma
    string Base64 formatada para uso direto em tags <img> de HTML.

    :param data_to_encode: A string (URL, texto, etc.) a ser codificada no QR Code.
    :return: Uma string no formato 'data:image/png;base64,...'.
    """
    qr_img = qrcode.make(data_to_encode)
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{qr_code_base64}"