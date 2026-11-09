"""
Modelo del Jugador.
Representa el estado y comportamiento de un jugador en el juego.
"""

from configuracion import (ANCHO_CASILLA, COLUMNAS, FILAS, ALTO_HUD,
                           ANCHO_JUEGO, ALTO_JUEGO, CASILLA_VACIA, PERSONAJES)


class Jugador:
    def __init__(self, indice_jugador, clave_personaje, nombre="Jugador"):
        self.indice = indice_jugador
        self.clave_personaje = clave_personaje if clave_personaje in PERSONAJES else "bomberman"
        datos_personaje = PERSONAJES[self.clave_personaje]

        posiciones_spawn = [
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
        ]
        sx, sy = posiciones_spawn[indice_jugador % len(posiciones_spawn)]

        self.posicion_x = float(sx)
        self.posicion_y = float(sy)
        self.velocidad = float(datos_personaje["velocidad"])
        self.potencia_fuego = datos_personaje["potencia_fuego"]
        self.bombas_maximas = datos_personaje["bombas_maximas"]
        self.bombas_activas = 0
        self.vidas = 3
        self.color = datos_personaje["color"]
        self.acento = datos_personaje["acento"]
        self.nombre = nombre
        self.vivo = True
        self.temporizador_invulnerabilidad = 0
        self.temporizador_escudo = 0
        self.puntaje = 0
        self.direccion_x = 0
        self.direccion_y = 1

    def reaparecer(self):
        """Reinicia la posición del jugador al perder una vida."""
        posiciones_spawn = [
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
        ]
        sx, sy = posiciones_spawn[self.indice % len(posiciones_spawn)]
        self.posicion_x = float(sx)
        self.posicion_y = float(sy)
        self.temporizador_invulnerabilidad = 120

    def mover(self, dx, dy, matriz_mapa, lista_enemigos, otros_jugadores, lista_bombas=None):
        """Calcula el movimiento fluido con auto-centrado en el carril y deslizamiento de esquinas."""
        if not self.vivo:
            return

        self.direccion_x = dx
        self.direccion_y = dy

        velocidad = self.velocidad
        r = 10  # Radio compacto de 20x20 para fluidez en pasillos

        def es_libre(tx, ty):
            if (tx - r < ANCHO_CASILLA or tx + r > (COLUMNAS - 1) * ANCHO_CASILLA or
                    ty - r < ALTO_HUD + ANCHO_CASILLA or ty + r > ALTO_HUD + (FILAS - 1) * ANCHO_CASILLA):
                return False
            for ox, oy in [(-r, -r), (r, -r), (-r, r), (r, r)]:
                cx = int(tx + ox) // ANCHO_CASILLA
                cy = int(ty + oy - ALTO_HUD) // ANCHO_CASILLA
                if cx < 0 or cx >= COLUMNAS or cy < 0 or cy >= FILAS:
                    return False
                if matriz_mapa[cy][cx] != CASILLA_VACIA:
                    return False
            # Las bombas no bloquean al jugador para permitirle pasar y no quedarse atrapado
            return True

        if dx != 0 and dy == 0:
            # Movimiento horizontal con centrado vertical
            cur_r = int(round((self.posicion_y - ALTO_HUD - ANCHO_CASILLA // 2) / ANCHO_CASILLA))
            cur_r = max(1, min(FILAS - 2, cur_r))
            centro_y = cur_r * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
            diff_y = centro_y - self.posicion_y

            nudge_y = math.copysign(min(abs(diff_y), velocidad * 0.7), diff_y) if abs(diff_y) > 0.5 else 0.0
            next_x = self.posicion_x + dx * velocidad
            next_y = self.posicion_y + nudge_y

            if es_libre(next_x, next_y):
                self.posicion_x = next_x
                self.posicion_y = next_y
            elif es_libre(next_x, self.posicion_y):
                self.posicion_x = next_x
            elif abs(diff_y) > 0.5 and es_libre(self.posicion_x + dx * (velocidad * 0.5), centro_y):
                self.posicion_y += math.copysign(min(abs(diff_y), velocidad), diff_y)
                if es_libre(self.posicion_x + dx * (velocidad * 0.5), self.posicion_y):
                    self.posicion_x += dx * (velocidad * 0.5)

        elif dy != 0 and dx == 0:
            # Movimiento vertical con centrado horizontal
            cur_c = int(round((self.posicion_x - ANCHO_CASILLA // 2) / ANCHO_CASILLA))
            cur_c = max(1, min(COLUMNAS - 2, cur_c))
            centro_x = cur_c * ANCHO_CASILLA + ANCHO_CASILLA // 2
            diff_x = centro_x - self.posicion_x

            nudge_x = math.copysign(min(abs(diff_x), velocidad * 0.7), diff_x) if abs(diff_x) > 0.5 else 0.0
            next_x = self.posicion_x + nudge_x
            next_y = self.posicion_y + dy * velocidad

            if es_libre(next_x, next_y):
                self.posicion_x = next_x
                self.posicion_y = next_y
            elif es_libre(self.posicion_x, next_y):
                self.posicion_y = next_y
            elif abs(diff_x) > 0.5 and es_libre(centro_x, self.posicion_y + dy * (velocidad * 0.5)):
                self.posicion_x += math.copysign(min(abs(diff_x), velocidad), diff_x)
                if es_libre(self.posicion_x, self.posicion_y + dy * (velocidad * 0.5)):
                    self.posicion_y += dy * (velocidad * 0.5)

    def recibir_danio(self):
        """Aplica daño al jugador reduciendo vidas e invulnerabilidad."""
        if self.temporizador_escudo > 0 or self.temporizador_invulnerabilidad > 0:
            return False

        self.vidas -= 1
        if self.vidas <= 0:
            self.vivo = False
        else:
            self.reaparecer()
        return True

    def recibir_mejora(self, tipo_mejora):
        """Aplica un efecto de power-up al jugador."""
        if tipo_mejora == "mas_bomba":
            self.bombas_maximas = min(8, self.bombas_maximas + 1)
        elif tipo_mejora == "mas_fuego":
            self.potencia_fuego = min(8, self.potencia_fuego + 1)
        elif tipo_mejora == "mas_velocidad":
            self.velocidad = min(6.0, self.velocidad + 0.5)
        elif tipo_mejora == "escudo":
            self.temporizador_escudo = 300
        elif tipo_mejora == "mas_vida":
            self.vidas = min(5, self.vidas + 1)

    def actualizar(self):
        """Actualiza temporizadores de estado del jugador."""
        if self.temporizador_invulnerabilidad > 0:
            self.temporizador_invulnerabilidad -= 1
        if self.temporizador_escudo > 0:
            self.temporizador_escudo -= 1

    def a_diccionario(self):
        """Serializa el jugador a un diccionario para transmisión por red."""
        return {
            "id": self.indice,
            "nombre": self.nombre,
            "clave_personaje": self.clave_personaje,
            "x": self.posicion_x,
            "y": self.posicion_y,
            "vidas": self.vidas,
            "vivo": self.vivo,
            "color": list(self.color),
            "acento": list(self.acento),
            "bombas_maximas": self.bombas_maximas,
            "potencia_fuego": self.potencia_fuego,
            "velocidad": self.velocidad,
            "puntaje": self.puntaje,
            "invuln_timer": self.temporizador_invulnerabilidad,
            "shield_timer": self.temporizador_escudo
        }

    @classmethod
    def desde_diccionario(cls, datos):
        """Crea o actualiza una instancia a partir de un diccionario."""
        jugador = cls(datos.get("id", 0), datos.get("clave_personaje", "bomberman"), datos.get("nombre", "Jugador"))
        jugador.posicion_x = datos.get("x", jugador.posicion_x)
        jugador.posicion_y = datos.get("y", jugador.posicion_y)
        jugador.vidas = datos.get("vidas", jugador.vidas)
        jugador.vivo = datos.get("vivo", jugador.vivo)
        jugador.bombas_maximas = datos.get("bombas_maximas", jugador.bombas_maximas)
        jugador.potencia_fuego = datos.get("potencia_fuego", jugador.potencia_fuego)
        jugador.velocidad = datos.get("velocidad", jugador.velocidad)
        jugador.puntaje = datos.get("puntaje", jugador.puntaje)
        jugador.temporizador_invulnerabilidad = datos.get("invuln_timer", 0)
        jugador.temporizador_escudo = datos.get("shield_timer", 0)
        return jugador
