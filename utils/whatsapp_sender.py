"""
Envío de facturas por WhatsApp.

Hay dos caminos:

1) GRATIS (implementado aquí): generar un link de wa.me con el mensaje
   pre-cargado. Al hacer clic, abre WhatsApp Web/App con el chat del
   cliente y el mensaje listo para enviar (el usuario solo presiona "Enviar").
   No permite adjuntar el PDF automáticamente, pero sí el resumen de la factura.

2) AUTOMÁTICO/COMPLETO (requiere cuenta de pago): usar la API de Twilio
   para WhatsApp Business, que sí permite adjuntar el PDF y enviar sin
   intervención humana. Se deja un ejemplo comentado abajo por si luego
   quieres escalar a esa opción.
"""

from urllib.parse import quote


def generar_link_whatsapp(factura):
    telefono = "".join(ch for ch in factura.cliente.telefono if ch.isdigit())

    mensaje = (
        f"Hola {factura.cliente.nombre}, tu factura #{factura.id} es por un total "
        f"de ${factura.total}."
    )
    if factura.estado in ("fiado", "abonada"):
        mensaje += f" Saldo pendiente: ${factura.saldo}."
    mensaje += " ¡Gracias por tu preferencia!"

    return f"https://wa.me/{telefono}?text={quote(mensaje)}"


# ---------------------------------------------------------------------------
# Ejemplo de envío 100% automático con Twilio (requiere cuenta y costo por mensaje)
# ---------------------------------------------------------------------------
# from twilio.rest import Client
#
# def enviar_whatsapp_automatico(factura, pdf_url):
#     client = Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])
#     client.messages.create(
#         from_="whatsapp:+14155238886",  # número sandbox o tu número de WhatsApp Business
#         to=f"whatsapp:+{factura.cliente.telefono}",
#         body=f"Tu factura #{factura.id} por ${factura.total}",
#         media_url=[pdf_url],  # el PDF debe estar accesible por una URL pública
#     )