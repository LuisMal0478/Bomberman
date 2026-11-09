"""
Cliente de Red Multijugador (ClienteRed).
Se conecta al servidor mediante socket TCP, transmite comandos del jugador local y renderiza el estado recibido.
"""

import pygame
import socket
import threading
import time

from configuracion import (ANCHO_JUEGO, ALTO_JUEGO, FPS, DORADO,
                           NEON_AZUL, GRIS, BLANCO)
from vistas.administrador_sonidos import AdministradorSonidos
from vistas.vista_juego import VistaJuego
from red.protocolo import (codificar_mensaje, decodificar_linea,
                           crear_mensaje_unirse, crear_mensaje_mover,
                           crear_mensaje_bomba, crear_mensaje_listo,
                           TIPO_CONEXION_OK, TIPO_ESTADO, TIPO_INICIO)


class ClienteRed:
    def __init__(self, host, puerto, nombre_jugador, clave_personaje, pantalla=None, reloj=None):
        self.host = host
        self.puerto = puerto
        self.nombre_jugador = nombre_jugador
        self.clave_personaje = clave_personaje

        self.pantalla = pantalla or pygame.display.set_mode((ANCHO_JUEGO, ALTO_JUEGO))
        self.reloj = reloj or pygame.time.Clock()

        info_pantalla = pygame.display.Info()
        self.ancho_pantalla = info_pantalla.current_w
        self.alto_pantalla = info_pantalla.current_h
        self.superficie_juego = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO))
        self.desfasaje_x = (self.ancho_pantalla - ANCHO_JUEGO) // 2
        self.desfasaje_y = (self.alto_pantalla - ALTO_JUEGO) // 2

        self.vista = VistaJuego(self.pantalla, self.superficie_juego, self.desfasaje_x, self.desfasaje_y)
        self.sonido = AdministradorSonidos()

        self.socket_cliente = None
        self.conectado = False
        self.mi_id = None
        self.estado_remoto = {}
        self.bloqueo_estado = threading.Lock()
        self.bufer_recepcion = b""
        self.fotograma = 0.0

    def conectar(self):
        """Intenta establecer conexión socket con el servidor."""
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.settimeout(3.0)
            self.socket_cliente.connect((self.host, self.puerto))
            self.conectado = True
            self.socket_cliente.settimeout(None)

            msg_unirse = codificar_mensaje(crear_mensaje_unirse(self.nombre_jugador, self.clave_personaje))
            self.socket_cliente.send(msg_unirse)

            self.hilo_recepcion = threading.Thread(target=self._bucle_recepcion, daemon=True)
            self.hilo_recepcion.start()
            return True
        except Exception as e:
            print(f"[CLIENTE] Error al conectar con el servidor: {e}")
            self.conectado = False
            return False

    def _bucle_recepcion(self):
        """Escucha continuamente mensajes entrantes del servidor."""
        try:
            while self.conectado:
                datos = self.socket_cliente.recv(4096)
                if not datos:
                    break
                self.bufer_recepcion += datos

                while b"\n" in self.bufer_recepcion:
                    linea, self.bufer_recepcion = self.bufer_recepcion.split(b"\n", 1)
                    mensaje = decodificar_linea(linea)
                    if not mensaje:
                        continue

                    tipo_msg = mensaje.get("type")

                    if tipo_msg == TIPO_CONEXION_OK or tipo_msg == "join_ok":
                        self.mi_id = mensaje.get("id")
                        self.enviar_listo()

                    elif tipo_msg == TIPO_ESTADO or tipo_msg == "state":
                        with self.bloqueo_estado:
                            self.estado_remoto = mensaje

                    elif tipo_msg == TIPO_INICIO or tipo_msg == "game_start":
                        with self.bloqueo_estado:
                            self.estado_remoto["game_state"] = "jugando"

        except (ConnectionResetError, OSError):
            pass
        finally:
            self.conectado = False

    def enviar_movimiento(self, dx, dy):
        """Envía el comando de movimiento al servidor."""
        if self.conectado and self.socket_cliente:
            try:
                self.socket_cliente.send(codificar_mensaje(crear_mensaje_mover(dx, dy)))
            except Exception:
                pass

    def enviar_bomba(self):
        """Envía la orden de colocar bomba al servidor."""
        if self.conectado and self.socket_cliente:
            try:
                self.socket_cliente.send(codificar_mensaje(crear_mensaje_bomba()))
            except Exception:
                pass

    def enviar_listo(self):
        """Notifica al servidor que este cliente está listo para empezar."""
        if self.conectado and self.socket_cliente:
            try:
                self.socket_cliente.send(codificar_mensaje(crear_mensaje_listo(True)))
            except Exception:
                pass

    def dibujar_espera(self):
        """Renderiza la pantalla de espera hasta que inicie el juego en red."""
        self.superficie_juego.fill((15, 15, 30))
        puntos = "." * ((int(self.fotograma * 2) % 3) + 1)
        titulo = self.vista.fuente_grande.render(f"Conectado a la partida{puntos}", True, DORADO)
        self.superficie_juego.blit(titulo, titulo.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 - 40)))

        sub = self.vista.fuente_media.render("Esperando inicio de la ronda...", True, NEON_AZUL)
        self.superficie_juego.blit(sub, sub.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 + 20)))

        ctrl = self.vista.fuente_pequetia.render("ESC = Volver al Menú Principal", True, GRIS)
        self.superficie_juego.blit(ctrl, ctrl.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO - 30)))

    def ejecutar(self):
        """Bucle principal de renderizado e interacción del cliente."""
        pygame.display.set_mode((self.ancho_pantalla, self.alto_pantalla), pygame.FULLSCREEN)
        pygame.display.set_caption("Bomberman - Multijugador en Red")

        ejecutando = True
        ultimo_movimiento_ms = 0
        intervalo_movimiento = 16

        while ejecutando and self.conectado:
            dt = self.reloj.tick(FPS) / 1000.0
            self.fotograma += dt * 3.0
            ahora_ms = pygame.time.get_ticks()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        ejecutando = False

                    with self.bloqueo_estado:
                        estado_actual = self.estado_remoto.get("game_state", "esperando")

                    if estado_actual == "esperando" and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.enviar_listo()
                    elif estado_actual in ("jugando", "playing"):
                        if evento.key == pygame.K_SPACE:
                            self.enviar_bomba()
                            self.sonido.reproducir('bomba_colocada')

            with self.bloqueo_estado:
                estado = dict(self.estado_remoto)

            estado_juego = estado.get("game_state", "esperando")

            # Entrada continua de teclado para movimiento suave
            if estado_juego in ("jugando", "playing"):
                teclas = pygame.key.get_pressed()
                if ahora_ms - ultimo_movimiento_ms > intervalo_movimiento:
                    dx, dy = 0, 0
                    if teclas[pygame.K_w] or teclas[pygame.K_UP]:
                        dy = -1
                    elif teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
                        dy = 1
                    elif teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                        dx = -1
                    elif teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                        dx = 1

                    if dx != 0 or dy != 0:
                        self.enviar_movimiento(dx, dy)
                        ultimo_movimiento_ms = ahora_ms

            # Renderizado
            self.superficie_juego.fill((0, 0, 0))

            if estado_juego == "esperando":
                self.dibujar_espera()
            else:
                self.vista.renderizar_mapa(estado.get("grid", []))
                self.vista.renderizar_puerta(estado, self.fotograma)
                self.vista.renderizar_bombas(estado.get("bombs", []), self.fotograma)
                self.vista.renderizar_explosiones(estado.get("explosions", []))
                self.vista.renderizar_enemigos(estado.get("enemies", []), self.fotograma, estado.get("grid", []))
                self.vista.renderizar_mejoras(estado.get("powerups", []), self.fotograma)
                jugadores_dict = list(estado.get("players", {}).values())
                self.vista.renderizar_jugadores(jugadores_dict, self.fotograma, self.mi_id)
                self.vista.renderizar_hud(estado)
                self.vista.renderizar_notificaciones(estado)

                if estado_juego == "game_over":
                    self.vista.renderizar_game_over(estado.get("score", 0), estado.get("level", 1))
                elif estado_juego == "victoria":
                    self.vista.renderizar_victoria(estado.get("score", 0))

            self.vista.actualizar_pantalla()

        if self.socket_cliente:
            try:
                self.socket_cliente.close()
            except Exception:
                pass
        self.conectado = False
        return "menu"
