"""Sonidos del juego. Se sintetizan al iniciar (no requieren archivos ni internet).

Si el operador coloca archivos WAV con estos nombres en assets/sonidos/, se usan en su lugar:
inicio, cuenta, ya, apilar, fallo, menu, reinicio, victoria
"""
import math
import os
from array import array

import pygame

from . import rutas

NOMBRES = ("inicio", "cuenta", "ya", "apilar", "fallo", "menu", "reinicio", "victoria")

# nombre -> lista de (frecuencia_inicial, frecuencia_final, duración_s, forma, volumen)
_DISENOS = {
    "inicio": [(523, 523, .10, "cuadrada", .30), (659, 659, .10, "cuadrada", .30),
               (784, 784, .10, "cuadrada", .30), (1046, 1046, .28, "seno", .45)],
    "cuenta": [(660, 660, .16, "cuadrada", .30)],
    "ya": [(880, 1320, .40, "cuadrada", .35)],
    "apilar": [(520, 780, .06, "seno", .55), (780, 1040, .07, "seno", .55)],
    "fallo": [(240, 90, .45, "sierra", .35)],
    "menu": [(900, 900, .04, "seno", .45)],
    "reinicio": [(300, 900, .28, "seno", .45)],
    "victoria": [(523, 523, .13, "cuadrada", .30), (523, 523, .13, "cuadrada", .30),
                 (523, 523, .13, "cuadrada", .30), (659, 659, .32, "cuadrada", .30),
                 (587, 587, .13, "cuadrada", .30), (659, 659, .13, "cuadrada", .30),
                 (784, 784, .70, "seno", .50), (1046, 1046, .50, "seno", .45)],
}


def _sintetizar(nombre, frecuencia, canales):
    muestras = array("h")
    for f0, f1, dur, forma, vol in _DISENOS[nombre]:
        n = max(1, int(dur * frecuencia))
        fase = 0.0
        ataque = max(1, int(0.008 * frecuencia))
        salida = max(1, int(0.03 * frecuencia))
        for i in range(n):
            f = f0 + (f1 - f0) * (i / n)
            fase += 2.0 * math.pi * f / frecuencia
            if forma == "seno":
                v = math.sin(fase)
            elif forma == "cuadrada":
                v = 0.6 if math.sin(fase) >= 0 else -0.6
            else:  # sierra
                v = ((fase / (2.0 * math.pi)) % 1.0) * 2.0 - 1.0
            env = min(1.0, i / ataque, (n - i) / salida)
            m = int(v * env * vol * 32767)
            for _ in range(canales):
                muestras.append(m)
    return muestras.tobytes()


class Audio:
    def __init__(self, cfg):
        self.volumen = cfg["volumen"]
        self.activo = cfg["sonidos"]
        self.ok = False
        self.sonidos = {}
        self.reproducidos = []        # historial (útil para las pruebas)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.ok = True
        except pygame.error:
            self.ok = False           # sin tarjeta de sonido: el juego sigue funcionando en silencio
        if self.ok:
            self._cargar()

    def _cargar(self):
        frecuencia, formato, canales = pygame.mixer.get_init()
        for nombre in NOMBRES:
            ruta = rutas.recurso("sonidos", nombre + ".wav")
            try:
                if os.path.isfile(ruta):
                    self.sonidos[nombre] = pygame.mixer.Sound(ruta)
                elif formato == -16:
                    self.sonidos[nombre] = pygame.mixer.Sound(
                        buffer=_sintetizar(nombre, frecuencia, canales))
            except (pygame.error, ValueError):
                pass

    def reproducir(self, nombre):
        """Reproduce un sonido. Devuelve True si se solicitó (aunque no haya dispositivo)."""
        if not self.activo:
            return False
        self.reproducidos.append(nombre)
        sonido = self.sonidos.get(nombre)
        if sonido is not None:
            sonido.set_volume(max(0.0, min(1.0, self.volumen)))
            sonido.play()
        return True
