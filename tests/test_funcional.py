"""Pruebas funcionales de TORRE LOCA (sin intervención humana, pantalla/sonido 'dummy').

Ejecutar:   python -m unittest discover -s tests -v
Cubre: competencia simultánea, puntuación, victoria, parpadeo del ganador, X del perdedor,
bloqueo de controles al terminar, reinicio, tecla M (pausa), controles configurables,
sonidos, pantalla completa y funcionamiento sin conexión.
"""
import os
import socket
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame                                            # noqa: E402

from torreloca.configuracion import Configuracion       # noqa: E402
from torreloca.juego import Juego                        # noqa: E402
from torreloca.tableros import VistaTablero              # noqa: E402

DT = 1.0 / 60.0


def tecla(k):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode=""))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ruta_cfg = os.path.join(self.tmp.name, "configuracion.json")
        cfg = Configuracion(self.ruta_cfg)
        cfg["filas"] = 6                                  # torres cortas para acelerar las pruebas
        self.juego = Juego(cfg)

    def tearDown(self):
        pygame.quit()
        self.tmp.cleanup()

    # --- utilidades -----------------------------------------------------------
    def avanzar(self, segundos):
        for _ in range(int(segundos / DT) + 1):
            self.juego.paso(DT)

    def empezar_partida(self):
        tecla(pygame.K_RETURN); self.juego.paso(DT)       # inicio -> instrucciones
        tecla(pygame.K_RETURN); self.juego.paso(DT)       # instrucciones -> cuenta
        self.assertEqual(self.juego.estado, "cuenta")
        self.avanzar(3.3)
        self.assertEqual(self.juego.estado, "juego")

    def pulsar_perfecto(self, clave):
        torre = self.juego.partida.torres[clave]
        torre.colocar(torre.capas[-1][0] if torre.capas else 1)
        tecla(int(self.juego.cfg["controles"][clave].split(":")[1]))
        self.juego.paso(0.0001)

    def ganar(self, clave):
        for _ in range(self.juego.cfg["filas"]):
            self.pulsar_perfecto(clave)


class PruebasFlujo(Base):
    def test_inicio_instrucciones_cuenta_y_juego(self):
        self.assertEqual(self.juego.estado, "inicio")
        self.empezar_partida()

    def test_pulsadores_deshabilitados_durante_la_cuenta(self):
        tecla(pygame.K_RETURN); self.juego.paso(DT)
        tecla(pygame.K_RETURN); self.juego.paso(DT)
        tecla(pygame.K_a); tecla(pygame.K_l); self.juego.paso(DT)
        self.assertEqual(self.juego.partida.torres["azul"].puntos, 0)
        self.assertEqual(self.juego.partida.torres["rojo"].puntos, 0)

    def test_competencia_simultanea_y_puntuacion(self):
        self.empezar_partida()
        torres = self.juego.partida.torres
        torres["azul"].colocar(1); torres["rojo"].colocar(1)
        tecla(pygame.K_a); tecla(pygame.K_l); self.juego.paso(0.0001)   # mismo cuadro
        self.assertEqual(torres["azul"].puntos, self.juego.cfg["puntos"])
        self.assertEqual(torres["rojo"].puntos, self.juego.cfg["puntos"])
        self.pulsar_perfecto("azul")
        self.assertEqual(torres["azul"].puntos, 2 * self.juego.cfg["puntos"])
        self.assertEqual(torres["rojo"].puntos, self.juego.cfg["puntos"])

    def test_ambas_barras_se_mueven_a_la_vez(self):
        self.empezar_partida()
        torres = self.juego.partida.torres
        antes = (torres["azul"].fase, torres["rojo"].fase)
        self.avanzar(0.2)
        self.assertNotEqual(antes[0], torres["azul"].fase)
        self.assertNotEqual(antes[1], torres["rojo"].fase)


class PruebasVictoria(Base):
    def test_victoria_parpadeo_x_y_bloqueo(self):
        self.empezar_partida()
        self.ganar("azul")
        j = self.juego
        self.assertEqual(j.estado, "fin")
        self.assertEqual(j.partida.ganador, "azul")
        # El sonido de victoria se reproduce una sola vez
        self.avanzar(1.0)
        self.assertEqual(j.audio.reproducidos.count("victoria"), 1)
        # Ganador parpadea; perdedor fijo con X
        ganador, perdedor = j.vistas["azul"], j.vistas["rojo"]
        self.assertEqual(ganador.modo, VistaTablero.GANADOR)
        self.assertEqual(perdedor.modo, VistaTablero.PERDEDOR)
        alfas_g = {ganador.alfa_parpadeo(t / 10.0) for t in range(0, 20)}
        alfas_p = {perdedor.alfa_parpadeo(t / 10.0) for t in range(0, 20)}
        self.assertEqual(len(alfas_g), 2)                  # alterna entre visible y atenuado
        self.assertEqual(alfas_p, {255})                   # no parpadea
        # Controles bloqueados y contadores congelados
        puntos = {k: t.puntos for k, t in j.partida.torres.items()}
        tecla(pygame.K_a); tecla(pygame.K_l); self.avanzar(1.0)
        self.assertEqual(puntos, {k: t.puntos for k, t in j.partida.torres.items()})

    def test_reinicio_borra_tableros_y_rehabilita_controles(self):
        self.empezar_partida()
        self.pulsar_perfecto("rojo"); self.ganar("azul")
        self.assertEqual(self.juego.estado, "fin")
        tecla(pygame.K_r); self.juego.paso(DT)
        self.assertEqual(self.juego.estado, "cuenta")
        for torre in self.juego.partida.torres.values():
            self.assertEqual((torre.capas, torre.puntos, torre.completa), ([], 0, False))
        for vista in self.juego.vistas.values():
            self.assertEqual(vista.modo, VistaTablero.JUEGO)
        self.avanzar(3.3)
        self.assertEqual(self.juego.estado, "juego")
        self.pulsar_perfecto("azul")
        self.assertGreater(self.juego.partida.torres["azul"].puntos, 0)


class PruebasMenu(Base):
    def test_tecla_m_pausa_y_reanuda(self):
        self.empezar_partida()
        torre = self.juego.partida.torres["azul"]
        tecla(pygame.K_m); self.juego.paso(DT)
        self.assertTrue(self.juego.menu_abierto)
        fase = torre.fase
        self.avanzar(1.0)
        self.assertEqual(torre.fase, fase)                 # pausada
        tecla(pygame.K_a); self.juego.paso(DT)             # los pulsadores no cuentan en el menú
        self.assertEqual(torre.puntos, 0)
        tecla(pygame.K_m); self.juego.paso(DT)
        self.assertFalse(self.juego.menu_abierto)
        self.avanzar(0.3)
        self.assertNotEqual(torre.fase, fase)              # reanudada

    def test_controles_configurables_y_persistentes(self):
        self.empezar_partida()
        tecla(pygame.K_m); self.juego.paso(DT)
        tecla(pygame.K_DOWN); tecla(pygame.K_DOWN); tecla(pygame.K_RETURN); self.juego.paso(DT)
        self.assertEqual(self.juego.menu.capturando, "azul")
        tecla(pygame.K_m); self.juego.paso(DT)             # tecla reservada: se rechaza
        self.assertEqual(self.juego.menu.capturando, "azul")
        tecla(pygame.K_l); self.juego.paso(DT)             # la usa el otro equipo: se rechaza
        self.assertEqual(self.juego.menu.capturando, "azul")
        tecla(pygame.K_q); self.juego.paso(DT)             # válida
        self.assertIsNone(self.juego.menu.capturando)
        self.assertEqual(self.juego.cfg["controles"]["azul"], "key:%d" % pygame.K_q)
        tecla(pygame.K_m); self.juego.paso(DT)             # cerrar menú
        self.juego.partida.torres["azul"].colocar(1)
        tecla(pygame.K_a); self.juego.paso(0.0001)         # la tecla vieja ya no funciona
        self.assertEqual(self.juego.partida.torres["azul"].puntos, 0)
        tecla(pygame.K_q); self.juego.paso(0.0001)
        self.assertGreater(self.juego.partida.torres["azul"].puntos, 0)
        self.assertEqual(Configuracion(self.ruta_cfg)["controles"]["azul"], "key:%d" % pygame.K_q)

    def test_cambio_de_filas_reinicia_al_salir_del_menu(self):
        self.empezar_partida()
        self.pulsar_perfecto("azul")
        tecla(pygame.K_m); self.juego.paso(DT)
        for _ in range(7):
            tecla(pygame.K_DOWN)
        tecla(pygame.K_RIGHT); self.juego.paso(DT)          # FILAS +1
        self.assertEqual(self.juego.cfg["filas"], 7)
        tecla(pygame.K_m); self.juego.paso(DT)
        self.assertEqual(self.juego.estado, "cuenta")
        self.assertEqual(self.juego.partida.torres["azul"].filas, 7)
        self.assertEqual(self.juego.partida.torres["azul"].puntos, 0)

    def test_restaurar_predeterminados(self):
        self.juego.cfg["volumen"] = 0.1
        tecla(pygame.K_m); self.juego.paso(DT)
        self.juego.menu.items[12].accion()                  # RESTAURAR VALORES PREDETERMINADOS
        self.assertEqual(self.juego.cfg["volumen"], 0.7)
        self.assertEqual(self.juego.cfg["filas"], 16)

    def test_instrucciones_y_demostracion_desde_el_menu(self):
        tecla(pygame.K_m); self.juego.paso(DT)
        self.juego.menu.items[13].accion()                  # LEER INSTRUCCIONES
        self.assertEqual(self.juego.estado, "instrucciones")
        tecla(pygame.K_d); self.juego.paso(DT)
        self.assertEqual(self.juego.estado, "demo")
        self.avanzar(8.0)                                   # la animación integrada corre sin errores
        tecla(pygame.K_RETURN); self.juego.paso(DT)
        self.assertEqual(self.juego.estado, "instrucciones")


class PruebasSistema(Base):
    def test_sonidos_disponibles(self):
        j = self.juego
        self.assertTrue(j.audio.reproducir("menu"))
        j.cfg["sonidos"] = False; j.aplicar_audio()
        self.assertFalse(j.audio.reproducir("menu"))        # silenciado
        if j.audio.ok:
            self.assertEqual(set(j.audio.sonidos), set(("inicio", "cuenta", "ya", "apilar",
                                                        "fallo", "menu", "reinicio", "victoria")))

    def test_pantalla_completa_con_f11(self):
        j = self.juego
        self.assertFalse(j.cfg["pantalla_completa"])
        tecla(pygame.K_F11); j.paso(DT)
        if not j.cfg["pantalla_completa"]:
            self.skipTest("Este entorno de pruebas no admite pantalla completa")
        tecla(pygame.K_F11); j.paso(DT)
        self.assertFalse(j.cfg["pantalla_completa"])

    def test_funciona_sin_conexion(self):
        """Una partida completa no abre ningún socket de red."""
        original = socket.socket

        def prohibido(*a, **k):
            raise AssertionError("El juego intentó usar la red")
        socket.socket = prohibido
        try:
            self.empezar_partida()
            self.ganar("rojo")
            self.assertEqual(self.juego.partida.ganador, "rojo")
        finally:
            socket.socket = original


if __name__ == "__main__":
    unittest.main()
