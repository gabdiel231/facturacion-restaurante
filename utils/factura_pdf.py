"""
Generación del PDF de una factura, listo para adjuntar en el correo
o guardar como comprobante.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "facturas_pdf")


def generar_pdf_factura(factura):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ruta = os.path.join(OUTPUT_DIR, f"factura_{factura.id}.pdf")

    doc = SimpleDocTemplate(ruta, pagesize=letter, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "Titulo", parent=styles["Title"], fontSize=18, spaceAfter=6
    )

    story = []

    story.append(Paragraph("Restaurante - Factura", titulo_style))
    story.append(Paragraph(f"Factura N° {factura.id}", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # Datos del cliente y la factura
    info = (
        f"<b>Cliente:</b> {factura.cliente.nombre}<br/>"
        f"<b>Teléfono:</b> {factura.cliente.telefono or '-'}<br/>"
        f"<b>Fecha:</b> {factura.fecha.strftime('%d/%m/%Y %H:%M')}<br/>"
        f"<b>Estado:</b> {factura.estado.capitalize()}<br/>"
        f"<b>Método de pago:</b> {factura.metodo_pago or '-'}"
    )
    story.append(Paragraph(info, styles["Normal"]))
    story.append(Spacer(1, 16))

    # Tabla de detalle
    data = [["Comida", "Cantidad", "Precio unit.", "Subtotal"]]
    for d in factura.detalles:
        data.append([
            d.comida.nombre,
            str(d.cantidad),
            f"${d.precio_unitario}",
            f"${d.subtotal}",
        ])
    data.append(["", "", "Total", f"${factura.total}"])

    tabla = Table(data, colWidths=[7 * cm, 3 * cm, 3.5 * cm, 3.5 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
    ]))
    story.append(tabla)

    # Si la factura está fiada o abonada, mostrar saldo
    if factura.estado in ("fiado", "abonada"):
        story.append(Spacer(1, 16))
        story.append(Paragraph(
            f"<b>Total abonado:</b> ${factura.total_abonado}<br/>"
            f"<b>Saldo pendiente:</b> ${factura.saldo}",
            styles["Normal"],
        ))

    story.append(Spacer(1, 20))
    story.append(Paragraph("¡Gracias por su compra!", styles["Italic"]))

    doc.build(story)
    return ruta
