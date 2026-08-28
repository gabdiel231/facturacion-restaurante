"""
Autenticación simple basada en sesión (sin base de datos de usuarios).

Pensado para un solo negocio con un usuario administrador (el dueño/cajero).
Las credenciales se definen por variables de entorno para no dejarlas
escritas en el código:

    export ADMIN_USER=admin
    export ADMIN_PASSWORD=una_clave_segura

Si no defines las variables, se usan valores por defecto SOLO para
desarrollo (admin / admin123) — cámbialos antes de usar en producción.
"""

import os
from functools import wraps
from flask import session, redirect, url_for, request, flash

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


def verificar_credenciales(usuario, password):
    return usuario == ADMIN_USER and password == ADMIN_PASSWORD


def login_requerido(f):
    """Decorador para proteger rutas: redirige a /login si no hay sesión activa."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("logueado"):
            flash("Debes iniciar sesión para continuar.", "danger")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorada