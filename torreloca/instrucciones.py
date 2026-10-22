"""Pantalla de instrucciones y demostración (demo.mp4 local o animación integrada)."""
import random

import pygame

from . import graficos as g
from . import rutas
from .jugadores import COLORES, NOMBRES, nombre_control
from .logica import AZUL, ROJO, Partida
from .tableros import CX, VistaTablero


def dibujar_instrucciones(c, juego):
    cfg = juego.cfg
    g.texto(c, "¿CÓMO SE JUEGA?", 78, g.AMARILLO, (640, 120), contorno=g.NEGRO, grosor=4)
    g.texto(c, "Presiona tu botón, apila los bloques y llega primero a la cima",
            44, g.BLANCO, (640, 205), contorno=g.NEGRO, grosor=3)
    pasos = [
        "1.  Cada equipo tiene su propio pulsador.",
        "2.  Púlsalo justo cuando el bloque en movimiento esté sobre la fila de abajo.",
        "3.  Lo que sobresale se pierde: ¡cada vez queda menos espacio!",
        "4.  Si fallas por completo, tu torre vuelve a empezar.",
        "5.  Cada apilación válida suma %d puntos." % cfg["puntos"],
        "6.  El primero en llegar a la cima gana la partida.",
    ]
    for i, linea in enumerate(pasos):
        g.texto(c, linea, 32, g.BLANCO, (170, 275 + i * 46), ancla="izq", contorno=g.NEGRO)
    for clave, x in ((AZUL, 330), (ROJO, 950)):
        g.texto(c, NOMBRES[clave], 34, COLORES[clave], (x, 580), contorno=g.NEGRO, grosor=3)
        g.texto(c, nombre_control(cfg["controles"][clave]), 30, g.BLANCO, (x, 620),
                contorno=COLORES[clave], grosor=2)
    if int(juego.t * 2.5) % 2 == 0:
        g.texto(c, "ENTER = ¡A JUGAR!", 40, g.AMARILLO, (640, 600), contorno=g.NEGRO, grosor=3)
    g.texto(c, "D = ver demostración     M = menú del operador", 22, g.GRIS, (640, 676))


class Demostracion:
    """Video local 'demo.mp4' (si existe y hay OpenCV) o animación integrada con autopiloto."""

    PASOS = [
        "Cada equipo tiene su propio pulsador.",
        "Púlsalo cuando el bloque coincida con la fila de abajo.",
        "Lo que sobresale se pierde: cada vez hay menos espacio.",
        "¡El primero en llegar a la cima gana!",
    ]

    def __init__(self, juego):
        self.juego = juego
        self.video = None
        self.cv2 = None
        self.rng = random.Random()
        self.acum = 0.0
        self.fps = 30.0
        self.frame = None
        ruta = rutas.buscar_demo()
        if ruta:
            self._abrir_video(ruta)
        if self.video is None:
            self._reiniciar_animacion()

    # ------------------------------------------------------------------ video
    def _abrir_video(self, ruta):
        try:
            import cv2                                   # opcional: pip install opencv-python
            captura = cv2.VideoCapture(ruta)
            if captura.isOpened():
                self.cv2, self.video = cv2, captura
                self.fps = captura.get(cv2.CAP_PROP_FPS) or 30.0
        except Exception:
            self.video = None

    def _leer_video(self):
        ok, bruto = self.video.read()
        if not ok:
            self.video.set(self.cv2.CAP_PROP_POS_FRAMES, 0)
            ok, bruto = self.video.read()
        if not ok:                                       # video ilegible: usar animación integrada
            self.video = None
            self._reiniciar_animacion()
            return
        rgb = self.cv2.cvtColor(bruto, self.cv2.COLOR_BGR2RGB)
        alto, ancho = rgb.shape[:2]
        sup = pygame.image.frombuffer(rgb.tobytes(), (ancho, alto), "RGB")
        esc = min(g.LW / ancho, g.LH / alto)
        self.frame = pygame.transform.smoothscale(sup, (int(ancho * esc), int(alto * esc)))

    # -------------------------------------------------------------- animación
    def _reiniciar_animacion(self):
        self.partida = Partida(9, 10, self.juego.cfg["puntos"], 4)
        self.vistas = {j: VistaTablero(j, self.partida.torres[j], CX[j]) for j in (AZUL, ROJO)}
        self.partida.iniciar()
        self.t = 0.0
        self.fin = 0.0
        self.espera = {AZUL: 0.4, ROJO: 0.6}
        self.desvio = {AZUL: (-1, 0), ROJO: (-1, 0)}     # (fila, desviación elegida)

    def _elegir_desvio(self, jugador, torre):
        fila, _ = self.desvio[jugador]
        if fila != torre.fila_actual:
            opciones = (0, 0, 0, 1) if jugador == AZUL else (-1, 0, 0, 1)
            self.desvio[jugador] = (torre.fila_actual, self.rng.choice(opciones))
        return self.desvio[jugador][1]

    def actualizar(self, dt):
        if self.video is not None:
            self.acum += dt
            if self.acum >= 1.0 / self.fps or self.frame is None:
                self.acum = 0.0
                self._leer_video()
            return
        p = self.partida
        for v in self.vistas.values():
            v.actualizar(dt)
        if p.estado == Partida.TERMINADA:
            self.fin += dt
            if self.fin > 4.0:
                self._reiniciar_animacion()
            return
        self.t += dt
        if self.t > 60.0:
            self._reiniciar_animacion()
            return
        p.actualizar(dt)
        for j in (AZUL, ROJO):
            torre = p.torres[j]
            self.espera[j] -= dt
            if self.espera[j] > 0:
                continue
            previo = torre.capas[-1][0] if torre.capas else 1
            objetivo = max(0, min(torre.maximo, previo + self._elegir_desvio(j, torre)))
            if torre.celda_actual == objetivo:
                res = p.pulsar(j)
                self.vistas[j].efecto(res, True)
                self.espera[j] = 0.35
                if p.estado == Partida.TERMINADA:
                    self.vistas[p.ganador].modo = VistaTablero.GANADOR
                    self.vistas[p.perdedor].modo = VistaTablero.PERDEDOR
                    break

    def dibujar(self, c, t, efectos):
        if self.video is not None and self.frame is not None:
            c.fill((0, 0, 0))
            c.blit(self.frame, self.frame.get_rect(center=(g.LW // 2, g.LH // 2)))
            g.texto(c, "ENTER = salir de la demostración", 24, g.AMARILLO, (640, 690),
                    contorno=g.NEGRO)
            return
        for j in (AZUL, ROJO):
            self.vistas[j].dibujar(c, t, efectos)
            self.vistas[j].dibujar_marcador(c, t, efectos)
        g.dibujar_vs(c)
        g.texto(c, "DEMOSTRACIÓN", 36, g.AMARILLO, (640, 300), contorno=g.NEGRO, grosor=3)
        paso = self.PASOS[int(t / 2.5) % len(self.PASOS)]
        for i, linea in enumerate(g.envolver(paso, 26, 330)):
            g.texto(c, linea, 26, g.BLANCO, (640, 380 + i * 32), contorno=g.NEGRO)
        g.texto(c, "ENTER = salir", 24, g.GRIS, (640, 640))
