"""Menú del operador (tecla M). La partida permanece en pausa mientras está abierto."""
import pygame

from . import graficos as g
from .jugadores import (COLORES, es_reservada, evento_a_control, nombre_control)

ESTRUCTURALES = ("puntos", "filas", "columnas", "velocidad")


class Item:
    def __init__(self, etiqueta, accion=None, ajustar=None):
        self.etiqueta = etiqueta          # función sin argumentos -> texto
        self.accion = accion              # ENTER
        self.ajustar = ajustar            # flechas izquierda/derecha: función(delta)


class Menu:
    def __init__(self, juego):
        self.juego = juego
        self.cfg = juego.cfg
        self.indice = 0
        self.capturando = None            # "azul" / "rojo" mientras se espera una tecla
        self.mensaje = ""
        self.items = self._construir()

    # ---------------------------------------------------------------- opciones
    def _construir(self):
        cfg, j = self.cfg, self.juego
        si_no = lambda v: "SÍ" if v else "NO"
        return [
            Item(lambda: "CONTINUAR (SALIR DEL MENÚ)", accion=j.cerrar_menu),
            Item(lambda: "REINICIAR PARTIDA", accion=j.reiniciar_partida),
            Item(lambda: "CONTROL EQUIPO AZUL: " + nombre_control(cfg["controles"]["azul"]),
                 accion=lambda: self._capturar("azul")),
            Item(lambda: "CONTROL EQUIPO ROJO: " + nombre_control(cfg["controles"]["rojo"]),
                 accion=lambda: self._capturar("rojo")),
            Item(lambda: "VOLUMEN: %d%%" % round(cfg["volumen"] * 100),
                 ajustar=lambda d: self._numero("volumen", d)),
            Item(lambda: "SONIDOS: " + si_no(cfg["sonidos"]),
                 accion=lambda: self._alternar("sonidos"), ajustar=lambda d: self._alternar("sonidos")),
            Item(lambda: "PUNTOS POR APILACIÓN: %d" % cfg["puntos"],
                 ajustar=lambda d: self._numero("puntos", d)),
            Item(lambda: "FILAS (ALTURA): %d" % cfg["filas"],
                 ajustar=lambda d: self._numero("filas", d)),
            Item(lambda: "COLUMNAS (ANCHO): %d" % cfg["columnas"],
                 ajustar=lambda d: self._numero("columnas", d)),
            Item(lambda: "VELOCIDAD: %d / 10" % cfg["velocidad"],
                 ajustar=lambda d: self._numero("velocidad", d)),
            Item(lambda: "EFECTOS VISUALES: " + si_no(cfg["efectos"]),
                 accion=lambda: self._alternar("efectos"), ajustar=lambda d: self._alternar("efectos")),
            Item(lambda: "PANTALLA: " + ("COMPLETA" if cfg["pantalla_completa"] else "VENTANA"),
                 accion=lambda: self._alternar("pantalla_completa"),
                 ajustar=lambda d: self._alternar("pantalla_completa")),
            Item(lambda: "RESTAURAR VALORES PREDETERMINADOS", accion=self._restaurar),
            Item(lambda: "LEER INSTRUCCIONES", accion=j.ir_a_instrucciones),
            Item(lambda: "VER DEMOSTRACIÓN", accion=j.ir_a_demo),
            Item(lambda: "CERRAR EL PROGRAMA", accion=j.salir),
        ]

    def abrir(self):
        self.indice = 0
        self.capturando = None
        self.mensaje = ""

    # ----------------------------------------------------------------- acciones
    def _numero(self, clave, delta):
        self.cfg.ajustar(clave, delta)
        if clave in ESTRUCTURALES:
            self.juego.cambio_estructural = True
            self.mensaje = "Este cambio reinicia la partida al salir del menú."
        self.juego.aplicar_audio()
        self.juego.audio.reproducir("menu")
        self.cfg.guardar()

    def _alternar(self, clave):
        self.cfg[clave] = not self.cfg[clave]
        self.juego.aplicar_audio()
        if clave == "pantalla_completa":
            self.juego.aplicar_pantalla()
        self.juego.audio.reproducir("menu")
        self.cfg.guardar()

    def _restaurar(self):
        self.cfg.restaurar()
        self.juego.cambio_estructural = True
        self.juego.aplicar_audio()
        self.juego.aplicar_pantalla()
        self.juego.audio.reproducir("menu")
        self.cfg.guardar()
        self.mensaje = "Valores predeterminados restaurados."

    def _capturar(self, jugador):
        self.capturando = jugador
        self.mensaje = "Presiona la nueva tecla o pulsador (ESC cancela)."

    # ------------------------------------------------------------------ eventos
    def evento(self, ev):
        if self.capturando:
            self._evento_captura(ev)
            return
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key in (pygame.K_ESCAPE, pygame.K_m):
            self.juego.cerrar_menu()
        elif ev.key == pygame.K_UP:
            self.indice = (self.indice - 1) % len(self.items)
            self.juego.audio.reproducir("menu")
        elif ev.key == pygame.K_DOWN:
            self.indice = (self.indice + 1) % len(self.items)
            self.juego.audio.reproducir("menu")
        elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
            item = self.items[self.indice]
            if item.ajustar:
                item.ajustar(-1 if ev.key == pygame.K_LEFT else 1)
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            item = self.items[self.indice]
            if item.accion:
                self.mensaje = ""
                item.accion()

    def _evento_captura(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
            self.capturando, self.mensaje = None, "Asignación cancelada."
            return
        control = evento_a_control(ev)
        if control is None:
            return
        otro = "rojo" if self.capturando == "azul" else "azul"
        if es_reservada(control):
            self.mensaje = "Esa tecla está reservada para el operador. Elige otra."
        elif control == self.cfg["controles"][otro]:
            self.mensaje = "Ya la usa el otro equipo. Elige otra."
        else:
            self.cfg["controles"][self.capturando] = control
            self.cfg.guardar()
            self.juego.audio.reproducir("menu")
            self.mensaje = "¡Asignado: %s!" % nombre_control(control)
            self.capturando = None

    # ------------------------------------------------------------------- dibujo
    def dibujar(self, c, t):
        velo = pygame.Surface((g.LW, g.LH), pygame.SRCALPHA)
        velo.fill((0, 0, 8, 200))
        c.blit(velo, (0, 0))
        panel = pygame.Rect(0, 0, 820, 650)
        panel.center = (g.LW // 2, g.LH // 2)
        pygame.draw.rect(c, (12, 14, 32), panel, border_radius=22)
        pygame.draw.rect(c, g.AMARILLO, panel, width=4, border_radius=22)
        g.texto(c, "MENÚ DEL OPERADOR  -  PARTIDA EN PAUSA", 36, g.AMARILLO,
                (g.LW // 2, panel.top + 38), contorno=g.NEGRO, grosor=2)
        y0 = panel.top + 82
        for i, item in enumerate(self.items):
            fila = pygame.Rect(panel.left + 30, y0 + i * 32 - 14, panel.w - 60, 30)
            texto = item.etiqueta()
            color = g.BLANCO
            if i == self.indice:
                pygame.draw.rect(c, (40, 46, 96), fila, border_radius=10)
                pygame.draw.rect(c, g.AMARILLO, fila, width=2, border_radius=10)
                color = g.AMARILLO
                if item.ajustar:
                    g.texto(c, "<", 26, g.AMARILLO, (fila.left + 18, fila.centery))
                    g.texto(c, ">", 26, g.AMARILLO, (fila.right - 18, fila.centery))
            elif "AZUL" in texto and "CONTROL" in texto:
                color = COLORES["azul"]
            elif "ROJO" in texto and "CONTROL" in texto:
                color = COLORES["rojo"]
            g.texto(c, texto, 24, color, fila.center)
        g.texto(c, self.mensaje, 22, g.AMARILLO, (g.LW // 2, panel.bottom - 56))
        g.texto(c, "ARRIBA/ABAJO: elegir   IZQ/DER: cambiar   ENTER: aceptar   M o ESC: salir",
                20, g.GRIS, (g.LW // 2, panel.bottom - 24))
