# Sistema de Facturación para Restaurante

Proyecto hecho con **Python + Flask + SQLAlchemy (SQL) + HTML**, combinando
lógica de backend, base de datos relacional y un mini-CRM de clientes.

## ¿Qué hace?

- **Clientes** (mini CRM): registro de nombre, teléfono, email, dirección, y
  vista de historial de compras y saldo pendiente.
- **Menú**: comidas con su precio, categoría y disponibilidad.
- **Facturación**: generar una venta seleccionando cliente + comidas, con
  cálculo automático del total.
- **Control de fiado**: marcar una factura como fiada (crédito), registrar
  abonos parciales, y ver el saldo pendiente por factura y por cliente.
  El estado de cada factura cambia automáticamente: `fiado` → `abonada` → `pagada`.
- **Envío de factura**: por correo (PDF adjunto vía SMTP) y por WhatsApp
  (link directo con el resumen, gratis, sin necesitar API de pago).
- **Login**: todo el sistema queda protegido detrás de un inicio de sesión.
- **Reportes de ventas** (con pandas): total vendido, ventas por día, y
  ranking de platos más vendidos.

## Modelo de datos

```
Cliente 1---N Factura 1---N DetalleFactura N---1 Comida
                  |
                  1---N Abono
```

| Tabla            | Campos principales                                          |
|------------------|--------------------------------------------------------------|
| clientes         | id, nombre, telefono, email, direccion, fecha_registro       |
| comidas          | id, nombre, descripcion, categoria, precio_actual, disponible|
| facturas         | id, cliente_id, fecha, total, estado, metodo_pago             |
| detalle_facturas | id, factura_id, comida_id, cantidad, precio_unitario, subtotal|
| abonos           | id, factura_id, monto, fecha, metodo_pago                     |

## Instalación

```bash
cd facturacion_restaurante
pip install -r requirements.txt

# Crear la base de datos con datos de ejemplo (2 clientes, 6 platos)
python seed_data.py

# Arrancar el servidor
python app.py
```

Abre http://127.0.0.1:5000 en tu navegador.

## Iniciar sesión

Usuario y contraseña por defecto (**cámbialos** antes de usar en serio):

```
usuario: admin
contraseña: admin123
```

Para cambiarlos, define variables de entorno antes de correr `python app.py`:

```bash
export ADMIN_USER=tu_usuario
export ADMIN_PASSWORD=tu_clave_segura
export FLASK_SECRET_KEY=una_cadena_aleatoria_larga
```

## Desplegar en internet (para que tu cliente lo use sin depender de tu PC)

El proyecto ya está listo para producción: detecta automáticamente si hay
una `DATABASE_URL` (PostgreSQL en la nube) y si no, usa SQLite localmente.

### Paso a paso con Render.com (gratis para empezar)

1. **Sube el proyecto a GitHub.**
   ```bash
   cd facturacion_restaurante
   git init
   git add .
   git commit -m "Sistema de facturación"
   # crea un repo vacío en github.com, luego:
   git remote add origin https://github.com/tu-usuario/tu-repo.git
   git push -u origin main
   ```
   (El `.gitignore` ya excluye la base de datos local y los PDFs generados.)

2. **Crea la base de datos.** En Render: *New → PostgreSQL* → dale un
   nombre → espera a que se cree. Copia el valor de **"Internal Database
   URL"**.

3. **Crea el servicio web.** En Render: *New → Web Service* → conecta tu
   repositorio de GitHub → Render detecta automáticamente el `Procfile`.

4. **Configura las variables de entorno.** En la pestaña *Environment* del
   servicio, agrega (mira `.env.example` para la lista completa):
   - `DATABASE_URL` → pega la URL de PostgreSQL del paso 2
   - `FLASK_SECRET_KEY` → una cadena aleatoria larga
   - `ADMIN_USER` / `ADMIN_PASSWORD` → tus credenciales reales
   - `EMAIL_USER` / `EMAIL_PASSWORD` (si usarás el envío por correo)

5. **Deploy.** Render instala `requirements.txt`, corre `gunicorn app:app`
   (según el `Procfile`), y las tablas se crean solas la primera vez que
   arranca (`db.create_all()` está en `app.py`).

6. **Comparte el link.** Render te da una URL pública tipo
   `https://tu-restaurante.onrender.com` — ese es el link para tu cliente.
   Ya no depende de tu computadora ni de tu disco: vive en el servidor de
   Render, con su propia base de datos en la nube.

> Railway.app funciona casi idéntico (mismo `Procfile`, mismas variables).

## Configurar el envío de correo (opcional)

Para que el botón "Enviar por correo" funcione, define estas variables de
entorno antes de correr `python app.py`:

```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USER=tu_correo@gmail.com
export EMAIL_PASSWORD=tu_contraseña_de_aplicacion
```

Si usas Gmail, necesitas crear una "contraseña de aplicación" desde la
configuración de seguridad de tu cuenta de Google (no tu contraseña normal).

## WhatsApp

El botón "Enviar por WhatsApp" abre un link `wa.me` con el mensaje ya
redactado —el usuario solo presiona enviar. Es gratis y no requiere cuenta
de desarrollador. Si más adelante quieres automatizarlo 100% (sin clic
humano) y adjuntar el PDF, en `utils/whatsapp_sender.py` dejé un ejemplo
comentado usando la API de Twilio para WhatsApp Business (esa sí tiene costo
por mensaje).

## Estructura del proyecto

```
facturacion_restaurante/
├── app.py                  # Rutas Flask (controlador principal)
├── models.py                # Modelos SQLAlchemy (el modelo de datos)
├── seed_data.py              # Script para poblar datos de ejemplo
├── requirements.txt
├── utils/
│   ├── auth.py                # Login simple basado en sesión
│   ├── email_sender.py       # Envío de correo con PDF adjunto
│   ├── whatsapp_sender.py    # Generación de link de WhatsApp
│   ├── factura_pdf.py         # Generación del PDF de la factura
│   └── reportes.py            # Reportes de ventas con pandas
├── templates/                # Vistas HTML (Jinja2)
└── static/css/style.css       # Estilos
```

## Próximos pasos sugeridos (para seguir combinando lo que ya sabes)

- Exportar reportes a Excel (puedes usar `pandas.DataFrame.to_excel`).
- Gráficas en el reporte (matplotlib o Chart.js) para ver la tendencia de ventas.
- Múltiples usuarios con roles (cajero, administrador) usando una tabla `Usuario`.
- Migrar de SQLite a PostgreSQL cuando el negocio crezca (solo cambia una
  línea en `app.py`, gracias a que usamos SQLAlchemy como ORM).
