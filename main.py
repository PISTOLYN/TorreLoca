"""TORRE LOCA - punto de entrada.

    python main.py                     -> inicia el juego
    python main.py --probar-controles  -> muestra el código de cada tecla/pulsador detectado
"""
import os
import sys
import traceback


def _dpi_windows():
    """Evita que Windows escale (y emborrone) la ventana en pantallas de alta densidad."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    _dpi_windows()
    if "--probar-controles" in sys.argv:
        from torreloca.jugadores import probar_controles
        probar_controles()
        return 0
    try:
        from torreloca.juego import Juego
        Juego().ejecutar()
        return 0
    except Exception:
        # Registro de errores para el operador (%APPDATA%\TorreLoca\error.log)
        try:
            from torreloca import rutas
            with open(os.path.join(rutas.carpeta_datos(), "error.log"), "a", encoding="utf-8") as f:
                f.write(traceback.format_exc() + "\n")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    sys.exit(main())
