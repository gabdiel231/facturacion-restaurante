from pathlib import Path
import shutil
import os

# 1. Salir primero de la carpeta conflictiva y posicionarse en C:/Proyectos
base_parent = Path("C:/Proyectos")
base_parent.mkdir(parents=True, exist_ok=True)
os.chdir(base_parent)

base_dir = base_parent / "facturacion_restaurante"

# 2. Intentar borrar la carpeta de manera segura (manejando bloqueos si los hubiera)
if base_dir.exists():
    try:
        shutil.rmtree(base_dir)
    except PermissionError:
        print("Aviso: No se pudo borrar completamente la carpeta porque está abierta en otra ventana o proceso.")

# 3. Volver a crear las subcarpetas
subdirs = [
    "templates",
    "static/css",
    "utils",
    "instance"
]

for sub in subdirs:
    (base_dir / sub).mkdir(parents=True, exist_ok=True)

# 4. Cambiar al directorio final y listar la estructura
os.chdir(base_dir)

print(".")
for root, dirs, _ in os.walk("."):
    for d in sorted(dirs):
        print(f"./{Path(root, d).relative_to('.')}".replace("\\", "/"))