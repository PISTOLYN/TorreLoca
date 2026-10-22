"""Preferencias del operador: se guardan en JSON y se conservan al reabrir el juego."""
import copy
import json
import os

from . import rutas

PREDETERMINADOS = {
    "volumen": 0.7,
    "sonidos": True,
    "puntos": 100,          # puntos por apilación válida
    "filas": 16,            # altura de la torre
    "columnas": 9,          # ancho del tablero
    "velocidad": 5,         # 1 (lenta) .. 10 (rápida)
    "efectos": True,        # efectos visuales (luces, partículas)
    "pantalla_completa": False,
    # Formato de control: "key:<código pygame>" o "joy:<id>:<botón>"
    # 97 = tecla A, 108 = tecla L
    "controles": {"azul": "key:97", "rojo": "key:108"},
}

# (mínimo, máximo, paso)
RANGOS = {
    "volumen": (0.0, 1.0, 0.1),
    "puntos": (10, 1000, 10),
    "filas": (6, 20, 1),
    "columnas": (5, 12, 1),
    "velocidad": (1, 10, 1),
}


def _limitar(clave, valor):
    minimo, maximo, _ = RANGOS[clave]
    valor = max(minimo, min(maximo, valor))
    return round(valor, 2) if clave == "volumen" else int(valor)


class Configuracion:
    def __init__(self, ruta=None):
        self.ruta = ruta or os.path.join(rutas.carpeta_datos(), "configuracion.json")
        self.datos = copy.deepcopy(PREDETERMINADOS)
        self.cargar()

    # --- acceso tipo diccionario -------------------------------------------------
    def __getitem__(self, clave):
        return self.datos[clave]

    def __setitem__(self, clave, valor):
        self.datos[clave] = valor

    # --- persistencia ------------------------------------------------------------
    def cargar(self):
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                leido = json.load(f)
        except (OSError, ValueError):
            return False
        if not isinstance(leido, dict):
            return False
        for clave, defecto in PREDETERMINADOS.items():
            if clave not in leido:
                continue
            valor = leido[clave]
            if clave == "controles":
                if isinstance(valor, dict):
                    for jugador in ("azul", "rojo"):
                        texto = valor.get(jugador)
                        if isinstance(texto, str) and texto.split(":")[0] in ("key", "joy"):
                            self.datos["controles"][jugador] = texto
            elif clave in RANGOS:
                if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                    self.datos[clave] = _limitar(clave, valor)
            elif isinstance(defecto, bool):
                if isinstance(valor, bool):
                    self.datos[clave] = valor
        return True

    def guardar(self):
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False

    # --- operaciones del menú ----------------------------------------------------
    def ajustar(self, clave, delta):
        """Suma 'delta' pasos al valor numérico 'clave' respetando su rango."""
        _, _, paso = RANGOS[clave]
        self.datos[clave] = _limitar(clave, self.datos[clave] + delta * paso)
        return self.datos[clave]

    def restaurar(self):
        self.datos = copy.deepcopy(PREDETERMINADOS)
