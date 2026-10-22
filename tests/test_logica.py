"""Pruebas de la lógica (sin pantalla). Ejecutar: python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from torreloca.logica import AZUL, ROJO, Partida, Torre
from torreloca.configuracion import Configuracion, PREDETERMINADOS


def apilar_perfecto(torre):
    """Coloca la barra exactamente sobre la fila anterior y apila."""
    ini = torre.capas[-1][0] if torre.capas else 1
    torre.colocar(ini)
    return torre.apilar()


class PruebasTorre(unittest.TestCase):
    def test_base_siempre_valida_y_suma_puntos(self):
        t = Torre(9, 8, 100, 5)
        r = t.apilar()
        self.assertEqual(r.tipo, "ok")
        self.assertEqual(t.puntos, 100)
        self.assertEqual(len(t.capas), 1)
        self.assertEqual(t.capas[0][1], 7)       # ancho inicial = columnas - 2

    def test_lo_que_sobresale_se_pierde(self):
        t = Torre(9, 8, 100, 5)
        t.colocar(1); t.apilar()                  # base en columnas 1..8 (ancho 7)
        t.colocar(2)                              # barra 2..9 -> solape 2..8 = 6
        r = t.apilar()
        self.assertEqual(r.tipo, "ok")
        self.assertEqual((r.ini, r.ancho, r.perdidas), (2, 6, 1))
        self.assertEqual(t.ancho, 6)
        t.colocar(3)                              # barra 3..9 sobre 2..8 -> solape 3..8 = 5
        r = t.apilar()
        self.assertEqual((r.ini, r.ancho, r.perdidas), (3, 5, 1))
        self.assertEqual(t.puntos, 300)

    def test_fallo_total_reinicia_torre_y_conserva_puntos(self):
        t = Torre(9, 8, 100, 5, ancho_inicial=2)
        t.colocar(0); t.apilar()                  # base 0..2
        t.colocar(6)                              # sin solape
        r = t.apilar()
        self.assertEqual(r.tipo, "fallo")
        self.assertEqual(len(t.capas), 0)
        self.assertEqual(t.ancho, 2)
        self.assertEqual(t.puntos, 100)
        self.assertEqual(t.fallos, 1)

    def test_llegar_a_la_cima(self):
        t = Torre(9, 6, 100, 5)
        for _ in range(5):
            self.assertEqual(apilar_perfecto(t).tipo, "ok")
        self.assertEqual(apilar_perfecto(t).tipo, "cima")
        self.assertTrue(t.completa)
        self.assertIsNone(t.apilar())            # ya no acepta más

    def test_barra_rebota_dentro_del_tablero(self):
        t = Torre(9, 8, 100, 10)
        for _ in range(2000):
            t.actualizar(0.016)
            self.assertGreaterEqual(t.pos, 0)
            self.assertLessEqual(t.pos, t.maximo)

    def test_velocidad_aumenta_con_la_altura(self):
        t = Torre(9, 12, 100, 5)
        v0 = t.velocidad_actual
        apilar_perfecto(t); apilar_perfecto(t)
        self.assertGreater(t.velocidad_actual, v0)

    def test_reiniciar_borra_todo(self):
        t = Torre(9, 8, 100, 5)
        apilar_perfecto(t); apilar_perfecto(t)
        t.reiniciar()
        self.assertEqual((t.capas, t.puntos, t.fallos, t.completa), ([], 0, 0, False))


class PruebasPartida(unittest.TestCase):
    def test_competencia_simultanea(self):
        p = Partida(9, 8, 100, 5); p.iniciar()
        p.torres[AZUL].colocar(1); p.pulsar(AZUL)
        p.torres[ROJO].colocar(1); p.pulsar(ROJO)
        self.assertEqual(p.torres[AZUL].puntos, 100)
        self.assertEqual(p.torres[ROJO].puntos, 100)
        p.pulsar(AZUL)
        self.assertEqual(p.torres[AZUL].puntos, 200)
        self.assertEqual(p.torres[ROJO].puntos, 100)   # el otro tablero no se afecta

    def test_no_se_puede_jugar_en_espera(self):
        p = Partida(9, 8, 100, 5)
        self.assertIsNone(p.pulsar(AZUL))
        self.assertEqual(p.torres[AZUL].puntos, 0)

    def test_primero_en_la_cima_gana_y_se_bloquea_todo(self):
        p = Partida(9, 6, 100, 5); p.iniciar()
        for _ in range(6):
            r = p.torres[ROJO].capas[-1][0] if p.torres[ROJO].capas else 1
            p.torres[ROJO].colocar(r); p.pulsar(ROJO)
        self.assertEqual(p.ganador, ROJO)
        self.assertEqual(p.perdedor, AZUL)
        self.assertEqual(p.estado, Partida.TERMINADA)
        # Pulsadores deshabilitados y contadores congelados
        puntos = {j: t.puntos for j, t in p.torres.items()}
        self.assertIsNone(p.pulsar(AZUL))
        self.assertIsNone(p.pulsar(ROJO))
        for _ in range(50):
            p.actualizar(0.016)
        self.assertEqual(puntos, {j: t.puntos for j, t in p.torres.items()})

    def test_ganador_es_el_primero_aunque_el_otro_este_cerca(self):
        p = Partida(9, 6, 100, 5); p.iniciar()
        for _ in range(5):
            for j in (AZUL, ROJO):
                t = p.torres[j]; t.colocar(t.capas[-1][0] if t.capas else 1); p.pulsar(j)
        t = p.torres[AZUL]; t.colocar(t.capas[-1][0]); p.pulsar(AZUL)   # azul llega primero
        t = p.torres[ROJO]; t.colocar(t.capas[-1][0]); p.pulsar(ROJO)   # rojo ya no cuenta
        self.assertEqual(p.ganador, AZUL)
        self.assertEqual(p.torres[ROJO].puntos, 500)

    def test_reinicio_limpia_ambos_tableros(self):
        p = Partida(9, 6, 100, 5); p.iniciar()
        for _ in range(6):
            t = p.torres[AZUL]; t.colocar(t.capas[-1][0] if t.capas else 1); p.pulsar(AZUL)
        p.pulsar(ROJO)
        p.reiniciar()
        for t in p.torres.values():
            self.assertEqual((t.capas, t.puntos, t.completa), ([], 0, False))
        self.assertIsNone(p.ganador)
        self.assertEqual(p.estado, Partida.ESPERA)
        p.iniciar()                                # controles habilitados otra vez
        self.assertIsNotNone(p.pulsar(AZUL))


class PruebasConfiguracion(unittest.TestCase):
    def test_guardar_y_cargar(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "c.json")
            c = Configuracion(ruta)
            c.ajustar("volumen", -3); c.ajustar("filas", 2); c["controles"]["azul"] = "key:113"
            c["pantalla_completa"] = True
            c.guardar()
            c2 = Configuracion(ruta)
            self.assertEqual(c2["volumen"], 0.4)
            self.assertEqual(c2["filas"], 18)
            self.assertEqual(c2["controles"]["azul"], "key:113")
            self.assertTrue(c2["pantalla_completa"])

    def test_limites_y_restaurar(self):
        with tempfile.TemporaryDirectory() as d:
            c = Configuracion(os.path.join(d, "c.json"))
            for _ in range(50):
                c.ajustar("columnas", 1)
            self.assertEqual(c["columnas"], 12)
            c.restaurar()
            self.assertEqual(c.datos, PREDETERMINADOS)

    def test_archivo_corrupto_usa_predeterminados(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "c.json")
            with open(ruta, "w") as f:
                f.write("{esto no es json")
            self.assertEqual(Configuracion(ruta).datos, PREDETERMINADOS)


if __name__ == "__main__":
    unittest.main()
