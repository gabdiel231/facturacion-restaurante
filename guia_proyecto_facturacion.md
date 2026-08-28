# Guía del Proyecto: Sistema de Facturación para Restaurante

Este documento explica **cómo están conectados los archivos entre sí** y
**en qué orden se construyó (y se debe entender) el proyecto**, para que
sepas por dónde empezar si quieres modificarlo o recrearlo desde cero.

---

## 1. Mapa de dependencias

Antes del paso a paso, esto es lo importante: **quién depende de quién**.

```
requirements.txt        (no depende de nada — se instala primero)
        |
        v
   models.py             <-- LA BASE DE TODO. No importa nada del
        |                    proyecto, solo define las tablas.
        |
        +--------------------------+--------------------------+
        v                          v                          v
utils/auth.py          utils/factura_pdf.py         utils/reportes.py
(no usa models)         utils/email_sender.py         (usa models)
                         utils/whatsapp_sender.py
                         (reciben un objeto "factura"
                          ya armado, no importan models
                          directamente excepto reportes.py)
        |                          |                          |
        +--------------------------+--------------------------+
                              v
                          app.py          <-- EL CENTRO. Importa
                                               models.py y TODOS los
                                               archivos de utils/.
                              |
                +-------------+--------------+
                v                            v
        templates/*.html              static/css/style.css
   (Flask las busca automático,       (las plantillas la
    dependen de las variables          referencian con
    que app.py les pasa)               url_for('static', ...))
                              |
                              v
                        seed_data.py    <-- Se ejecuta AL FINAL, una
                                             sola vez. Importa app.py
                                             y models.py para crear
                                             las tablas y meter datos
                                             de ejemplo.
```

**Regla clave:** `models.py` no depende de nada del proyecto — por eso
siempre se construye primero. `app.py` depende de todo lo demás — por eso
es el último en poder funcionar, y el primero que se rompe si falta algo.

---

## 2. Orden para entender el proyecto (léelo en este orden)

Si quieres leer el código para entenderlo de arriba a abajo, este es el
orden correcto — no el orden alfabético de las carpetas:

### Paso 1 — `requirements.txt`
Qué librerías se necesitan: Flask (el framework web), Flask-SQLAlchemy (el
ORM para hablar con SQL sin escribir SQL a mano), reportlab (generar PDF),
pandas (los reportes).

### Paso 2 — `models.py`
**El corazón del sistema.** Aquí se definen las 5 tablas y sus relaciones:
`Cliente`, `Comida`, `Factura`, `DetalleFactura`, `Abono`. Todo lo demás en
el proyecto existe para leer o escribir en estas tablas. Si no entiendes
esta tabla, nada más va a tener sentido.

### Paso 3 — `utils/` (los ayudantes, uno por uno)
Cada archivo aquí hace **una sola cosa** y se apoya en lo que ya definió
`models.py`:
- `auth.py` — decide si dejas pasar o no a alguien sin sesión iniciada.
- `factura_pdf.py` — recibe una `Factura` y genera su PDF.
- `email_sender.py` — recibe una `Factura` y su PDF, y los manda por correo.
- `whatsapp_sender.py` — recibe una `Factura` y arma el link de WhatsApp.
- `reportes.py` — consulta las tablas y arma los resúmenes de ventas.

### Paso 4 — `app.py`
Aquí se conecta todo: cada **ruta** (`/clientes`, `/facturas/nueva`, etc.)
recibe una petición del navegador, usa `models.py` para leer/escribir datos,
usa los archivos de `utils/` cuando hace falta (mandar correo, generar PDF),
y al final le entrega los datos a una plantilla HTML para mostrarlos.

### Paso 5 — `templates/*.html`
Las vistas. Cada una recibe datos desde una función de `app.py` (por
ejemplo, `index.html` recibe `clientes_con_deuda` y `ultimas_facturas`) y
solo se encarga de mostrarlos. No tienen lógica de negocio, solo lógica de
presentación (bucles `for`, condicionales `if` para pintar la pantalla).

### Paso 6 — `static/css/style.css`
El diseño visual. Ningún archivo depende de este, pero todas las plantillas
lo referencian.

### Paso 7 — `seed_data.py`
El último eslabón. Se corre una sola vez para llenar la base de datos con
clientes y platos de ejemplo, para poder probar el sistema sin capturar
todo a mano.

---

## 3. Orden para *ejecutar* el proyecto (comandos)

Este es el orden real de comandos, de cero a tener el sistema corriendo:

```bash
# 1. Entrar a la carpeta del proyecto
cd facturacion_restaurante

# 2. Instalar las librerías (usa lo que dice requirements.txt)
pip install -r requirements.txt

# 3. Crear la base de datos y meter datos de ejemplo
#    (esto ejecuta models.py "por dentro" para crear las tablas)
python seed_data.py

# 4. Arrancar el servidor (esto activa app.py, que ya tiene
#    todo lo anterior disponible para usar)
python app.py

# 5. Abrir el navegador en:
http://127.0.0.1:5000
```

Si en algún momento quieres empezar de cero (borrar todo lo capturado):

```bash
rm instance/facturacion.db
python seed_data.py
```

---

## 4. Si quieres modificar algo, ¿por dónde empiezo?

| Quiero...                                  | Empiezo a editar aquí                     |
|---------------------------------------------|--------------------------------------------|
| Agregar un campo nuevo (ej: "mesa" en la factura) | `models.py` primero, luego `app.py`, luego el `.html` correspondiente |
| Cambiar cómo se ve una pantalla              | Solo el archivo en `templates/`             |
| Cambiar colores/estilos                      | Solo `static/css/style.css`                 |
| Agregar una pantalla nueva (ej: editar cliente) | `app.py` (nueva ruta) + un `.html` nuevo en `templates/` |
| Cambiar cómo se calcula el fiado/abonos      | `models.py` (los métodos de `Factura`)      |
| Cambiar el correo o el mensaje de WhatsApp   | `utils/email_sender.py` o `utils/whatsapp_sender.py` |

**Regla práctica:** si el cambio tiene que ver con *qué datos existen*,
empieza en `models.py`. Si tiene que ver con *qué se ve en pantalla*,
empieza en `templates/`. Si tiene que ver con *qué pasa cuando alguien
hace clic en un botón*, empieza en `app.py`.
