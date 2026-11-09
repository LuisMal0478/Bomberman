"""
Controlador del Juego (ControladorJuego).
Gestiona el bucle principal de juego, procesamiento de entradas del teclado y llamadas a la Vista y Modelo.
"""

import pygame
from configuracion import (ANCHO_JUEGO, ALTO_JUEGO, FPS)
from modelos.modelo_juego import ModeloJuego
from vistas.vista_juego import VistaJuego
from vistas.administrador_sonidos import AdministradorSonidos


class ControladorJuego:
    def __init__(self, modo="single", claves_personajes=None, pantalla=None, reloj=None):
        self.modo = modo
        self.claves_personajes = claves_personajes or ["bomberman"]

        # Inicialización del entorno gráfico
        if pantalla is None:
            pygame.init()
            info = pygame.display.Info()
            self.ancho_pantalla = info.current_w
            self.alto_pantalla = info.current_h
            self.pantalla = pygame.display.set_mode((self.ancho_pantalla, self.alto_pantalla), pygame.FULLSCREEN)
        else:
            self.pantalla = pantalla
            info = pygame.display.Info()
            self.ancho_pantalla = info.current_w
            self.alto_pantalla = info.current_h

        self.reloj = reloj or pygame.time.Clock()
        self.superficie_juego = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO))
        self.desfasaje_x = (self.ancho_pantalla - ANCHO_JUEGO) // 2
        self.desfasaje_y = (self.alto_pantalla - ALTO_JUEGO) // 2

        # Instanciar Modelo, Vista y Sonidos
        self.modelo = ModeloJuego(self.modo, self.claves_personajes)
        self.vista = VistaJuego(self.pantalla, self.superficie_juego, self.desfasaje_x, self.desfasaje_y)
        self.sonido = AdministradorSonidos()

        self.fotograma = 0.0

    def procesar_entrada_teclado(self):
        """Procesa la entrada continua del teclado para movimiento suave."""
        teclas = pygame.key.get_pressed()

        # Jugador 1 (Controles WASD o Flechas en modo individual)
        if len(self.modelo.jugadores) >= 1:
            p1 = self.modelo.jugadores[0]
            if p1.vivo:
                dx, dy = 0, 0
                if teclas[pygame.K_w] or (self.modo == "single" and teclas[pygame.K_UP]):
                    dy = -1
                elif teclas[pygame.K_s] or (self.modo == "single" and teclas[pygame.K_DOWN]):
                    dy = 1
                elif teclas[pygame.K_a] or (self.modo == "single" and teclas[pygame.K_LEFT]):
                    dx = -1
                elif teclas[pygame.K_d] or (self.modo == "single" and teclas[pygame.K_RIGHT]):
                    dx = 1

                if dx != 0 or dy != 0:
                    otros = [j for j in self.modelo.jugadores if j is not p1]
                    p1.mover(dx, dy, self.modelo.matriz_mapa, self.modelo.enemigos, otros, self.modelo.bombas)

        # Jugador 2 (Modo Local Multijugador - Controles Flechas)
        if len(self.modelo.jugadores) >= 2 and self.modo == "local":
            p2 = self.modelo.jugadores[1]
            if p2.vivo:
                dx, dy = 0, 0
                if teclas[pygame.K_UP]:
                    dy = -1
                elif teclas[pygame.K_DOWN]:
                    dy = 1
                elif teclas[pygame.K_LEFT]:
                    dx = -1
                elif teclas[pygame.K_RIGHT]:
                    dx = 1

                if dx != 0 or dy != 0:
                    otros = [j for j in self.modelo.jugadores if j is not p2]
                    p2.mover(dx, dy, self.modelo.matriz_mapa, self.modelo.enemigos, otros, self.modelo.bombas)

    def ejecutar(self):
        """Ejecuta el bucle principal de la partida."""
        pygame.display.set_caption("Bomberman - En Partida")
        ejecutando = True

        while ejecutando:
            dt = self.reloj.tick(FPS) / 1000.0
            self.fotograma += dt * 3.0

            # Procesamiento de eventos discretos
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        return self.modelo.puntaje

                    # Acciones en estado de juego normal
                    if self.modelo.estado_juego == "jugando":
                        if len(self.modelo.jugadores) >= 1:
                            p1 = self.modelo.jugadores[0]
                            if evento.key in (pygame.K_SPACE, pygame.K_RETURN if self.modo == "single" else None):
                                self.modelo.colocar_bomba(p1)

                        if self.modo == "local" and len(self.modelo.jugadores) >= 2:
                            p2 = self.modelo.jugadores[1]
                            if evento.key == pygame.K_RETURN:
                                self.modelo.colocar_bomba(p2)

                    # Navegación en menú de subida de nivel
                    elif self.modelo.estado_juego == "subir_nivel":
                        if not self.modelo.opciones_mejora_nivel:
                            self.modelo.estado_juego = "jugando"
                        elif evento.key == pygame.K_LEFT:
                            self.modelo.opcion_mejora_seleccionada = (self.modelo.opcion_mejora_seleccionada - 1) % len(self.modelo.opciones_mejora_nivel)
                            self.sonido.reproducir('menu_hover')
                        elif evento.key == pygame.K_RIGHT:
                            self.modelo.opcion_mejora_seleccionada = (self.modelo.opcion_mejora_seleccionada + 1) % len(self.modelo.opciones_mejora_nivel)
                            self.sonido.reproducir('menu_hover')
                        elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.modelo.aplicar_mejora_seleccionada()
                            self.sonido.reproducir('menu_seleccion')
                        elif evento.key == pygame.K_ESCAPE:
                            self.modelo.estado_juego = "jugando"

            # Actualizar lógica y movimiento
            if self.modelo.estado_juego == "jugando":
                self.procesar_entrada_teclado()

            self.modelo.actualizar()

            # Reproducir efectos de sonido generados en el modelo
            eventos_sonido = self.modelo.consumir_eventos_sonido()
            for evento_s in eventos_sonido:
                self.sonido.reproducir(evento_s)

            # Renderizar escena actual
            self.superficie_juego.fill((0, 0, 0))
            self.vista.renderizar_mapa(self.modelo.matriz_mapa)
            self.vista.renderizar_puerta(self.modelo, self.fotograma)
            self.vista.renderizar_bombas(self.modelo.bombas, self.fotograma)
            self.vista.renderizar_explosiones(self.modelo.explosions)
            self.vista.renderizar_enemigos(self.modelo.enemigos, self.fotograma, self.modelo.matriz_mapa)
            self.vista.renderizar_mejoras(self.modelo.mejoras, self.fotograma)
            self.vista.renderizar_jugadores(self.modelo.jugadores, self.fotograma)
            self.vista.renderizar_hud(self.modelo)
            self.vista.renderizar_notificaciones(self.modelo)

            if self.modelo.estado_juego == "subir_nivel":
                self.vista.renderizar_menu_subir_nivel(self.modelo.opciones_mejora_nivel, self.modelo.opcion_mejora_seleccionada)
            elif self.modelo.estado_juego == "game_over":
                self.vista.renderizar_game_over(self.modelo.puntaje, self.modelo.nivel)
            elif self.modelo.estado_juego == "victoria":
                self.vista.renderizar_victoria(self.modelo.puntaje)

            self.vista.actualizar_pantalla()

        return self.modelo.puntaje
