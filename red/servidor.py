"""
Servidor Multijugador (ServidorJuego).
Escucha conexiones socket de clientes, procesa sus acciones y sincroniza el estado de la partida.
"""

import sys
import os
import socket
import threading
import time

# Agregar directorio principal al path para importaciones directas si es invocado como script separado
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Headless safe
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from configuracion import PERSONAJES
from modelos.modelo_juego import ModeloJuego
from red.protocolo import (codificar_mensaje, decodificar_linea,
                           TIPO_UNIRSE, TIPO_MOVER, TIPO_BOMBA,
                           TIPO_LISTO, TIPO_CONEXION_OK, TIPO_ESTADO,
                           TIPO_INICIO, TIPO_JUGADOR_UNIDO, TIPO_JUGADOR_SALIDO)


class ServidorJuego:
    def __init__(self, host="0.0.0.0", puerto=5555):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        self.clientes = {}  # {id_jugador: (socket_cliente, direccion)}
        self.bloqueo = threading.Lock()
        self.ejecutando = False
        self.modelo = ModeloJuego(modo="network")
        self.contador_id_jugadores = 0

    def iniciar(self):
        """Inicia el socket servidor y lanza los hilos de red y bucle de juego."""
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.host, self.puerto))
        self.socket_servidor.listen(5)
        self.ejecutando = True

        print(f"[SERVIDOR] Escuchando en {self.host}:{self.puerto}")

        hilo_aceptar = threading.Thread(target=self._aceptar_conexiones, daemon=True)
        hilo_aceptar.start()

        hilo_bucle_juego = threading.Thread(target=self._bucle_principal_juego, daemon=True)
        hilo_bucle_juego.start()

        try:
            while self.ejecutando:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[SERVIDOR] Deteniendo servidor...")
            self.ejecutando = False
            if self.socket_servidor:
                self.socket_servidor.close()

    def _aceptar_conexiones(self):
        """Hilo dedicado a aceptar nuevas conexiones entrantes."""
        while self.ejecutando:
            try:
                self.socket_servidor.settimeout(1.0)
                socket_cliente, direccion = self.socket_servidor.accept()
                print(f"[SERVIDOR] Nueva conexión desde {direccion}")

                hilo_cliente = threading.Thread(
                    target=self._atender_cliente, args=(socket_cliente, direccion), daemon=True
                )
                hilo_cliente.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _atender_cliente(self, socket_cliente, direccion):
        """Atiende la comunicación socket entrante de un cliente específico."""
        id_jugador = None
        bufer = b""
        try:
            while self.ejecutando:
                datos = socket_cliente.recv(4096)
                if not datos:
                    break
                bufer += datos

                while b"\n" in bufer:
                    linea, bufer = bufer.split(b"\n", 1)
                    mensaje = decodificar_linea(linea)
                    if not mensaje:
                        continue

                    tipo_msg = mensaje.get("type")

                    if tipo_msg == TIPO_UNIRSE or tipo_msg == "join":
                        with self.bloqueo:
                            id_jugador = self.contador_id_jugadores
                            self.contador_id_jugadores += 1

                            nombre = mensaje.get("name", f"P{id_jugador + 1}")
                            clave_personaje = mensaje.get("char", "bomberman")

                            # Si ya había jugadores o se reinicia
                            if len(self.modelo.jugadores) <= id_jugador:
                                from modelos.jugador import Jugador
                                p = Jugador(id_jugador, clave_personaje, nombre)
                                self.modelo.jugadores.append(p)

                            self.clientes[id_jugador] = (socket_cliente, direccion)

                        # Responder confirmación al cliente
                        msg_ok = codificar_mensaje({"type": TIPO_CONEXION_OK, "id": id_jugador})
                        socket_cliente.send(msg_ok)

                        self._notificar_jugador_unido(id_jugador, nombre, clave_personaje)
                        print(f"[SERVIDOR] Jugador '{nombre}' registrado con ID:{id_jugador}")

                        if self.modelo.estado_juego == "jugando":
                            self._enviar_estado_individual(socket_cliente)

                    elif tipo_msg == TIPO_MOVER or tipo_msg == "move":
                        if id_jugador is not None:
                            dx = mensaje.get("dx", 0)
                            dy = mensaje.get("dy", 0)
                            with self.bloqueo:
                                for p in self.modelo.jugadores:
                                    if p.indice == id_jugador and p.vivo:
                                        otros = [j for j in self.modelo.jugadores if j.indice != id_jugador]
                                        p.mover(dx, dy, self.modelo.matriz_mapa, self.modelo.enemigos, otros)
                                        break

                    elif tipo_msg == TIPO_BOMBA or tipo_msg == "bomb":
                        if id_jugador is not None:
                            with self.bloqueo:
                                for p in self.modelo.jugadores:
                                    if p.indice == id_jugador and p.vivo:
                                        self.modelo.colocar_bomba(p)
                                        break

                    elif tipo_msg == TIPO_LISTO or tipo_msg == "ready":
                        with self.bloqueo:
                            if self.modelo.estado_juego in ("jugando", "esperando"):
                                self.modelo.iniciar_nivel()
                                self.modelo.estado_juego = "jugando"
                                msg_inicio = codificar_mensaje({"type": TIPO_INICIO})
                                self._transmitir_a_todos(msg_inicio)

        except (ConnectionResetError, OSError, BrokenPipeError):
            pass
        finally:
            with self.bloqueo:
                if id_jugador is not None:
                    if id_jugador in self.clientes:
                        del self.clientes[id_jugador]
                    self.modelo.jugadores = [j for j in self.modelo.jugadores if j.indice != id_jugador]

            self._notificar_jugador_salido(id_jugador)
            try:
                socket_cliente.close()
            except Exception:
                pass
            print(f"[SERVIDOR] Cliente {direccion} desconectado (ID:{id_jugador})")

    def _transmitir_a_todos(self, datos_bytes):
        """Envía un paquete codificado a todos los clientes conectados."""
        for socket_c, _ in list(self.clientes.values()):
            try:
                socket_c.send(datos_bytes)
            except Exception:
                pass

    def _notificar_jugador_unido(self, id_jugador, nombre, clave_personaje):
        msg = codificar_mensaje({
            "type": TIPO_JUGADOR_UNIDO,
            "id": id_jugador,
            "name": nombre,
            "char": clave_personaje
        })
        self._transmitir_a_todos(msg)

    def _notificar_jugador_salido(self, id_jugador):
        msg = codificar_mensaje({"type": TIPO_JUGADOR_SALIDO, "id": id_jugador})
        self._transmitir_a_todos(msg)

    def _enviar_estado_individual(self, socket_cliente):
        datos_estado = self.modelo.a_diccionario()
        msg = codificar_mensaje({"type": TIPO_ESTADO, **datos_estado})
        try:
            socket_cliente.send(msg)
        except Exception:
            pass

    def _transmitir_estado_general(self):
        datos_estado = self.modelo.a_diccionario()
        msg = codificar_mensaje({"type": TIPO_ESTADO, **datos_estado})
        self._transmitir_a_todos(msg)

    def _bucle_principal_juego(self):
        """Bucle continuo de física del modelo a 30 fotogramas por segundo."""
        while self.ejecutando:
            time.sleep(1.0 / 30.0)
            with self.bloqueo:
                if self.clientes and self.modelo.estado_juego == "jugando":
                    self.modelo.actualizar()
                    self._transmitir_estado_general()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Servidor Bomberman Red")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Host IP")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5555")), help="Puerto")
    args = parser.parse_args()

    servidor = ServidorJuego(host=args.host, puerto=args.port)
    servidor.iniciar()
