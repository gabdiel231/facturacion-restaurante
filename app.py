"""
Sistema de Facturación para Restaurante
----------------------------------------
App Flask con:
  - Gestión de clientes (mini CRM)
  - Gestión del menú (comidas y precios)
  - Generación de facturas con detalle
  - Control de comidas fiadas (crédito) y abonos
  - Envío de factura por correo y WhatsApp
"""

import os
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash

from models import db, Cliente, Comida, Factura, DetalleFactura, Abono
from utils.email_sender import enviar_factura_por_correo
from utils.whatsapp_sender import generar_link_whatsapp
from utils.factura_pdf import generar_pdf_factura
from utils.auth import verificar_credenciales, login_requerido
from utils import reportes

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__)

# En producción (Render, Railway, etc.) el hosting inyecta la variable de
# entorno DATABASE_URL apuntando a PostgreSQL. Si no existe (desarrollo
# local), se usa SQLite como respaldo automático.
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Render/Heroku entregan la URL con el prefijo antiguo "postgres://",
    # pero SQLAlchemy 1.4+ exige "postgresql://". Se corrige aquí.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(INSTANCE_DIR, 'facturacion.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambia-esta-clave-en-produccion")

db.init_app(app)


from flask import session


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        password = request.form.get("password", "")
        if verificar_credenciales(usuario, password):
            session["logueado"] = True
            flash("Bienvenido de nuevo.", "success")
            destino = request.args.get("next") or url_for("index")
            return redirect(destino)
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logueado", None)
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Inicio
# ---------------------------------------------------------------------------
@app.route("/")
@login_requerido
def index():
    clientes_con_deuda = [c for c in Cliente.query.all() if c.saldo_pendiente > 0]
    ultimas_facturas = Factura.query.order_by(Factura.fecha.desc()).limit(10).all()
    return render_template(
        "index.html",
        clientes_con_deuda=clientes_con_deuda,
        ultimas_facturas=ultimas_facturas,
    )


# ---------------------------------------------------------------------------
# CRM: Clientes
# ---------------------------------------------------------------------------
@app.route("/clientes")
@login_requerido
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo_cliente():
    if request.method == "POST":
        cliente = Cliente(
            nombre=request.form["nombre"],
            telefono=request.form.get("telefono"),
            email=request.form.get("email"),
            direccion=request.form.get("direccion"),
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f"Cliente '{cliente.nombre}' creado correctamente.", "success")
        return redirect(url_for("listar_clientes"))
    return render_template("cliente_form.html")


@app.route("/clientes/<int:cliente_id>")
@login_requerido
def ver_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("cliente_detalle.html", cliente=cliente)


@app.route("/clientes/<int:cliente_id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    if cliente.facturas:
        flash(
            f"No se puede eliminar a '{cliente.nombre}' porque ya tiene facturas "
            "registradas (eso protege tu historial de ventas).",
            "danger",
        )
        return redirect(url_for("ver_cliente", cliente_id=cliente.id))

    nombre = cliente.nombre
    db.session.delete(cliente)
    db.session.commit()
    flash(f"Cliente '{nombre}' eliminado.", "success")
    return redirect(url_for("listar_clientes"))


# ---------------------------------------------------------------------------
# Menú: Comidas y precios
# ---------------------------------------------------------------------------
@app.route("/menu")
@login_requerido
def listar_menu():
    comidas = Comida.query.order_by(Comida.categoria, Comida.nombre).all()
    return render_template("menu.html", comidas=comidas)


@app.route("/menu/nuevo", methods=["GET", "POST"])
@login_requerido
def nueva_comida():
    if request.method == "POST":
        comida = Comida(
            nombre=request.form["nombre"],
            descripcion=request.form.get("descripcion"),
            categoria=request.form.get("categoria"),
            precio_actual=Decimal(request.form["precio_actual"]),
            disponible=bool(request.form.get("disponible")),
        )
        db.session.add(comida)
        db.session.commit()
        flash(f"'{comida.nombre}' agregado al menú.", "success")
        return redirect(url_for("listar_menu"))
    return render_template("comida_form.html")


@app.route("/menu/<int:comida_id>/editar", methods=["GET", "POST"])
@login_requerido
def editar_comida(comida_id):
    comida = Comida.query.get_or_404(comida_id)
    if request.method == "POST":
        comida.nombre = request.form["nombre"]
        comida.descripcion = request.form.get("descripcion")
        comida.categoria = request.form.get("categoria")
        comida.precio_actual = Decimal(request.form["precio_actual"])
        comida.disponible = bool(request.form.get("disponible"))
        db.session.commit()
        flash("Precio/comida actualizado.", "success")
        return redirect(url_for("listar_menu"))
    return render_template("comida_form.html", comida=comida)


@app.route("/menu/<int:comida_id>/eliminar", methods=["POST"])
@login_requerido
def eliminar_comida(comida_id):
    comida = Comida.query.get_or_404(comida_id)
    ya_vendido = DetalleFactura.query.filter_by(comida_id=comida.id).first()

    if ya_vendido:
        # No se borra para no romper el historial de facturas antiguas;
        # simplemente se oculta del menú activo.
        comida.disponible = False
        db.session.commit()
        flash(
            f"'{comida.nombre}' ya aparece en facturas anteriores, así que no se "
            "puede eliminar por completo (protege tu historial). Se marcó como "
            "'no disponible' para que ya no aparezca en nuevas ventas.",
            "success",
        )
        return redirect(url_for("listar_menu"))

    nombre = comida.nombre
    db.session.delete(comida)
    db.session.commit()
    flash(f"'{nombre}' eliminado del menú.", "success")
    return redirect(url_for("listar_menu"))


# ---------------------------------------------------------------------------
# Facturación: crear venta
# ---------------------------------------------------------------------------
@app.route("/facturas/nueva", methods=["GET", "POST"])
@login_requerido
def nueva_factura():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    comidas = Comida.query.filter_by(disponible=True).order_by(Comida.nombre).all()

    if request.method == "POST":
        cliente_id = int(request.form["cliente_id"])
        es_fiado = request.form.get("es_fiado") == "on"
        metodo_pago = request.form.get("metodo_pago", "efectivo")

        comida_ids = request.form.getlist("comida_id")
        cantidades = request.form.getlist("cantidad")

        if not comida_ids:
            flash("Debes agregar al menos una comida a la factura.", "danger")
            return redirect(url_for("nueva_factura"))

        factura = Factura(
            cliente_id=cliente_id,
            estado="fiado" if es_fiado else "pagada",
            metodo_pago=metodo_pago,
        )
        db.session.add(factura)
        db.session.flush()  # para obtener factura.id antes del commit

        total = Decimal("0")
        for cid, cant in zip(comida_ids, cantidades):
            comida = Comida.query.get(int(cid))
            cantidad = int(cant)
            if cantidad <= 0:
                continue
            subtotal = comida.precio_actual * cantidad
            detalle = DetalleFactura(
                factura_id=factura.id,
                comida_id=comida.id,
                cantidad=cantidad,
                precio_unitario=comida.precio_actual,
                subtotal=subtotal,
            )
            db.session.add(detalle)
            total += subtotal

        factura.total = total
        db.session.commit()

        flash(f"Factura #{factura.id} generada por ${total}.", "success")
        return redirect(url_for("ver_factura", factura_id=factura.id))

    return render_template("factura_form.html", clientes=clientes, comidas=comidas)


@app.route("/facturas/<int:factura_id>")
@login_requerido
def ver_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    return render_template("factura_detalle.html", factura=factura)


# ---------------------------------------------------------------------------
# Control de fiado: registrar abonos
# ---------------------------------------------------------------------------
@app.route("/facturas/<int:factura_id>/abonar", methods=["POST"])
@login_requerido
def abonar_factura(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    monto = Decimal(request.form["monto"])

    if monto <= 0:
        flash("El monto del abono debe ser mayor a cero.", "danger")
        return redirect(url_for("ver_factura", factura_id=factura_id))

    if monto > Decimal(str(factura.saldo)):
        flash("El abono no puede ser mayor al saldo pendiente.", "danger")
        return redirect(url_for("ver_factura", factura_id=factura_id))

    abono = Abono(
        factura_id=factura.id,
        monto=monto,
        metodo_pago=request.form.get("metodo_pago", "efectivo"),
    )
    db.session.add(abono)
    db.session.flush()  # asegura que el abono ya exista en BD al recalcular el estado
    factura.actualizar_estado()
    db.session.commit()

    flash(f"Abono de ${monto} registrado. Saldo restante: ${factura.saldo}", "success")
    return redirect(url_for("ver_factura", factura_id=factura_id))


@app.route("/fiados")
@login_requerido
def listar_fiados():
    """Panel de control de comidas fiadas: quién debe y cuánto."""
    facturas_pendientes = (
        Factura.query.filter(Factura.estado.in_(["fiado", "abonada"]))
        .order_by(Factura.fecha.desc())
        .all()
    )
    return render_template("fiados.html", facturas=facturas_pendientes)


# ---------------------------------------------------------------------------
# Envío de factura por correo / WhatsApp
# ---------------------------------------------------------------------------
@app.route("/facturas/<int:factura_id>/enviar-correo", methods=["POST"])
@login_requerido
def enviar_correo(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    if not factura.cliente.email:
        flash("Este cliente no tiene correo registrado.", "danger")
        return redirect(url_for("ver_factura", factura_id=factura_id))

    pdf_path = generar_pdf_factura(factura)
    ok, mensaje = enviar_factura_por_correo(factura, pdf_path)
    flash(mensaje, "success" if ok else "danger")
    return redirect(url_for("ver_factura", factura_id=factura_id))


@app.route("/facturas/<int:factura_id>/enviar-whatsapp")
@login_requerido
def enviar_whatsapp(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    if not factura.cliente.telefono:
        flash("Este cliente no tiene teléfono registrado.", "danger")
        return redirect(url_for("ver_factura", factura_id=factura_id))

    link = generar_link_whatsapp(factura)
    return redirect(link)


# ---------------------------------------------------------------------------
# Reportes de ventas
# ---------------------------------------------------------------------------
@app.route("/reportes")
@login_requerido
def ver_reportes():
    return render_template(
        "reportes.html",
        resumen=reportes.resumen_general(),
        ventas_dia=reportes.ventas_por_dia(),
        platos=reportes.platos_mas_vendidos(),
    )


# Crea las tablas si no existen. Se ejecuta siempre al importar este módulo
# (no solo con `python app.py`), para que funcione también bajo gunicorn en
# producción, donde este bloque "if __name__" nunca se ejecuta.
with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
