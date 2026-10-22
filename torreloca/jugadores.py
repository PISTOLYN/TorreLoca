"""Jugadores, nombres, colores y traducción de teclas/pulsadores físicos.

Un 'control' es un texto: "key:<código>" (teclado) o "joy:<id>:<botón>" (mando/pulsador USB).
Muchas botoneras arcade (Zero Delay, I-PAC, etc.) se comportan como un teclado: en ese
caso se configuran igual que una tecla.
"""
import pygame

from .logica import AZUL, ROJO

NOMBRES = {AZUL: "EQUIPO AZUL", ROJO: "EQUIPO ROJO"}
COLORES = {AZUL: (40, 150, 255), ROJO: (255, 60, 70)}

# Teclas del operador que no se pueden asignar a un jugador.
RESERVADAS = {pygame.K_m, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER,
              pygame.K_F11, pygame.K_r}

_joysticks = {}

JUGADORES_EVENTOS = (pygame.KEYDOWN, pygame.JOYBUTTONDOWN)


def evento_a_control(ev):
    """Convierte un evento de teclado/pulsador en texto de control (o None)."""
    if ev.type == pygame.KEYDOWN:
        return "key:%d" % ev.key
    if ev.type == pygame.JOYBUTTONDOWN:
        dispositivo = getattr(ev, "instance_id", None)
        if dispositivo is None:
            dispositivo = getattr(ev, "joy", 0)
        return "joy:%d:%d" % (dispositivo, ev.button)
    return None


def control_coincide(ev, texto):
    return evento_a_control(ev) == texto


def es_reservada(texto):
    partes = texto.split(":")
    return partes[0] == "key" and int(partes[1]) in RESERVADAS


def nombre_control(texto):
    """Texto legible para mostrar en pantalla."""
    partes = texto.split(":")
    try:
        if partes[0] == "key":
            nombre = pygame.key.name(int(partes[1])) or partes[1]
            return "TECLA " + nombre.upper()
        if partes[0] == "joy":
            return "PULSADOR %s (DISPOSITIVO %s)" % (partes[2], partes[1])
    except (ValueError, IndexError):
        pass
    return texto


def inicializar_joysticks():
    pygame.joystick.init()
    for indice in range(pygame.joystick.get_count()):
        agregar_joystick(indice)


def agregar_joystick(indice):
    """Activa un mando/pulsador USB (pygame solo envía sus eventos si se mantiene la referencia)."""
    try:
        joy = pygame.joystick.Joystick(indice)
        try:
            joy.init()
        except Exception:
            pass
        try:
            _joysticks[joy.get_instance_id()] = joy
        except Exception:
            _joysticks[indice] = joy
    except pygame.error:
        pass


def probar_controles():
    """Herramienta para el operador: muestra el código de cada tecla/pulsador detectado.

    Ejecutar:  TorreLoca.exe --probar-controles   (ESC para salir)
    """
    pygame.init()
    inicializar_joysticks()
    pantalla = pygame.display.set_mode((960, 540))
    pygame.display.set_caption("TORRE LOCA - Probar controles")
    fuente = pygame.font.Font(None, 30)
    lineas = ["Presiona cualquier tecla o pulsador. ESC para salir.",
              "Dispositivos detectados: %d" % pygame.joystick.get_count()]
    reloj = pygame.time.Clock()
    activo = True
    while activo:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                activo = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                activo = False
            elif ev.type == pygame.JOYDEVICEADDED:
                agregar_joystick(ev.device_index)
                lineas.append("Dispositivo conectado (índice %d)" % ev.device_index)
            else:
                control = evento_a_control(ev)
                if control:
                    lineas.append("%s   ->   %s" % (nombre_control(control), control))
        pantalla.fill((12, 14, 28))
        for i, texto in enumerate(lineas[-14:]):
            pantalla.blit(fuente.render(texto, True, (235, 235, 245)), (30, 30 + i * 34))
        pygame.display.flip()
        reloj.tick(30)
    pygame.quit()
