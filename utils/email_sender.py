"""
Envío de facturas por correo electrónico usando SMTP.

Configura tus credenciales como variables de entorno (NUNCA las escribas
directamente en el código):

    export EMAIL_HOST=smtp.gmail.com
    export EMAIL_PORT=587
    export EMAIL_USER=tu_correo@gmail.com
    export EMAIL_PASSWORD=tu_contraseña_de_aplicacion

Nota: si usas Gmail, necesitas generar una "contraseña de aplicación"
(no tu contraseña normal) desde la configuración de seguridad de tu cuenta.
"""

import os
import smtplib
from email.message import EmailMessage


def enviar_factura_por_correo(factura, pdf_path):
    """
    Envía la factura (PDF adjunto) al correo del cliente.
    Retorna (ok: bool, mensaje: str)
    """
    host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_PORT", 587))
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")

    if not user or not password:
        return False, (
            "Faltan las credenciales de correo. Configura las variables de entorno "
            "EMAIL_USER y EMAIL_PASSWORD antes de enviar."
        )

    msg = EmailMessage()
    msg["Subject"] = f"Factura #{factura.id} - Restaurante"
    msg["From"] = user
    msg["To"] = factura.cliente.email

    cuerpo = (
        f"Hola {factura.cliente.nombre},\n\n"
        f"Adjuntamos tu factura #{factura.id} por un total de ${factura.total}.\n"
    )
    if factura.estado in ("fiado", "abonada"):
        cuerpo += f"Saldo pendiente: ${factura.saldo}\n"
    cuerpo += "\n¡Gracias por tu preferencia!"

    msg.set_content(cuerpo)

    try:
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=f"factura_{factura.id}.pdf",
            )

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True, f"Factura enviada por correo a {factura.cliente.email}."
    except FileNotFoundError:
        return False, "No se pudo generar el PDF de la factura para adjuntarlo."
    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail rechazó las credenciales. Verifica que EMAIL_PASSWORD sea una "
            "'contraseña de aplicación' (no tu contraseña normal de Gmail)."
        )
    except Exception as e:
        return False, f"Error al enviar el correo: {e}"
