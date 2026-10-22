"""Vista (dibujo) de cada tablero: rejilla, bloques, marcador, X del perdedor y parpadeo del ganador."""
import math
import random

import pygame

from . import graficos as g
from .jugadores import COLORES, NOMBRES
from .logica import AZUL

CX = {"azul": 285, "rojo": 995}          # centro horizontal de cada tablero
AREA_Y0, AREA_Y1 = 118, 694               # zona vertical disponible para el marco
AREA_W = 410
PAD = 18                                  # separación marco -> rejilla
M = 24                                    # margen para el resplandor neón


class VistaTablero:
    JUEGO, GANADOR, PERDEDOR = "juego", "ganador", "perdedor"

    def __init__(self, clave, torre, centro_x):
        self.clave = clave
        self.torre = torre
        self.color = COLORES[clave]
        self.nombre = NOMBRES[clave]
        self.centro_x = centro_x
        self.modo = self.JUEGO
        self.particulas = []
        self.pop = 0.0
        self._ultimo_puntos = 0
        alto_disp = (AREA_Y1 - AREA_Y0) - 2 * PAD
        self.celda = int(max(8, min((AREA_W - 2 * PAD) / torre.columnas,
                                    alto_disp / torre.filas, 56)))
        gw, gh = self.celda * torre.columnas, self.celda * torre.filas
        mw, mh = gw + 2 * PAD, gh + 2 * PAD
        mx = centro_x - mw // 2
        my = AREA_Y0 + ((AREA_Y1 - AREA_Y0) - mh) // 2
        self.marco = pygame.Rect(mx, my, mw, mh)
        self._estatico = self._construir_estatico()

    # ------------------------------------------------------------ construcción
    def _construir_estatico(self):
        c, torre = self.celda, self.torre
        s = pygame.Surface((self.marco.w + 2 * M, self.marco.h + 2 * M), pygame.SRCALPHA)
        marco = pygame.Rect(M, M, self.marco.w, self.marco.h)
        es_azul = self.clave == AZUL
        fondo = (8, 12, 28) if es_azul else (26, 8, 12)
        celda_c = (15, 24, 48) if es_azul else (40, 15, 22)
        pygame.draw.rect(s, fondo, marco, border_radius=20)
        for f in range(torre.filas):
            for col in range(torre.columnas):
                r = pygame.Rect(M + PAD + col * c + 1, M + PAD + f * c + 1, c - 2, c - 2)
                pygame.draw.rect(s, celda_c, r, border_radius=max(2, c // 10))
                pygame.draw.line(s, g.mezcla(celda_c, g.BLANCO, 0.12),
                                 (r.left + 2, r.top + 1), (r.right - 3, r.top + 1))
        # Fila de meta (cima) resaltada
        meta = pygame.Surface((c * torre.columnas, c), pygame.SRCALPHA)
        meta.fill(self.color + (45,))
        s.blit(meta, (M + PAD, M + PAD))
        # Marco neón con resplandor
        for grosor, alfa in ((18, 28), (12, 60), (7, 110)):
            capa = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(capa, self.color + (alfa,), marco, width=grosor, border_radius=20)
            s.blit(capa, (0, 0))
        pygame.draw.rect(s, g.mezcla(self.color, g.BLANCO, 0.45), marco, width=3, border_radius=20)
        luz = g.mezcla(self.color, g.BLANCO, 0.7)
        for x in range(marco.left + 34, marco.right - 20, 36):
            pygame.draw.circle(s, luz, (x, marco.top), 4)
            pygame.draw.circle(s, luz, (x, marco.bottom - 1), 4)
        for y in range(marco.top + 34, marco.bottom - 20, 36):
            pygame.draw.circle(s, luz, (marco.left, y), 4)
            pygame.draw.circle(s, luz, (marco.right - 1, y), 4)
        return s

    def _celda_local(self, col, fila):
        return (M + PAD + col * self.celda,
                M + PAD + (self.torre.filas - 1 - fila) * self.celda)

    # ---------------------------------------------------------------- efectos
    def efecto(self, res, efectos=True):
        """Partículas al apilar (chispas), cubos que caen al recortar y derrumbe al fallar."""
        if not efectos or res is None:
            return
        if res.tipo == "fallo":
            for col in range(res.barra_ini, res.barra_ini + res.barra_ancho):
                self._cubos(col, res.fila, (150, 150, 165), 3)
            return
        for col in range(res.ini, res.ini + res.ancho):
            self._chispas(col, res.fila)
        conservadas = set(range(res.ini, res.ini + res.ancho))
        for col in range(res.barra_ini, res.barra_ini + res.barra_ancho):
            if col not in conservadas:
                self._cubos(col, res.fila, self.color, 1)

    def _centro_celda(self, col, fila):
        x, y = self._celda_local(col, fila)
        return x + self.celda / 2.0, y + self.celda / 2.0

    def _chispas(self, col, fila):
        cx, cy = self._centro_celda(col, fila)
        for _ in range(4):
            ang = random.uniform(0, 2 * math.pi)
            vel = random.uniform(40, 140)
            self.particulas.append([cx, cy, math.cos(ang) * vel, math.sin(ang) * vel - 40,
                                    0.55, g.mezcla(self.color, g.BLANCO, 0.6), 4])

    def _cubos(self, col, fila, color, cantidad):
        cx, cy = self._centro_celda(col, fila)
        for _ in range(cantidad):
            self.particulas.append([cx, cy, random.uniform(-70, 70), random.uniform(-150, -30),
                                    1.4, color, max(4, int(self.celda * 0.5))])

    def actualizar(self, dt):
        if self.torre.puntos != self._ultimo_puntos:
            self._ultimo_puntos = self.torre.puntos
            self.pop = 1.0
        self.pop = max(0.0, self.pop - dt * 3.0)
        vivas = []
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 900 * dt
            p[4] -= dt
            if p[4] > 0:
                vivas.append(p)
        self.particulas = vivas

    # ----------------------------------------------------------------- dibujo
    def alfa_parpadeo(self, t):
        """Opacidad del tablero: parpadea solo si es el ganador."""
        if self.modo == self.GANADOR:
            return 255 if int(t * 3) % 2 == 0 else 70
        return 255

    def dibujar(self, destino, t, efectos=True):
        c, torre = self.celda, self.torre
        cap = pygame.Surface(self._estatico.get_size(), pygame.SRCALPHA)
        cap.blit(self._estatico, (0, 0))
        for fila, (ini, ancho) in enumerate(torre.capas):
            for col in range(ini, ini + ancho):
                cap.blit(g.bloque(c, self.color, 1.0), self._celda_local(col, fila))
        if not torre.completa:
            pos = self._celda_local(torre.celda_actual, torre.fila_actual)
            for i in range(torre.ancho):
                cap.blit(g.bloque(c, self.color, 1.6), (pos[0] + i * c, pos[1]))
        if self.modo == self.PERDEDOR:
            self._dibujar_x(cap)
        if efectos:
            for x, y, _, _, vida, color, tam in self.particulas:
                pygame.draw.rect(cap, color + (int(255 * min(1.0, vida)),),
                                 (int(x - tam / 2), int(y - tam / 2), tam, tam))
        alfa = self.alfa_parpadeo(t)
        if alfa < 255:
            cap.set_alpha(alfa)
        destino.blit(cap, (self.marco.x - M, self.marco.y - M))

    def _dibujar_x(self, cap):
        """X fija sobre el tablero perdedor (sin parpadeo)."""
        sombra = pygame.Surface((self.marco.w, self.marco.h), pygame.SRCALPHA)
        sombra.fill((0, 0, 0, 140))
        cap.blit(sombra, (M, M))
        x0, y0 = M + PAD + 8, M + PAD + 8
        x1, y1 = M + self.marco.w - PAD - 8, M + self.marco.h - PAD - 8
        ancho = max(14, self.celda)
        for a, b in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
            pygame.draw.line(cap, (0, 0, 0, 255), a, b, ancho + 12)
        for a, b in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
            pygame.draw.line(cap, (245, 245, 245, 255), a, b, ancho)

    def dibujar_marcador(self, destino, t, efectos=True):
        rect = pygame.Rect(0, 0, 270, 80)
        rect.midtop = (self.centro_x, 22)
        fondo = (8, 14, 34) if self.clave == AZUL else (34, 8, 18)
        pygame.draw.rect(destino, fondo, rect, border_radius=16)
        pygame.draw.rect(destino, self.color, rect, width=3, border_radius=16)
        g.texto(destino, self.nombre, 20, g.mezcla(self.color, g.BLANCO, 0.5),
                (rect.centerx, rect.top + 15))
        tam = int(46 * (1.0 + 0.25 * self.pop)) if efectos else 46
        g.texto(destino, str(self.torre.puntos), tam, g.BLANCO,
                (rect.centerx, rect.top + 52), contorno=self.color, grosor=2)
