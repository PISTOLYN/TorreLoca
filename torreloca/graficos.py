"""Utilidades gráficas: colores, textos con contorno, fondo neón, luces, logo y bloques."""
import math
import os

import pygame

from . import rutas

LW, LH = 1280, 720                      # resolución lógica (se escala a cualquier ventana)

AZUL = (40, 150, 255)
ROJO = (255, 60, 70)
BLANCO = (255, 255, 255)
AMARILLO = (255, 214, 0)
NEGRO = (8, 8, 14)
GRIS = (170, 175, 195)


def mezcla(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# ------------------------------------------------------------------ textos
_fuentes = {}
_cache_texto = {}
_ANCLAS = {"centro": "center", "izq": "midleft", "der": "midright",
           "arriba": "midtop", "abajo": "midbottom"}


def fuente(tam):
    """Impact/Arial Black si existen en el sistema; si no, la fuente incluida en pygame."""
    if tam not in _fuentes:
        ruta = None
        for nombre in ("impact", "arialblack", "arial"):
            ruta = pygame.font.match_font(nombre)
            if ruta:
                break
        _fuentes[tam] = pygame.font.Font(ruta, tam)
    return _fuentes[tam]


def texto(destino, txt, tam, color=BLANCO, pos=(0, 0), ancla="centro",
          contorno=None, grosor=2, alfa=255):
    clave = (txt, tam, color, contorno, grosor)
    superficie = _cache_texto.get(clave)
    if superficie is None:
        if len(_cache_texto) > 400:
            _cache_texto.clear()
        f = fuente(tam)
        base = f.render(txt, True, color)
        if contorno:
            sombra = f.render(txt, True, contorno)
            w, h = base.get_size()
            capa = pygame.Surface((w + 2 * grosor, h + 2 * grosor), pygame.SRCALPHA)
            for dx in range(-grosor, grosor + 1):
                for dy in range(-grosor, grosor + 1):
                    if dx or dy:
                        capa.blit(sombra, (dx + grosor, dy + grosor))
            capa.blit(base, (grosor, grosor))
            base = capa
        superficie = base
        _cache_texto[clave] = superficie
    rect = superficie.get_rect()
    setattr(rect, _ANCLAS[ancla], pos)
    if alfa < 255:
        copia = superficie.copy()
        copia.set_alpha(alfa)
        destino.blit(copia, rect)
    else:
        destino.blit(superficie, rect)
    return rect


def envolver(txt, tam, ancho_max):
    """Divide 'txt' en líneas que caben en 'ancho_max' píxeles."""
    f = fuente(tam)
    lineas, actual = [], ""
    for palabra in txt.split():
        prueba = (actual + " " + palabra).strip()
        if f.size(prueba)[0] <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


# ------------------------------------------------------------------ fondo
_fondo = None


def _rayas(superficie, y, alto):
    superficie.fill(AMARILLO, (0, y, LW, alto))
    superficie.set_clip(pygame.Rect(0, y, LW, alto))
    for x in range(-alto, LW + alto, alto * 2):
        pygame.draw.polygon(superficie, (15, 15, 15),
                            [(x, y + alto), (x + alto, y), (x + alto * 2, y), (x + alto, y + alto)])
    superficie.set_clip(None)


def fondo():
    """Degradado azul -> rojo con franjas de peligro arriba y abajo (se crea una sola vez)."""
    global _fondo
    if _fondo is None:
        s = pygame.Surface((LW, LH))
        izq, medio, der = (3, 10, 52), (9, 8, 22), (58, 5, 14)
        for x in range(LW):
            t = x / (LW - 1)
            color = mezcla(izq, medio, t * 2) if t < 0.5 else mezcla(medio, der, (t - 0.5) * 2)
            pygame.draw.line(s, color, (x, 0), (x, LH))
        _rayas(s, 0, 18)
        _rayas(s, LH - 18, 18)
        _fondo = s
    return _fondo


def luces(destino, t, efectos=True):
    """Hilera de reflectores entre ambos tableros."""
    n = 9
    for i in range(n):
        f = i / (n - 1)
        color = mezcla((70, 170, 255), (255, 80, 90), f)
        x, y = int(530 + f * 220), 58
        pulso = 0.5 + 0.5 * math.sin(t * 4.0 - i * 0.7) if efectos else 0.7
        halo = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(halo, color + (int(60 + 90 * pulso),), (35, 35), int(20 + 9 * pulso))
        destino.blit(halo, (x - 35, y - 35))
        pygame.draw.circle(destino, mezcla(color, BLANCO, 0.6), (x, y), int(8 + 3 * pulso))


def dibujar_vs(destino):
    texto(destino, "VS", 130, (205, 30, 35), (640, 205), contorno=AMARILLO, grosor=4)


# ------------------------------------------------------------------- logo
_logo = None


def _crear_logo():
    ruta = rutas.recurso("logo.png")        # el operador puede colocar su propio logo aquí
    if os.path.isfile(ruta):
        try:
            img = pygame.image.load(ruta).convert_alpha()
            esc = min(250.0 / img.get_width(), 300.0 / img.get_height())
            return pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * esc)), max(1, int(img.get_height() * esc))))
        except pygame.error:
            pass
    s = pygame.Surface((250, 240), pygame.SRCALPHA)
    pygame.draw.circle(s, (70, 30, 140), (125, 120), 116)
    pygame.draw.circle(s, (120, 220, 60), (125, 120), 116, width=6)
    pygame.draw.circle(s, AMARILLO, (125, 120), 104, width=3)
    for (cx, cy, col) in ((40, 60, AMARILLO), (210, 70, (255, 120, 40)), (60, 190, (90, 220, 255)),
                          (200, 185, (255, 90, 160)), (125, 22, (120, 255, 120))):
        pygame.draw.circle(s, col, (cx, cy), 7)
    texto(s, "DESAFÍOS", 46, BLANCO, (125, 100), contorno=(20, 10, 40), grosor=3)
    texto(s, "LOCOS", 70, AMARILLO, (125, 158), contorno=(20, 90, 20), grosor=3)
    return s


def dibujar_logo(destino, centro):
    global _logo
    if _logo is None:
        _logo = _crear_logo()
    destino.blit(_logo, _logo.get_rect(center=centro))


# ----------------------------------------------------------------- bloques
_sprites = {}


def bloque(celda, color, brillo=1.0):
    """Cubo luminoso con punto central (estilo del tablero de referencia)."""
    clave = (celda, color, round(brillo, 1))
    s = _sprites.get(clave)
    if s is None:
        s = pygame.Surface((celda, celda), pygame.SRCALPHA)
        rad = max(2, celda // 8)
        pygame.draw.rect(s, mezcla(color, (0, 0, 0), 0.45), (0, 0, celda, celda), border_radius=rad)
        m = max(2, celda // 12)
        pygame.draw.rect(s, mezcla(color, BLANCO, 0.12 * brillo),
                         (m, m, celda - 2 * m, celda - 2 * m), border_radius=rad)
        m2 = max(4, celda // 5)
        pygame.draw.rect(s, mezcla(color, BLANCO, 0.38 * brillo),
                         (m2, m2, celda - 2 * m2, celda - 2 * m2), border_radius=max(2, rad - 1))
        pygame.draw.circle(s, BLANCO, (celda // 2, celda // 2), max(2, celda // 10))
        _sprites[clave] = s
    return s


def reiniciar_cache():
    """Descarta fuentes y superficies guardadas (necesario si pygame se reinicia, p. ej. en pruebas)."""
    global _fondo, _logo
    _fuentes.clear()
    _cache_texto.clear()
    _sprites.clear()
    _fondo = None
    _logo = None
