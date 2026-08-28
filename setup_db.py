from sqlalchemy import create_engine
from sqlalchemy.sql import text

# 1. Conexión inicial al servidor PostgreSQL (usando la base de datos por defecto 'postgres')
# Reemplaza 'tu_password_postgres' con la contraseña que asignaste durante la instalación en Windows.
admin_engine = create_engine("postgresql://postgres:tu_password_postgres@localhost:5432/postgres")

# 2. Creación de la base de datos y el usuario (ejecutado con aislamiento de transacción)
try:
    with admin_engine.connect() as connection:
        # Importante: Para crear bases de datos en SQL, se debe desactivar el modo transacción (autocommit)
        connection = connection.execution_options(isolation_level="AUTOCOMMIT")
        
        # Crear usuario si no existe (opcionalmente puedes manejarlo directo)
        print("Verificando / Creando usuario y base de datos...")
        connection.execute(text("CREATE USER facturacion_user WITH PASSWORD 'facturacion_pass';"))
        connection.execute(text("CREATE DATABASE facturacion_db OWNER facturacion_user;"))
        connection.execute(text("GRANT ALL PRIVILEGES ON DATABASE facturacion_db TO facturacion_user;"))
        print("¡Base de datos y usuario configurados exitosamente!")
except Exception as e:
    print("Nota: Es posible que el usuario o la base de datos ya existan:", e)