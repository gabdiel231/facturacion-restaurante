"""
Envío de facturas por correo electrónico usando Resend (https://resend.com).

Se cambió de SMTP directo a la API HTTPS de Resend porque muchos hostings
gratuitos (incluido el plan Free de Render) bloquean las conexiones
salientes por el puerto 587 (SMTP), lo que hacía que el envío se quedara
"colgado" hasta que el servidor mataba el proceso. La API de Resend
funciona por HTTPS (puerto 443), que sí está permitido en todas partes.

Configuración necesaria (variables de entorno):

    RESEND_API_KEY   -> la API key que Resend te da al crear una cuenta
    EMAIL_FROM       -> (opcional) remitente a mostrar, ej:
                         "Restaurante <facturas@tudominio.com>"
                         Si no la defines, se usa el remitente de pruebas
                         de Resend (onboarding@resend.dev).

Cómo obtener tu API key:
    1. Crea una cuenta gratis en https://resend.com
    2. Ve a "API Keys" -> "Create API Key"
    3. Copia la key (empieza con "re_") y guárdala como RESEND_API_KEY

Nota importante sobre el remitente de pruebas:
    Mientras NO verifiques un dominio propio en Resend, solo podrás enviar
    correos a la dirección de email con la que te registraste en Resend
    (es una restricción de "modo sandbox" para evitar spam). Para poder
    enviarle facturas a CUALQUIER cliente real, necesitas verificar un
    dominio propio en Resend (Domains -> Add Domain) y usar ese dominio
    en EMAIL_FROM. Si el restaurante no tiene dominio propio, se puede
    comprar uno barato (ej. en Namecheap) solo para este propósito.
"""

import os
import base64
import requests

RESEND_API_URL = "https://api.resend.com/emails"


def enviar_factura_por_correo(factura, pdf_path):
    """
    Envía la factura (PDF adjunto) al correo del cliente vía Resend.
    Retorna (ok: bool, mensaje: str)
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False, (
            "Falta configurar RESEND_API_KEY. Crea una cuenta gratis en "
            "resend.com, genera una API key, y agrégala como variable de "
            "entorno antes de enviar."
        )

    remitente = os.environ.get("EMAIL_FROM", "Restaurante <onboarding@resend.dev>")

    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    except FileNotFoundError:
        return False, "No se pudo generar el PDF de la factura para adjuntarlo."
    except Exception as e:
        return False, f"Error al leer el PDF generado: {e}"

    cuerpo = (
        f"Hola {factura.cliente.nombre},\n\n"
        f"Adjuntamos tu factura #{factura.id} por un total de ${factura.total}.\n"
    )
    if factura.estado in ("fiado", "abonada"):
        cuerpo += f"Saldo pendiente: ${factura.saldo}\n"
    cuerpo += "\n¡Gracias por tu preferencia!"

    payload = {
        "from": remitente,
        "to": [factura.cliente.email],
        "subject": f"Factura #{factura.id} - Restaurante",
        "text": cuerpo,
        "attachments": [
            {
                "filename": f"factura_{factura.id}.pdf",
                "content": base64.b64encode(pdf_bytes).decode("utf-8"),
            }
        ],
    }

    try:
        # timeout=10: falla rápido con un mensaje claro en vez de colgar la
        # petición hasta que el servidor mate el proceso.
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
    except requests.exceptions.Timeout:
        return False, "Resend tardó demasiado en responder. Intenta de nuevo."
    except requests.exceptions.RequestException as e:
        return False, f"Error al conectar con Resend: {e}"

    if response.status_code in (200, 201):
        return True, f"Factura enviada por correo a {factura.cliente.email}."

    # Resend devuelve el motivo del rechazo en JSON, ej. dominio no verificado
    try:
        detalle = response.json().get("message", response.text)
    except ValueError:
        detalle = response.text
    return False, f"Resend rechazó el envío ({response.status_code}): {detalle}"
