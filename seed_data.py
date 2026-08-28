"""
Script para poblar la base de datos con datos de ejemplo.
Ejecutar una sola vez: python seed_data.py
"""

from app import app
from models import db, Cliente, Comida

with app.app_context():
    db.create_all()

    if Cliente.query.count() == 0:
        clientes = [
            Cliente(nombre="Juan Pérez", telefono="50761234567", email="juan@example.com"),
            Cliente(nombre="María Gómez", telefono="50769876543", email="maria@example.com"),
        ]
        db.session.add_all(clientes)

    if Comida.query.count() == 0:
        comidas = [
            Comida(nombre="Arroz con pollo", categoria="plato_fuerte", precio_actual=6.50),
            Comida(nombre="Sancocho", categoria="plato_fuerte", precio_actual=7.00),
            Comida(nombre="Ensalada César", categoria="entrada", precio_actual=4.50),
            Comida(nombre="Jugo natural", categoria="bebida", precio_actual=1.50),
            Comida(nombre="Gaseosa", categoria="bebida", precio_actual=1.00),
            Comida(nombre="Flan de caramelo", categoria="postre", precio_actual=2.50),
        ]
        db.session.add_all(comidas)

    db.session.commit()
    print("Datos de ejemplo creados correctamente ✅")
