"""
Reportes de ventas usando pandas para agregación y análisis.
"""

import pandas as pd
from models import db, Factura, DetalleFactura, Comida


def _facturas_a_dataframe():
    facturas = Factura.query.all()
    data = [{
        "id": f.id,
        "fecha": f.fecha,
        "total": float(f.total),
        "estado": f.estado,
        "cliente": f.cliente.nombre,
    } for f in facturas]
    return pd.DataFrame(data)


def ventas_por_dia():
    """Retorna lista de dicts [{fecha, total}] agrupado por día."""
    df = _facturas_a_dataframe()
    if df.empty:
        return []
    df["dia"] = df["fecha"].dt.date
    resumen = df.groupby("dia")["total"].sum().reset_index()
    resumen = resumen.sort_values("dia", ascending=False)
    return [
        {"fecha": row.dia.strftime("%d/%m/%Y"), "total": round(row.total, 2)}
        for row in resumen.itertuples()
    ]


def platos_mas_vendidos(limite=10):
    """Retorna lista de dicts [{nombre, cantidad, total}] de los platos más vendidos."""
    detalles = (
        db.session.query(
            Comida.nombre,
            db.func.sum(DetalleFactura.cantidad).label("cantidad"),
            db.func.sum(DetalleFactura.subtotal).label("total"),
        )
        .join(Comida, Comida.id == DetalleFactura.comida_id)
        .group_by(Comida.id)
        .order_by(db.desc("cantidad"))
        .limit(limite)
        .all()
    )
    return [
        {"nombre": d.nombre, "cantidad": int(d.cantidad), "total": round(float(d.total), 2)}
        for d in detalles
    ]


def resumen_general():
    """Totales generales para el encabezado del reporte."""
    df = _facturas_a_dataframe()
    if df.empty:
        return {"total_vendido": 0, "num_facturas": 0, "total_fiado": 0}

    total_vendido = df["total"].sum()
    num_facturas = len(df)
    total_fiado = df[df["estado"].isin(["fiado", "abonada"])]["total"].sum()

    return {
        "total_vendido": round(total_vendido, 2),
        "num_facturas": num_facturas,
        "total_fiado": round(total_fiado, 2),
    }
