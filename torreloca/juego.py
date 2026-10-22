"""Bucle principal y máquina de estados de TORRE LOCA.

Estados: inicio -> instrucciones -> cuenta -> juego -> fin  (y 'demo' desde instrucciones/menú).
"""
import pygame

from . import graficos as g
from .audio import Audio
from .configuracion import Configuracion
from .instrucciones import Demostracion, dibujar_instrucciones
from .jugadores import (COLORES, JUGADORES_EVENTOS, NOMBRES, agregar_joystick,
                        control_coincide, inicializar_joysticks)
from .logica import AZUL, ROJO, JUGADORES, Partida
from .menu import Menu
from .tableros import CX, VistaTablero

SEG_CUENTA = 1.0        # segundos por número de la cuenta regresiva
SEG_YA = 0.8            # tiempo que se muestra "¡YA!"


class Juego:
    def __init__(self, cfg=None):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("TORRE LOCA - Desafíos Locos")
        self.cfg = cfg or Configuracion()
        self.reloj = pygame.time.Clock()
        self.lienzo = pygame.Surface((g.LW, g.LH))
        self.tam_ventana = (1280, 720)
        self.pantalla = None
        self._crear_ventana()
        self.audio = Audio(self.cfg)
        inicializar_joysticks()
        self.menu = Menu(self)
        self.demo = None
        self.t = 0.0
        self.estado = "inicio"
        self.estado_previo = None          # a dónde volver tras leer instrucciones desde el menú
        self.estado_tras_demo = "inicio"
        self.menu_abierto = False
        self.cambio_estructural = False
        self.ejecutando = True
        self.t_estado = 0.0
        self.ya_timer = 0.0
        self.ultimo_numero = None
        self._crear_partida()

    # ------------------------------------------------------------------ ventana
    def _crear_ventana(self):
        if self.cfg["pantalla_completa"]:
            try:
                self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                pygame.mouse.set_visible(False)
                return
            except pygame.error:
                self.cfg["pantalla_completa"] = False     # sin soporte: seguir en ventana
        self.pantalla = pygame.display.set_mode(self.tam_ventana, pygame.RESIZABLE)
        pygame.mouse.set_visible(True)

    def aplicar_pantalla(self):
        self._crear_ventana()

    def aplicar_audio(self):
        self.audio.volumen = self.cfg["volumen"]
        self.audio.activo = self.cfg["sonidos"]

    def _presentar(self):
        ventana = pygame.display.get_surface()
        w, h = ventana.get_size()
        esc = min(w / g.LW, h / g.LH)
        nw, nh = max(1, int(g.LW * esc)), max(1, int(g.LH * esc))
        if (nw, nh) == (g.LW, g.LH) and (w, h) == (g.LW, g.LH):
            ventana.blit(self.lienzo, (0, 0))
        else:
            ventana.fill((0, 0, 0))
            ventana.blit(pygame.transform.smoothscale(self.lienzo, (nw, nh)),
                         ((w - nw) // 2, (h - nh) // 2))
        pygame.display.flip()

    # ------------------------------------------------------------------ partida
    def _crear_partida(self):
        self.partida = Partida.desde_config(self.cfg)
        self.vistas = {j: VistaTablero(j, self.partida.torres[j], CX[j]) for j in JUGADORES}
        self.t_estado = 0.0
        self.ya_timer = 0.0
        self.ultimo_numero = None

    def comenzar_cuenta(self):
        """Limpia ambos tableros y arranca la cuenta regresiva (pulsadores aún deshabilitados)."""
        self._crear_partida()
        self.estado = "cuenta"

    def reiniciar_partida(self):
        """Acción del operador: borra tableros, restablece puntos y habilita controles tras la cuenta."""
        self.menu_abierto = False
        self.cambio_estructural = False
        self.audio.reproducir("reinicio")
        self.comenzar_cuenta()

    def _pulsar(self, clave):
        res = self.partida.pulsar(clave)
        if res is None:
            return
        self.vistas[clave].efecto(res, self.cfg["efectos"])
        self.audio.reproducir("fallo" if res.tipo == "fallo" else "apilar")
        if res.tipo == "cima":
            self._terminar()

    def _terminar(self):
        self.estado = "fin"
        self.t_estado = 0.0
        self.vistas[self.partida.ganador].modo = VistaTablero.GANADOR
        self.vistas[self.partida.perdedor].modo = VistaTablero.PERDEDOR
        self.audio.reproducir("victoria")          # una sola vez al declarar al ganador

    # --------------------------------------------------------------------- menú
    def abrir_menu(self):
        self.menu_abierto = True
        self.menu.abrir()
        self.audio.reproducir("menu")

    def cerrar_menu(self):
        self.menu_abierto = False
        if self.cambio_estructural:
            self.cambio_estructural = False
            if self.estado in ("cuenta", "juego", "fin"):
                self.comenzar_cuenta()
            else:
                self._crear_partida()

    def ir_a_instrucciones(self):
        self.menu_abierto = False
        if self.estado in ("cuenta", "juego", "fin"):
            self.estado_previo = self.estado
        self.estado = "instrucciones"

    def ir_a_demo(self):
        self.menu_abierto = False
        self.estado_tras_demo = self.estado if self.estado != "demo" else "inicio"
        self.demo = Demostracion(self)
        self.estado = "demo"

    def salir(self):
        self.cfg.guardar()
        self.ejecutando = False

    # ------------------------------------------------------------------ eventos
    def _eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.salir()
            elif ev.type == pygame.JOYDEVICEADDED:
                agregar_joystick(ev.device_index)
            elif ev.type == pygame.VIDEORESIZE:
                if not self.cfg["pantalla_completa"]:
                    self.tam_ventana = (max(320, ev.w), max(180, ev.h))
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11 and not self.menu.capturando:
                self.cfg["pantalla_completa"] = not self.cfg["pantalla_completa"]
                self.cfg.guardar()
                self.aplicar_pantalla()
            elif self.menu_abierto:
                self.menu.evento(ev)
            else:
                if ev.type == pygame.KEYDOWN:
                    self._tecla_operador(ev)
                if ev.type in JUGADORES_EVENTOS and self.estado == "juego" and not self.menu_abierto:
                    for clave in JUGADORES:
                        if control_coincide(ev, self.cfg["controles"][clave]):
                            self._pulsar(clave)

    def _tecla_operador(self, ev):
        k = ev.key
        enter = k in (pygame.K_RETURN, pygame.K_KP_ENTER)
        if k == pygame.K_m:
            self.abrir_menu()
        elif self.estado == "inicio" and enter:
            self.audio.reproducir("inicio")
            self.estado_previo = None
            self.estado = "instrucciones"
        elif self.estado == "instrucciones":
            if enter:
                self.audio.reproducir("inicio")
                if self.estado_previo:
                    self.estado, self.estado_previo = self.estado_previo, None
                else:
                    self.comenzar_cuenta()
            elif k == pygame.K_ESCAPE:
                self.estado, self.estado_previo = (self.estado_previo or "inicio"), None
            elif k == pygame.K_d:
                self.ir_a_demo()
        elif self.estado == "demo" and (enter or k in (pygame.K_ESCAPE, pygame.K_SPACE)):
            self.estado = self.estado_tras_demo
            self.demo = None
        elif self.estado in ("cuenta", "juego", "fin") and (k == pygame.K_r or (enter and self.estado == "fin")):
            self.reiniciar_partida()

    # --------------------------------------------------------------- actualizar
    def _actualizar(self, dt):
        self.t += dt
        if self.menu_abierto:
            return                                   # la partida está en pausa
        if self.estado == "cuenta":
            self._actualizar_cuenta(dt)
        elif self.estado == "juego":
            self.ya_timer = max(0.0, self.ya_timer - dt)
            self.partida.actualizar(dt)
        elif self.estado == "demo" and self.demo:
            self.demo.actualizar(dt)
        if self.estado in ("cuenta", "juego", "fin"):
            for vista in self.vistas.values():
                vista.actualizar(dt)

    def _actualizar_cuenta(self, dt):
        self.t_estado += dt
        if self.t_estado >= 3 * SEG_CUENTA:
            self.partida.iniciar()                   # a partir de aquí los pulsadores funcionan
            self.estado = "juego"
            self.ya_timer = SEG_YA
            self.audio.reproducir("ya")
            return
        numero = 3 - int(self.t_estado // SEG_CUENTA)
        if numero != self.ultimo_numero:
            self.ultimo_numero = numero
            self.audio.reproducir("cuenta")

    # ------------------------------------------------------------------- dibujo
    def _dibujar(self):
        c = self.lienzo
        efectos = self.cfg["efectos"]
        c.blit(g.fondo(), (0, 0))
        if self.estado == "demo" and self.demo and self.demo.video is not None:
            pass
        else:
            g.luces(c, self.t, efectos)
        if self.estado == "inicio":
            self._dibujar_inicio(c)
        elif self.estado == "instrucciones":
            dibujar_instrucciones(c, self)
        elif self.estado == "demo" and self.demo:
            self.demo.dibujar(c, self.t, efectos)
        else:
            self._dibujar_juego(c, efectos)
        if self.menu_abierto:
            self.menu.dibujar(c, self.t)
        self._presentar()

    def _dibujar_inicio(self, c):
        g.texto(c, "DESAFÍOS LOCOS PRESENTA", 36, g.AMARILLO, (640, 140), contorno=g.NEGRO, grosor=3)
        g.texto(c, "TORRE LOCA", 150, (230, 40, 50), (646, 276), contorno=g.NEGRO, grosor=5)
        g.texto(c, "TORRE LOCA", 150, g.BLANCO, (640, 270), contorno=(30, 70, 220), grosor=5)
        g.texto(c, "¡APILA, COMPITE Y LLEGA A LA CIMA!", 46, g.AMARILLO, (640, 392),
                contorno=g.NEGRO, grosor=3)
        g.texto(c, NOMBRES[AZUL], 40, COLORES[AZUL], (330, 480), contorno=g.NEGRO, grosor=3)
        g.texto(c, "VS", 54, (230, 40, 50), (640, 480), contorno=g.AMARILLO, grosor=3)
        g.texto(c, NOMBRES[ROJO], 40, COLORES[ROJO], (950, 480), contorno=g.NEGRO, grosor=3)
        g.texto(c, "¡Dos jugadores, una torre y un solo ganador!", 30, g.BLANCO, (640, 546),
                contorno=g.NEGRO, grosor=2)
        if int(self.t * 2.5) % 2 == 0:
            g.texto(c, "PRESIONA ENTER PARA INICIAR", 52, g.AMARILLO, (640, 626),
                    contorno=g.NEGRO, grosor=3)
        g.texto(c, "M = menú del operador     F11 = pantalla completa", 20, g.GRIS, (640, 676))

    def _dibujar_juego(self, c, efectos):
        for clave in JUGADORES:
            vista = self.vistas[clave]
            vista.dibujar(c, self.t, efectos)
            vista.dibujar_marcador(c, self.t, efectos)
        g.dibujar_vs(c)
        if self.estado == "fin":
            col = COLORES[self.partida.ganador]
            g.texto(c, "¡GANADOR DE", 38, g.BLANCO, (640, 400), contorno=g.NEGRO, grosor=3)
            g.texto(c, "TORRE LOCA!", 52, g.AMARILLO, (640, 450), contorno=g.NEGRO, grosor=3)
            g.texto(c, NOMBRES[self.partida.ganador], 42, col, (640, 520), contorno=g.NEGRO, grosor=3)
            g.texto(c, "Operador: R = reiniciar", 22, g.GRIS, (640, 590))
            g.texto(c, "M = menú", 22, g.GRIS, (640, 620))
        elif self.estado == "cuenta":
            numero = 3 - int(self.t_estado // SEG_CUENTA)
            g.texto(c, str(max(1, numero)), 190, g.AMARILLO, (640, 470), contorno=g.NEGRO, grosor=6)
        else:
            if self.ya_timer > 0:
                g.texto(c, "¡YA!", 120, g.AMARILLO, (640, 470), contorno=g.NEGRO, grosor=5)
            else:
                g.dibujar_logo(c, (640, 480))

    # --------------------------------------------------------------- bucle
    def paso(self, dt=None):
        """Un cuadro completo: eventos, lógica y dibujo (también lo usan las pruebas)."""
        if dt is None:
            dt = min(0.05, self.reloj.tick(60) / 1000.0)
        self._eventos()
        self._actualizar(dt)
        self._dibujar()

    def ejecutar(self):
        while self.ejecutando:
            self.paso()
        pygame.quit()
