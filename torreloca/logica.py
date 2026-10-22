"""Lógica del juego, independiente de pygame (se puede probar sin pantalla).

Mecánica: en cada torre una barra de bloques va y viene por la fila actual.
El jugador la detiene con su pulsador. Solo se conserva la parte que coincide
con la fila de abajo; lo que sobresale se pierde. El primero en completar todas
las filas llega a la cima y gana.
"""
from collections import namedtuple

AZUL = "azul"
ROJO = "rojo"
JUGADORES = (AZUL, ROJO)

# tipo: "ok" | "cima" | "fallo"
Resultado = namedtuple(
    "Resultado",
    "jugador tipo fila ini ancho barra_ini barra_ancho perdidas puntos",
)


class Torre:
    """Torre de un jugador."""

    def __init__(self, columnas, filas, valor_apilacion, velocidad, ancho_inicial=None):
        self.columnas = int(columnas)
        self.filas = int(filas)
        self.valor = int(valor_apilacion)
        self.velocidad = int(velocidad)
        if ancho_inicial is None:
            ancho_inicial = max(1, self.columnas - 2)
        self.ancho_inicial = max(1, min(int(ancho_inicial), self.columnas))
        self.reiniciar()

    # ------------------------------------------------------------------ estado
    def reiniciar(self):
        """Borra el tablero y restablece el contador."""
        self.capas = []            # [(columna_inicial, ancho)] de abajo hacia arriba
        self.puntos = 0
        self.fallos = 0
        self.completa = False
        self.bloqueada = False
        self.ancho = self.ancho_inicial
        self._nueva_fila()

    def _nueva_fila(self):
        # La barra entra alternando lados: izquierda en filas pares, derecha en impares.
        self.fase = float(self.maximo) if len(self.capas) % 2 else 0.0

    # --------------------------------------------------------------- consultas
    @property
    def fila_actual(self):
        return len(self.capas)

    @property
    def maximo(self):
        """Posición máxima (columna inicial) que puede tomar la barra."""
        return max(0, self.columnas - self.ancho)

    @property
    def velocidad_actual(self):
        """Celdas por segundo; aumenta con la altura."""
        base = 1.5 + self.velocidad * 0.6
        return min(14.0, base + 0.25 * len(self.capas))

    @property
    def pos(self):
        maximo = self.maximo
        if maximo == 0:
            return 0.0
        return self.fase if self.fase <= maximo else 2 * maximo - self.fase

    @property
    def celda_actual(self):
        return int(round(self.pos))

    # ------------------------------------------------------------- movimiento
    def actualizar(self, dt):
        if self.bloqueada or self.completa:
            return
        maximo = self.maximo
        if maximo == 0:
            self.fase = 0.0
            return
        periodo = 2.0 * maximo
        self.fase = (self.fase + self.velocidad_actual * dt) % periodo

    def colocar(self, columna):
        """Coloca la barra en 'columna' (útil para demostraciones y pruebas)."""
        self.fase = float(max(0, min(self.maximo, columna)))

    # ----------------------------------------------------------------- acción
    def apilar(self, jugador=AZUL):
        """Detiene la barra. Devuelve un Resultado, o None si la torre está bloqueada."""
        if self.bloqueada or self.completa:
            return None
        fila = len(self.capas)
        b_ini = self.celda_actual
        b_ancho = self.ancho
        b_fin = b_ini + b_ancho

        if not self.capas:
            ini, ancho = b_ini, b_ancho                      # la base siempre es válida
        else:
            p_ini, p_ancho = self.capas[-1]
            ini = max(b_ini, p_ini)
            fin = min(b_fin, p_ini + p_ancho)
            ancho = fin - ini

        if ancho <= 0:
            # Fallo total: la torre se derrumba y se empieza de nuevo (los puntos se conservan).
            self.fallos += 1
            self.capas = []
            self.ancho = self.ancho_inicial
            self._nueva_fila()
            return Resultado(jugador, "fallo", fila, b_ini, 0, b_ini, b_ancho, b_ancho, 0)

        self.capas.append((ini, ancho))
        self.ancho = ancho
        self.puntos += self.valor
        perdidas = b_ancho - ancho
        if len(self.capas) >= self.filas:
            self.completa = True
            tipo = "cima"
        else:
            tipo = "ok"
            self._nueva_fila()
        return Resultado(jugador, tipo, fila, ini, ancho, b_ini, b_ancho, perdidas, self.valor)


class Partida:
    """Dos torres compitiendo a la vez."""

    ESPERA, JUGANDO, TERMINADA = "espera", "jugando", "terminada"

    def __init__(self, columnas=9, filas=16, valor_apilacion=100, velocidad=5):
        self.params = (columnas, filas, valor_apilacion, velocidad)
        self.torres = {j: Torre(*self.params) for j in JUGADORES}
        self.reiniciar()

    @classmethod
    def desde_config(cls, cfg):
        return cls(cfg["columnas"], cfg["filas"], cfg["puntos"], cfg["velocidad"])

    def reiniciar(self):
        """Limpia ambos tableros, restablece contadores y deja la partida en espera."""
        for torre in self.torres.values():
            torre.reiniciar()
            torre.bloqueada = True        # los pulsadores siguen deshabilitados hasta iniciar()
        self.estado = self.ESPERA
        self.ganador = None

    def iniciar(self):
        self.estado = self.JUGANDO
        self.ganador = None
        for torre in self.torres.values():
            torre.bloqueada = False

    @property
    def perdedor(self):
        if self.ganador is None:
            return None
        return ROJO if self.ganador == AZUL else AZUL

    def actualizar(self, dt):
        if self.estado != self.JUGANDO:
            return
        for torre in self.torres.values():
            torre.actualizar(dt)

    def pulsar(self, jugador):
        """Procesa el pulsador de 'jugador'. Devuelve Resultado o None si no cuenta."""
        if self.estado != self.JUGANDO:
            return None
        resultado = self.torres[jugador].apilar(jugador)
        if resultado is not None and resultado.tipo == "cima":
            self._terminar(jugador)
        return resultado

    def _terminar(self, ganador):
        self.ganador = ganador
        self.estado = self.TERMINADA
        for torre in self.torres.values():     # contadores congelados y pulsadores bloqueados
            torre.bloqueada = True
