"""
Modelos de datos del sistema de facturación de restaurante.

Tablas:
    Cliente         -> Datos del cliente
    Comida          -> Menú / platos disponibles con su precio
    Factura         -> Encabezado de cada venta (una por transacción)
    DetalleFactura  -> Líneas de la factura (qué comidas y cuántas)
    Abono           -> Pagos parciales para facturas "fiadas" (control de crédito)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(20))          # para enviar por WhatsApp
    email = db.Column(db.String(120))            # para enviar por correo
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    facturas = db.relationship("Factura", backref="cliente", lazy=True)

    @property
    def saldo_pendiente(self):
        """Suma de todo lo que el cliente debe (facturas fiadas - abonos)."""
        total = 0
        for f in self.facturas:
            if f.estado in ("fiado", "abonada"):
                total += f.saldo
        return total

    def __repr__(self):
        return f"<Cliente {self.nombre}>"


class Comida(db.Model):
    __tablename__ = "comidas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(250))
    categoria = db.Column(db.String(50))          # ej: plato_fuerte, bebida, postre
    precio_actual = db.Column(db.Numeric(10, 2), nullable=False)
    disponible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Comida {self.nombre} (${self.precio_actual})>"


class Factura(db.Model):
    __tablename__ = "facturas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # pagada  -> se pagó completa al momento
    # fiado   -> no se ha abonado nada
    # abonada -> se han hecho pagos parciales pero aún debe
    estado = db.Column(db.String(20), nullable=False, default="pagada")
    metodo_pago = db.Column(db.String(30))         # efectivo, tarjeta, transferencia...

    detalles = db.relationship(
        "DetalleFactura", backref="factura", lazy=True, cascade="all, delete-orphan"
    )
    abonos = db.relationship(
        "Abono", backref="factura", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def total_abonado(self):
        # Se consulta directo a la BD (en vez de usar self.abonos) para evitar
        # datos obsoletos si se llama justo después de agregar un abono nuevo.
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Abono.monto), 0))
            .filter(Abono.factura_id == self.id)
            .scalar()
        )
        return float(total)

    @property
    def saldo(self):
        """Lo que falta por pagar de esta factura."""
        if self.estado == "pagada":
            return 0
        return float(self.total) - float(self.total_abonado)

    def actualizar_estado(self):
        """Recalcula el estado según lo abonado. Llamar tras registrar un abono."""
        if self.estado == "pagada":
            return
        if self.total_abonado >= self.total:
            self.estado = "pagada"
        elif self.total_abonado > 0:
            self.estado = "abonada"
        else:
            self.estado = "fiado"

    def __repr__(self):
        return f"<Factura #{self.id} - {self.estado} - ${self.total}>"


class DetalleFactura(db.Model):
    __tablename__ = "detalle_facturas"

    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey("facturas.id"), nullable=False)
    comida_id = db.Column(db.Integer, db.ForeignKey("comidas.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # precio al momento de vender
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    comida = db.relationship("Comida")

    def __repr__(self):
        return f"<Detalle {self.comida.nombre} x{self.cantidad}>"


class Abono(db.Model):
    """Pago parcial hecho a una factura fiada. Es lo que permite llevar
    el control real de las 'comidas fiadas' hasta que el cliente salda su cuenta."""

    __tablename__ = "abonos"

    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey("facturas.id"), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(30))

    def __repr__(self):
        return f"<Abono ${self.monto} a Factura #{self.factura_id}>"
