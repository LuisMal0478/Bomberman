"""
Modelo del Enemigo.
Representa la IA de los enemigos que recorren el mapa.
"""

import math
import random
from configuracion import (ANCHO_CASILLA, COLUMNAS, FILAS, ALTO_HUD,
                           CASILLA_VACIA, CASILLA_PARED, CASILLA_BLOQUE, TIPOS_ENEMIGOS)


class Enemigo:
    def __init__(self, posicion_x, posicion_y, tipo_enemigo="balloom"):
        self.posicion_x = float(posicion_x)
        self.posicion_y = float(posicion_y)
        self.posicion_objetivo_x = float(posicion_x)
        self.posicion_objetivo_y = float(posicion_y)

        if tipo_enemigo in TIPOS_ENEMIGOS:
            self.tipo_enemigo = tipo_enemigo
        else:
            self.tipo_enemigo = "balloom"

        datos = TIPOS_ENEMIGOS[self.tipo_enemigo]
        self.salud = datos["salud"]
        self.velocidad = datos["velocidad"]
        self.puntos = datos["puntos"]
        self.color = datos["color"]
        self.traspasa_bloques = datos.get("traspasa_bloques", False)
        self.prob_persecucion = datos.get("prob_persecucion", 0.35)
        self.direccion_x, self.direccion_y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.temporizador_movimiento = 0

    def actualizar(self, matriz_mapa, lista_enemigos, lista_jugadores=None, lista_bombas=None):
        """Mueve al enemigo de forma fluida con IA de persecución y traspaso de ladrillos."""
        paso = max(0.5, self.velocidad * 0.95)

        distancia_objetivo = math.hypot(self.posicion_objetivo_x - self.posicion_x,
                                        self.posicion_objetivo_y - self.posicion_y)

        if distancia_objetivo <= paso:
            self.posicion_x = self.posicion_objetivo_x
            self.posicion_y = self.posicion_objetivo_y

            casilla_x = int(round((self.posicion_x - ANCHO_CASILLA // 2) / ANCHO_CASILLA))
            casilla_y = int(round((self.posicion_y - ALTO_HUD - ANCHO_CASILLA // 2) / ANCHO_CASILLA))
            casilla_x = max(1, min(COLUMNAS - 2, casilla_x))
            casilla_y = max(1, min(FILAS - 2, casilla_y))

            direcciones_validas = []
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx = casilla_x + dx
                ny = casilla_y + dy
                if 0 <= nx < COLUMNAS and 0 <= ny < FILAS:
                    # Las paredes siempre bloquean
                    if matriz_mapa[ny][nx] == CASILLA_PARED:
                        continue
                    # Ladrillo bloquea solo si NO traspasa bloques
                    if matriz_mapa[ny][nx] == CASILLA_BLOQUE and not self.traspasa_bloques:
                        continue
                    # Bombas activas bloquean si no traspasa bloques
                    if lista_bombas and not self.traspasa_bloques:
                        hay_bomba = any(int(b.posicion_x) // ANCHO_CASILLA == nx and
                                        int(b.posicion_y - ALTO_HUD) // ANCHO_CASILLA == ny for b in lista_bombas)
                        if hay_bomba:
                            continue
                    direcciones_validas.append((dx, dy))

            if not direcciones_validas:
                return

            # Persecución inteligente si hay jugadores vivos
            jugador_cercano = None
            if lista_jugadores:
                vivos = [p for p in lista_jugadores if getattr(p, "vivo", True)]
                if vivos:
                    jugador_cercano = min(vivos, key=lambda p: (p.posicion_x - self.posicion_x)**2 +
                                                               (p.posicion_y - self.posicion_y)**2)

            elegida = None
            if jugador_cercano and random.random() < self.prob_persecucion:
                def puntaje_dist(d):
                    px = (casilla_x + d[0]) * ANCHO_CASILLA + ANCHO_CASILLA // 2
                    py = (casilla_y + d[1]) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
                    return (px - jugador_cercano.posicion_x)**2 + (py - jugador_cercano.posicion_y)**2

                direcciones_validas.sort(key=puntaje_dist)
                elegida = direcciones_validas[0]
            else:
                dir_actual = (self.direccion_x, self.direccion_y)
                if dir_actual in direcciones_validas and random.random() < 0.65:
                    elegida = dir_actual
                else:
                    elegida = random.choice(direcciones_validas)

            self.direccion_x, self.direccion_y = elegida
            self.posicion_objetivo_x = float((casilla_x + elegida[0]) * ANCHO_CASILLA + ANCHO_CASILLA // 2)
            self.posicion_objetivo_y = float((casilla_y + elegida[1]) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD)
        else:
            dx = self.posicion_objetivo_x - self.posicion_x
            dy = self.posicion_objetivo_y - self.posicion_y
            if abs(dx) <= paso:
                self.posicion_x = self.posicion_objetivo_x
            else:
                self.posicion_x += math.copysign(paso, dx)

            if abs(dy) <= paso:
                self.posicion_y = self.posicion_objetivo_y
            else:
                self.posicion_y += math.copysign(paso, dy)

    def recibir_danio(self, cantidad=1):
        """Resta salud al enemigo y retorna True si ha muerto."""
        self.salud -= cantidad
        return self.salud <= 0

    def a_diccionario(self):
        """Serializa el enemigo a un diccionario para red."""
        return {
            "x": self.posicion_x,
            "y": self.posicion_y,
            "type": self.tipo_enemigo,
            "hp": self.salud,
            "color": list(self.color),
            "dir": [self.direccion_x, self.direccion_y],
            "pass_blocks": self.traspasa_bloques
        }
