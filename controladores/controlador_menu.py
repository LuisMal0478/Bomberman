"""
Controlador del Menú Principal (ControladorMenu).
Maneja las transiciones de pantalla, botones, selección de personaje y configuración centreada dinámicamente.
"""

import sys
import os
import math
import random
import socket
import subprocess
import time
import pygame

# Asegurar importación de módulos desde el directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from configuracion import (PERSONAJES, VERDE, NEON_AZUL, GRIS, ROJO)
from vistas.administrador_sonidos import AdministradorSonidos
from vistas.vista_menu import VistaMenu
from vistas.componentes import Boton, CampoTexto, Particula
from controladores.controlador_juego import ControladorJuego


def servidor_esta_ejecutandose(host="127.0.0.1", puerto=5555):
    """Verifica si hay un servidor escuchando en el puerto indicado."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, puerto)) == 0
    except Exception:
        return False


class ControladorMenu:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.ancho = self.pantalla.get_width()
        self.alto = self.pantalla.get_height()
        pygame.display.set_caption("Bomberman Multijugador - Menú Principal")

        self.reloj = pygame.time.Clock()
        self.estado = "principal"  # "principal", "seleccion_personaje", "multijugador", "unirse", "configuracion"
        self.vista = VistaMenu(self.pantalla, self.ancho, self.alto)
        self.sonido = AdministradorSonidos()

        self.particulas = []
        self.fotograma = 0.0
        self.personaje_seleccionado = 0
        self.claves_personajes = list(PERSONAJES.keys())

        self.mejor_puntaje = 0
        self.estado_servidor = ""
        self.proceso_servidor = None

        self._inicializar_botones()

    def _inicializar_botones(self):
        """Calcula proporciones y centra botones perfectamente de acuerdo al alto y ancho real."""
        ancho_b = max(280, min(380, int(self.ancho * 0.3)))
        alto_b = max(45, min(56, int(self.alto * 0.07)))
        cx = self.ancho // 2 - ancho_b // 2
        espaciado_y = alto_b + 12

        # 1. Menú Principal (centrado vertical y horizontal exacto)
        alto_bloque_principal = 4 * alto_b + 3 * 12
        inicio_y_main = (self.alto - alto_bloque_principal) // 2 + 50

        self.btn_un_jugador = Boton(cx, inicio_y_main, ancho_b, alto_b, "MODO UN JUGADOR", VERDE, (40, 180, 100))
        self.btn_multijugador = Boton(cx, inicio_y_main + espaciado_y, ancho_b, alto_b, "MODO MULTIJUGADOR", NEON_AZUL, (0, 160, 200))
        self.btn_configuracion = Boton(cx, inicio_y_main + espaciado_y * 2, ancho_b, alto_b, "CONFIGURACIÓN", GRIS, (120, 120, 140))
        self.btn_salir = Boton(cx, inicio_y_main + espaciado_y * 3, ancho_b, alto_b, "SALIR", ROJO, (200, 50, 60))

        # 2. Menú Multijugador (centrado)
        alto_bloque_mp = 3 * alto_b + 2 * 12
        inicio_y_mp = (self.alto - alto_bloque_mp) // 2 + 20
        self.btn_hostear = Boton(cx, inicio_y_mp, ancho_b, alto_b, "HOSTEAR PARTIDA", VERDE, (40, 180, 100))
        self.btn_conectarse = Boton(cx, inicio_y_mp + espaciado_y, ancho_b, alto_b, "CONECTARSE A IP", NEON_AZUL, (0, 160, 200))
        self.btn_volver_mp = Boton(cx, inicio_y_mp + espaciado_y * 2, ancho_b, alto_b, "VOLVER", GRIS, (120, 120, 140))

        # 3. Formulario Conectar IP (centrado)
        self.entrada_nombre = CampoTexto(cx, int(self.alto * 0.28), ancho_b, alto_b - 10, "Jugador")
        self.entrada_ip = CampoTexto(cx, int(self.alto * 0.44), ancho_b, alto_b - 10, "127.0.0.1")

        inicio_y_join = int(self.alto * 0.62)
        self.btn_conectar_ip = Boton(cx, inicio_y_join, ancho_b, alto_b, "CONECTAR", NEON_AZUL, (0, 160, 200))
        self.btn_volver_unirse = Boton(cx, inicio_y_join + espaciado_y, ancho_b, alto_b, "VOLVER", GRIS, (120, 120, 140))

        # 4. Configuración
        self.btn_sonido = Boton(self.ancho // 2 - 90, int(self.alto * 0.26), 180, 45, "SONIDO: ON", VERDE)
        self.btn_volver_config = Boton(cx, int(self.alto * 0.74), ancho_b, alto_b, "VOLVER", GRIS, (120, 120, 140))

    def generar_particulas(self):
        """Genera partículas flotantes en el fondo."""
        if random.random() < 0.3:
            self.particulas.append(Particula(
                random.randint(0, self.ancho), self.alto + 10,
                random.choice([NEON_AZUL, (255, 215, 0), (255, 100, 150)])
            ))

    def actualizar_particulas(self):
        """Actualiza la física de la lista de partículas."""
        for p in self.particulas:
            p.actualizar()
        self.particulas = [p for p in self.particulas if p.vida > 0]

    def iniciar_servidor_local(self):
        """Inicia el proceso del servidor multijugador en segundo plano."""
        try:
            if servidor_esta_ejecutandose("127.0.0.1", 5555):
                self.estado_servidor = "El servidor ya está en ejecución."
                return True

            self.estado_servidor = "Iniciando servidor..."
            script_servidor = sys.executable
            path_servidor = os.path.join(os.path.dirname(__file__), '..', 'red', 'servidor.py')

            self.proceso_servidor = subprocess.Popen(
                [script_servidor, path_servidor],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            tiempo_limite = 3.0
            transcurrido = 0.0
            while transcurrido < tiempo_limite:
                time.sleep(0.2)
                transcurrido += 0.2
                if servidor_esta_ejecutandose("127.0.0.1", 5555):
                    self.estado_servidor = "¡Servidor iniciado! Conectando..."
                    return True

            self.estado_servidor = "Tiempo de espera agotado para el servidor"
            self.detener_servidor_local()
            return False
        except Exception as e:
            self.estado_servidor = f"Error: {e}"
            return False

    def detener_servidor_local(self):
        """Detiene el proceso del servidor si fue iniciado por el menú."""
        if self.proceso_servidor:
            try:
                self.proceso_servidor.terminate()
            except Exception:
                pass
            self.proceso_servidor = None

    def ejecutar_modo_un_jugador(self):
        """Inicia una partida individual mediante el ControladorJuego."""
        clave = self.claves_personajes[self.personaje_seleccionado]
        controlador = ControladorJuego(modo="single", claves_personajes=[clave], pantalla=self.pantalla, reloj=self.reloj)
        resultado = controlador.ejecutar()

        pygame.display.set_mode((self.ancho, self.alto), pygame.FULLSCREEN)
        pygame.display.set_caption("Bomberman - Menú Principal")

        if resultado > self.mejor_puntaje:
            self.mejor_puntaje = resultado

    def ejecutar_modo_multijugador(self, host, puerto):
        """Conecta con un servidor multijugador e inicia el ClienteRed."""
        for intento in range(5):
            if servidor_esta_ejecutandose(host, puerto):
                break
            time.sleep(0.2)
        else:
            self.estado_servidor = "El servidor no está disponible"
            return "conexion_fallida"

        clave = self.claves_personajes[self.personaje_seleccionado]
        nombre = self.entrada_nombre.texto or "Jugador"

        from red.cliente import ClienteRed
        cliente = ClienteRed(host, puerto, nombre, clave, pantalla=self.pantalla, reloj=self.reloj)
        if not cliente.conectar():
            return "conexion_fallida"

        resultado = cliente.ejecutar()
        pygame.display.set_mode((self.ancho, self.alto), pygame.FULLSCREEN)
        pygame.display.set_caption("Bomberman - Menú Principal")
        return resultado

    def ejecutar(self):
        """Bucle principal de la interfaz de menú."""
        ejecutando = True

        while ejecutando:
            dt = self.reloj.tick(60) / 1000.0
            self.fotograma += dt * 3.0
            posicion_mouse = pygame.mouse.get_pos()

            self.generar_particulas()
            self.actualizar_particulas()

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False

                if self.estado == "principal":
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_un_jugador.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "seleccion_personaje"
                        elif self.btn_multijugador.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "multijugador"
                        elif self.btn_configuracion.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "configuracion"
                        elif self.btn_salir.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            ejecutando = False
                    elif evento.type == pygame.KEYDOWN:
                        if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "seleccion_personaje"

                elif self.estado == "seleccion_personaje":
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_LEFT:
                            self.personaje_seleccionado = (self.personaje_seleccionado - 1) % len(self.claves_personajes)
                            self.sonido.reproducir('menu_hover')
                        elif evento.key == pygame.K_RIGHT:
                            self.personaje_seleccionado = (self.personaje_seleccionado + 1) % len(self.claves_personajes)
                            self.sonido.reproducir('menu_hover')
                        elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.sonido.reproducir('menu_seleccion')
                            self.ejecutar_modo_un_jugador()
                            self.estado = "principal"
                        elif evento.key == pygame.K_ESCAPE:
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "principal"

                elif self.estado == "multijugador":
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_hostear.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            if self.iniciar_servidor_local():
                                self.ejecutar_modo_multijugador("127.0.0.1", 5555)
                                self.estado = "multijugador"
                        elif self.btn_conectarse.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "unirse"
                        elif self.btn_volver_mp.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "principal"

                elif self.estado == "unirse":
                    self.entrada_nombre.manejar_evento(evento)
                    self.entrada_ip.manejar_evento(evento)
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_conectar_ip.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            ip = self.entrada_ip.texto or "127.0.0.1"
                            res = self.ejecutar_modo_multijugador(ip, 5555)
                            if res == "conexion_fallida":
                                self.estado_servidor = f"No se pudo conectar a {ip}"
                            self.estado = "unirse"
                        elif self.btn_volver_unirse.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "multijugador"

                elif self.estado == "configuracion":
                    if evento.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_sonido.es_clicqueado(evento.pos):
                            self.sonido.alternar_sonido()
                            self.sonido.reproducir('menu_seleccion')
                        elif self.btn_volver_config.es_clicqueado(evento.pos):
                            self.sonido.reproducir('menu_seleccion')
                            self.estado = "principal"

            # Renderizar Vista correspondiente
            if self.estado == "principal":
                botones = [self.btn_un_jugador, self.btn_multijugador, self.btn_configuracion, self.btn_salir]
                self.vista.dibujar_menu_principal(botones, posicion_mouse, self.mejor_puntaje, self.particulas)
            elif self.estado == "seleccion_personaje":
                self.vista.dibujar_seleccion_personaje(self.claves_personajes, self.personaje_seleccionado, self.fotograma)
            elif self.estado == "multijugador":
                botones = [self.btn_hostear, self.btn_conectarse, self.btn_volver_mp]
                self.vista.dibujar_menu_multijugador(botones, posicion_mouse, self.particulas)
            elif self.estado == "unirse":
                botones = [self.btn_conectar_ip, self.btn_volver_unirse]
                self.vista.dibujar_pantalla_conexion(self.entrada_nombre, self.entrada_ip, botones, self.estado_servidor, posicion_mouse, self.particulas)
            elif self.estado == "configuracion":
                self.vista.dibujar_configuracion(self.btn_sonido, self.btn_volver_config, self.sonido, posicion_mouse)

            pygame.display.flip()

        self.detener_servidor_local()
        pygame.quit()
        sys.exit()
