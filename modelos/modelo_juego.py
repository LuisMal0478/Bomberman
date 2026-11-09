"""
Modelo Principal del Juego (ModeloJuego).
Centraliza todo el estado del juego, colisiones, explosiones y lógica de la partida.
"""

import math
import random
from configuracion import (ANCHO_CASILLA, COLUMNAS, FILAS, ALTO_HUD,
                           CASILLA_VACIA, CASILLA_PARED, CASILLA_BLOQUE,
                           NIVEL_MAXIMO)
from modelos.jugador import Jugador
from modelos.bomba import Bomba, Explosion
from modelos.enemigo import Enemigo
from modelos.mejora import Mejora
from modelos.mapa import Mapa


class ModeloJuego:
    def __init__(self, modo="single", claves_personajes=None):
        self.modo = modo
        self.claves_personajes = claves_personajes or ["bomberman"]
        self.nivel = 1
        self.puntaje = 0
        self.estado_juego = "jugando"  # "jugando", "transicion_nivel", "game_over", "victoria", "subir_nivel"
        self.matriz_mapa = []
        self.jugadores = []
        self.enemigos = []
        self.bombas = []
        self.explosions = []
        self.mejoras = []
        self.eventos_sonido = []
        self.temporizador_transicion = 0
        self.fotograma = 0
        self.opciones_mejora_nivel = []
        self.opcion_mejora_seleccionada = 0

        # Mecánica de puerta secreta bajo los ladrillos
        self.posicion_puerta = (0, 0)
        self.puerta_revelada = False
        self.puerta_abierta = False
        self.notificacion_puerta = ""
        self.temporizador_notificacion = 0
        self.sonido_puerta_reproducido = False

        self.inicializar_jugadores()
        self.iniciar_nivel()

    def inicializar_jugadores(self):
        """Crea las instancias iniciales de jugadores."""
        self.jugadores.clear()
        for i, clave in enumerate(self.claves_personajes):
            nombre = f"P{i+1}" if len(self.claves_personajes) > 1 else "Jugador"
            self.jugadores.append(Jugador(i, clave, nombre))

    def iniciar_nivel(self):
        """Genera el nivel actual, reseteando bombas, explosiones y enemigos."""
        self.bombas.clear()
        self.explosions.clear()
        self.mejoras.clear()

        # Resetear posiciones de los jugadores a sus esquinas de spawn
        posiciones_spawn = [
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            (ANCHO_CASILLA + ANCHO_CASILLA // 2, (FILAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
            ((COLUMNAS - 2) * ANCHO_CASILLA + ANCHO_CASILLA // 2, ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD),
        ]
        for i, j in enumerate(self.jugadores):
            sx, sy = posiciones_spawn[i % len(posiciones_spawn)]
            j.posicion_x = float(sx)
            j.posicion_y = float(sy)
            j.posicion_objetivo_x = float(sx)
            j.posicion_objetivo_y = float(sy)
            j.bombas_activas = 0
            j.temporizador_invulnerabilidad = 60

        posiciones_jugadores = [(j.posicion_x, j.posicion_y) for j in self.jugadores]
        self.matriz_mapa = Mapa.generar_matriz(self.nivel, posiciones_jugadores)
        self.enemigos = Mapa.generar_enemigos(self.nivel, self.matriz_mapa, posiciones_jugadores)

        # Ocultar la puerta bajo un bloque de ladrillos
        bloques = [(r, c) for r in range(FILAS) for c in range(COLUMNAS) if self.matriz_mapa[r][c] == CASILLA_BLOQUE]
        if bloques:
            self.posicion_puerta = random.choice(bloques)
        else:
            self.posicion_puerta = (FILAS // 2, COLUMNAS // 2)

        self.puerta_revelada = False
        self.puerta_abierta = False
        self.sonido_puerta_reproducido = False

        if self.nivel == 1:
            self.notificacion_puerta = "¡NIVEL 1! Destruye ladrillos para hallar la puerta de salida."
        elif self.nivel == 3:
            self.notificacion_puerta = "¡CUIDADO! Aparecen enemigos que traspasan ladrillos."
        elif self.nivel >= 5:
            self.notificacion_puerta = f"¡NIVEL {self.nivel}! Máxima dificultad. ¡Halla la salida!"
        else:
            self.notificacion_puerta = f"¡NIVEL {self.nivel}! Encuentra la puerta secreta."
        self.temporizador_notificacion = 200

    def consumir_eventos_sonido(self):
        """Devuelve los eventos de sonido acumulados y limpia la lista."""
        eventos = list(self.eventos_sonido)
        self.eventos_sonido.clear()
        return eventos

    def colocar_bomba(self, jugador):
        """Permite a un jugador colocar una bomba en su posición actual."""
        if not jugador or not jugador.vivo:
            return False
        if jugador.bombas_activas >= jugador.bombas_maximas:
            return False

        casilla_x = int(jugador.posicion_x) // ANCHO_CASILLA * ANCHO_CASILLA + ANCHO_CASILLA // 2
        casilla_y = int(jugador.posicion_y - ALTO_HUD) // ANCHO_CASILLA * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD

        # Evitar colocar sobre una bomba existente
        for b in self.bombas:
            if b.posicion_x == casilla_x and b.posicion_y == casilla_y:
                return False

        self.bombas.append(Bomba(casilla_x, casilla_y, jugador.potencia_fuego, jugador))
        jugador.bombas_activas += 1
        self.eventos_sonido.append('bomba_colocada')
        return True

    def explotar_bomba(self, bomba):
        """Genera la explosión de una bomba, destruye bloques y activa power-ups."""
        if bomba.propietario:
            bomba.propietario.bombas_activas = max(0, bomba.propietario.bombas_activas - 1)

        casilla_bomba_x = int(bomba.posicion_x) // ANCHO_CASILLA
        casilla_bomba_y = int(bomba.posicion_y - ALTO_HUD) // ANCHO_CASILLA

        casillas_afectadas = [(casilla_bomba_x, casilla_bomba_y)]
        if 0 <= casilla_bomba_x < COLUMNAS and 0 <= casilla_bomba_y < FILAS and self.matriz_mapa[casilla_bomba_y][casilla_bomba_x] == CASILLA_BLOQUE:
            self.matriz_mapa[casilla_bomba_y][casilla_bomba_x] = CASILLA_VACIA
            if (casilla_bomba_y, casilla_bomba_x) == self.posicion_puerta:
                self.puerta_revelada = True
                self.eventos_sonido.append('mejora')
                if len(self.enemigos) == 0:
                    self.notificacion_puerta = "¡PUERTA ENCONTRADA Y ABIERTA! ¡ENTRA PARA AVANZAR!"
                else:
                    self.notificacion_puerta = f"¡PUERTA ENCONTRADA! Elimina a los {len(self.enemigos)} enemigos para abrirla."
                self.temporizador_notificacion = 180

        # Expansión en 4 direcciones
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for i in range(1, bomba.potencia + 1):
                nx, ny = casilla_bomba_x + dx * i, casilla_bomba_y + dy * i
                if 0 <= nx < COLUMNAS and 0 <= ny < FILAS:
                    if self.matriz_mapa[ny][nx] == CASILLA_PARED:
                        break
                    casillas_afectadas.append((nx, ny))
                    if self.matriz_mapa[ny][nx] == CASILLA_BLOQUE:
                        self.matriz_mapa[ny][nx] = CASILLA_VACIA
                        # Verificar si se reveló la puerta secreta
                        if (ny, nx) == self.posicion_puerta:
                            self.puerta_revelada = True
                            self.eventos_sonido.append('mejora')
                            if len(self.enemigos) == 0:
                                self.notificacion_puerta = "¡PUERTA ENCONTRADA Y ABIERTA! ¡ENTRA PARA AVANZAR!"
                            else:
                                self.notificacion_puerta = f"¡PUERTA ENCONTRADA! Elimina a los {len(self.enemigos)} enemigos para abrirla."
                            self.temporizador_notificacion = 180
                        elif random.random() < 0.25:
                            pos_x = nx * ANCHO_CASILLA + ANCHO_CASILLA // 2
                            pos_y = ny * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
                            self.mejoras.append(Mejora(pos_x, pos_y))
                        break
                else:
                    break

        for cx, cy in casillas_afectadas:
            pos_x = cx * ANCHO_CASILLA + ANCHO_CASILLA // 2
            pos_y = cy * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
            self.explosions.append(Explosion(pos_x, pos_y))

        self.eventos_sonido.append('explosion')

    def actualizar_bombas(self):
        """Actualiza el estado de las bombas activas."""
        nuevas_bombas = []
        for b in self.bombas:
            if b.actualizar():
                self.explotar_bomba(b)
            else:
                nuevas_bombas.append(b)
        self.bombas = nuevas_bombas

    def actualizar_explosiones(self):
        """Actualiza la duración de las explosiones."""
        self.explosions = [exp for exp in self.explosions if exp.actualizar()]

    def actualizar_enemigos(self):
        """Actualiza la IA y movimiento de todos los enemigos."""
        for e in self.enemigos:
            e.actualizar(self.matriz_mapa, self.enemigos, self.jugadores, self.bombas)

    def verificar_colisiones(self):
        """Verifica interacciones entre explosiones, jugadores y enemigos."""
        # Colisiones de jugadores
        for p in self.jugadores:
            if not p.vivo:
                continue

            p.actualizar()

            # Jugador vs Enemigo
            for e in self.enemigos:
                if abs(p.posicion_x - e.posicion_x) < ANCHO_CASILLA * 0.6 and abs(p.posicion_y - e.posicion_y) < ANCHO_CASILLA * 0.6:
                    if p.recibir_danio():
                        self.eventos_sonido.append('dano' if p.vivo else 'muerte')

            # Jugador vs Explosión
            for exp in self.explosions:
                if abs(p.posicion_x - exp.posicion_x) < ANCHO_CASILLA * 0.6 and abs(p.posicion_y - exp.posicion_y) < ANCHO_CASILLA * 0.6:
                    if p.recibir_danio():
                        self.eventos_sonido.append('dano' if p.vivo else 'muerte')

        # Enemigo vs Explosión
        for e in self.enemigos[:]:
            for exp in self.explosions:
                if abs(e.posicion_x - exp.posicion_x) < ANCHO_CASILLA * 0.6 and abs(e.posicion_y - exp.posicion_y) < ANCHO_CASILLA * 0.6:
                    if e.recibir_danio():
                        if e in self.enemigos:
                            self.enemigos.remove(e)
                        self.puntaje += e.puntos
                        for p in self.jugadores:
                            if p.vivo:
                                p.puntaje += e.puntos

                        # Si es modo un solo jugador y muere un enemigo, abrir menú de mejora opcional
                        if self.modo == "single" and self.jugadores and self.jugadores[0].vivo:
                            self.generar_opciones_mejora()
                            self.estado_juego = "subir_nivel"
                        break

    def verificar_mejoras(self):
        """Verifica la recolección de power-ups por parte de los jugadores."""
        for p in self.jugadores:
            if not p.vivo:
                continue
            for mej in self.mejoras[:]:
                if abs(p.posicion_x - mej.posicion_x) < ANCHO_CASILLA * 0.6 and abs(p.posicion_y - mej.posicion_y) < ANCHO_CASILLA * 0.6:
                    p.recibir_mejora(mej.tipo_mejora)
                    self.mejoras.remove(mej)
                    self.eventos_sonido.append('mejora')

    def generar_opciones_mejora(self):
        """Genera opciones para el menú de subir de nivel."""
        if not self.jugadores:
            return
        p = self.jugadores[0]
        opciones = []
        if p.bombas_maximas < 8:
            opciones.append(("mas_bomba", "+1 Bomba", (255, 140, 0)))
        if p.potencia_fuego < 8:
            opciones.append(("mas_fuego", "+1 Fuego", (255, 69, 0)))
        if p.velocidad < 6.0:
            opciones.append(("mas_velocidad", "+1 Velocidad", (0, 200, 200)))
        if p.vidas < 5:
            opciones.append(("mas_vida", "+1 Vida", (46, 213, 115)))
        if not opciones:
            opciones.append(("escudo", "Escudo 5s", (100, 200, 255)))
            opciones.append(("mas_vida", "+1000 Puntos", (255, 215, 0)))
        random.shuffle(opciones)
        self.opciones_mejora_nivel = opciones[:3]
        self.opcion_mejora_seleccionada = 0

    def aplicar_mejora_seleccionada(self):
        """Aplica la mejora elegida en el menú desplegable."""
        if not self.opciones_mejora_nivel or not self.jugadores:
            self.estado_juego = "jugando"
            return
        tipo, _, _ = self.opciones_mejora_nivel[self.opcion_mejora_seleccionada]
        self.jugadores[0].recibir_mejora(tipo)
        self.estado_juego = "jugando"

    def actualizar(self):
        """Ciclo principal de actualización del modelo."""
        if self.estado_juego == "subir_nivel":
            return

        if self.estado_juego == "transicion_nivel":
            self.temporizador_transicion += 1
            if self.temporizador_transicion > 120:
                self.nivel += 1
                if self.nivel > NIVEL_MAXIMO:
                    self.estado_juego = "victoria"
                    self.eventos_sonido.append('victoria')
                    return
                self.puntaje += self.nivel * 1000
                self.iniciar_nivel()
                self.estado_juego = "jugando"
                self.temporizador_transicion = 0
            return

        if self.estado_juego in ("game_over", "victoria"):
            return

        self.fotograma += 1
        self.actualizar_bombas()
        self.actualizar_explosiones()
        self.actualizar_enemigos()
        self.verificar_colisiones()
        self.verificar_mejoras()

        if self.temporizador_notificacion > 0:
            self.temporizador_notificacion -= 1

        todos_muertos = all(not p.vivo for p in self.jugadores)
        if todos_muertos:
            self.estado_juego = "game_over"
            self.eventos_sonido.append('muerte')
        else:
            # Abrir la puerta si todos los enemigos fueron derrotados
            if len(self.enemigos) == 0 and not self.puerta_abierta:
                self.puerta_abierta = True
                if not self.sonido_puerta_reproducido:
                    self.sonido_puerta_reproducido = True
                    self.eventos_sonido.append('mejora')
                    if self.puerta_revelada:
                        self.notificacion_puerta = "¡ENEMIGOS ELIMINADOS! ¡LA PUERTA ESTÁ ABIERTA! ¡ENTRA!"
                    else:
                        self.notificacion_puerta = "¡ENEMIGOS ELIMINADOS! ¡HALLA LA PUERTA BAJO LOS LADRILLOS!"
                    self.temporizador_notificacion = 220

            # Comprobar si un jugador pisa la puerta revelada
            if self.puerta_revelada and self.matriz_mapa[self.posicion_puerta[0]][self.posicion_puerta[1]] != CASILLA_BLOQUE:
                dr, dc = self.posicion_puerta
                door_x = dc * ANCHO_CASILLA + ANCHO_CASILLA // 2
                door_y = dr * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
                for p in self.jugadores:
                    if p.vivo:
                        if math.hypot(p.posicion_x - door_x, p.posicion_y - door_y) < ANCHO_CASILLA * 0.55:
                            if self.puerta_abierta:
                                self.estado_juego = "transicion_nivel"
                                self.temporizador_transicion = 0
                                self.eventos_sonido.append('nivel_completado')
                                self.puntaje += self.nivel * 1000
                                for pl in self.jugadores:
                                    pl.puntaje += self.nivel * 1000
                                break
                            else:
                                if self.temporizador_notificacion <= 0:
                                    self.notificacion_puerta = f"¡PUERTA CERRADA! Elimina a los {len(self.enemigos)} enemigos restantes"
                                    self.temporizador_notificacion = 90

    def a_diccionario(self):
        """Serializa el estado del modelo a diccionario para el servidor multijugador."""
        return {
            "game_state": self.estado_juego,
            "level": self.nivel,
            "score": self.puntaje,
            "grid": self.matriz_mapa,
            "players": {str(p.indice): p.a_diccionario() for p in self.jugadores},
            "enemies": [e.a_diccionario() for e in self.enemigos],
            "bombs": [b.a_diccionario() for b in self.bombas],
            "explosions": [exp.a_diccionario() for exp in self.explosions],
            "powerups": [m.a_diccionario() for m in self.mejoras],
            "door": {
                "cell": list(self.posicion_puerta),
                "revealed": self.puerta_revelada,
                "open": self.puerta_abierta
            },
            "notification": self.notificacion_puerta if self.temporizador_notificacion > 0 else ""
        }
