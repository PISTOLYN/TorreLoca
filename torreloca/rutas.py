"""Rutas de recursos y de datos del usuario (funciona en desarrollo y dentro del .exe)."""
import os
import sys


def congelado():
    return bool(getattr(sys, "frozen", False))


def base_dir():
    """Carpeta raíz del proyecto (o carpeta temporal de PyInstaller)."""
    if congelado():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def exe_dir():
    """Carpeta donde vive TorreLoca.exe (o la raíz del proyecto en desarrollo)."""
    if congelado():
        return os.path.dirname(sys.executable)
    return base_dir()


def recurso(*partes):
    """Ruta a un archivo dentro de la carpeta assets/ incluida con el juego."""
    return os.path.join(base_dir(), "assets", *partes)


def buscar_demo():
    """Busca demo.mp4 junto al .exe (editable por el operador) y luego en assets/."""
    for carpeta in (exe_dir(), os.path.join(exe_dir(), "assets"), os.path.join(base_dir(), "assets")):
        ruta = os.path.join(carpeta, "demo.mp4")
        if os.path.isfile(ruta):
            return ruta
    return None


def carpeta_datos():
    """Carpeta persistente para las preferencias (%APPDATA%\\TorreLoca en Windows)."""
    forzada = os.environ.get("TORRELOCA_DATOS")
    if forzada:
        base = forzada
    else:
        raiz = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
        base = os.path.join(raiz, "TorreLoca")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        base = exe_dir()
    return base
