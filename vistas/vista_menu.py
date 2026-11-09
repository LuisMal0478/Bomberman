"""
Vista de Menús e Interfaz de Usuario (VistaMenu).
Maneja la selección de personaje, configuración, multijugador y renderizado totalmente adaptativo a cualquier pantalla.
"""

import sys
import os
import math
import pygame

# Asegurar importación de módulos desde el directorio raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from configuracion import (BLANCO, NEGRO, NEON_AZUL, DORADO, ROJO, VERDE,
                           GRIS, GRIS_CLARO, COLOR_FONDO_OSCURO,
                           COLOR_FONDO_OSCURO2, PERSONAJES)
from vistas.componentes import (Boton, CampoTexto, Particula, cargar_imagen,
                                renderizar_texto_ajustado)


class VistaMenu:
    def __init__(self, pantalla, ancho, alto):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto

        self.recalcular_fuentes()

        # Imagen de fondo que cubre el 100% de la pantalla sin barras negras laterales
        self.img_fondo = cargar_imagen("fondo.jpeg", (ancho, alto), preservar_aspecto=False)

        # Logos e ilustraciones con aspecto proporcional preservado
        ancho_logo = min(460, int(ancho * 0.38))
        alto_logo = min(140, int(alto * 0.16))
        ancho_personaje = min(220, int(ancho * 0.20))
        alto_personaje = min(120, int(alto * 0.14))

        self.img_texto = cargar_imagen("texto.png", (ancho_logo, alto_logo), preservar_aspecto=True)
        self.img_play = cargar_imagen("boton_play.png", (200, 60), preservar_aspecto=True)

        # Cargar modelo 3D para el menú principal y avatares
        alto_p_menu = max(130, min(280, int(alto * 0.28)))
        ancho_p_menu = max(60, int(alto_p_menu * (230.0 / 485.0)))
        self.img_personaje = cargar_imagen("personaje_3d_bomberman.png", (ancho_p_menu, alto_p_menu), preservar_aspecto=True)

        self.sprites_3d_tarjetas = {}
        alto_av = max(70, min(130, int(alto * 0.17)))
        ancho_av = max(35, int(alto_av * (230.0 / 485.0)))
        mapeo = {
            "bomberman": "personaje_3d_bomberman.png",
            "fuego": "personaje_3d_fuego.png",
            "velocidad": "personaje_3d_velocidad.png",
            "tanque": "personaje_3d_tanque.png",
        }
        for k, fname in mapeo.items():
            img = cargar_imagen(fname, (ancho_av, alto_av), preservar_aspecto=True)
            if img:
                self.sprites_3d_tarjetas[k] = img

    def recalcular_fuentes(self):
        """Ajusta proporcionalmente las fuentes según el tamaño real de pantalla."""
        escala = self.ancho / 1280.0
        self.fuente_gigante = pygame.font.SysFont("Arial", max(34, int(60 * escala)), bold=True)
        self.fuente_grande = pygame.font.SysFont("Arial", max(26, int(44 * escala)), bold=True)
        self.fuente_media = pygame.font.SysFont("Arial", max(16, int(24 * escala)), bold=True)
        self.fuente_pequetia = pygame.font.SysFont("Arial", max(11, int(15 * escala)))

    def dibujar_particulas(self, lista_particulas):
        """Dibuja partículas decorativas en pantalla."""
        for p in lista_particulas:
            p.dibujar(self.pantalla)

    def dibujar_menu_principal(self, botones, posicion_mouse, mejor_puntaje, lista_particulas):
        """Renderiza la pantalla de inicio del juego cubriendo el 100% del fondo y centrando elementos."""
        # 1. Fondo completo
        self.pantalla.blit(self.img_fondo, (0, 0))
        capa_oscura = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        capa_oscura.fill((0, 0, 0, 130))
        self.pantalla.blit(capa_oscura, (0, 0))

        self.dibujar_particulas(lista_particulas)

        # 2. Logo de Título Centrado Arriba
        rect_texto = self.img_texto.get_rect(center=(self.ancho // 2, int(self.alto * 0.14)))
        self.pantalla.blit(self.img_texto, rect_texto)

        # 3. Ilustración del Personaje Centrada Debajo del Título (sin deformaciones)
        rect_p = self.img_personaje.get_rect(center=(self.ancho // 2, int(self.alto * 0.30)))
        self.pantalla.blit(self.img_personaje, rect_p)

        # 4. Botones del Menú Principal Centrados
        for b in botones:
            b.actualizar(posicion_mouse)
            b.dibujar(self.pantalla, self.fuente_media)

        # 5. Información de pie de página centrada
        txt_puntaje = renderizar_texto_ajustado(self.fuente_pequetia, f"Mejor Puntaje: {mejor_puntaje}", DORADO, self.ancho - 40)
        self.pantalla.blit(txt_puntaje, txt_puntaje.get_rect(center=(self.ancho // 2, self.alto - 50)))

        txt_controles = renderizar_texto_ajustado(self.fuente_pequetia, "WASD / Flechas = Mover | ESPACIO = Bomba | ESC = Pausa", GRIS, self.ancho - 40)
        self.pantalla.blit(txt_controles, txt_controles.get_rect(center=(self.ancho // 2, self.alto - 22)))

    def dibujar_seleccion_personaje(self, claves_personajes, indice_seleccionado, fotograma, titulo_texto="SELECCIONA TU PERSONAJE"):
        """Renderiza las 4 tarjetas de personaje asegurando que TODAS quepan 100% visibles, simétricas y centradas."""
        self.pantalla.fill(COLOR_FONDO_OSCURO)

        titulo = renderizar_texto_ajustado(self.fuente_grande, titulo_texto, DORADO, self.ancho - 40)
        self.pantalla.blit(titulo, titulo.get_rect(center=(self.ancho // 2, int(self.alto * 0.08))))

        num_tarjetas = len(claves_personajes)

        # Usar exactamente el 82% del ancho útil para asegurar márgenes laterales en cualquier resolución
        espaciado = max(12, int(self.ancho * 0.018))
        ancho_util = int(self.ancho * 0.82)
        ancho_tarjeta = max(160, min(220, int((ancho_util - (num_tarjetas - 1) * espaciado) / num_tarjetas)))
        alto_tarjeta = max(260, min(360, int(self.alto * 0.42)))

        total_ancho_bloque = (num_tarjetas * ancho_tarjeta) + ((num_tarjetas - 1) * espaciado)
        inicio_x = (self.ancho - total_ancho_bloque) // 2
        inicio_y = (self.alto - alto_tarjeta) // 2 + 10

        for i, clave in enumerate(claves_personajes):
            ch = PERSONAJES[clave]
            x = inicio_x + i * (ancho_tarjeta + espaciado)
            y = inicio_y
            seleccionado = (i == indice_seleccionado)
            rect_tarjeta = pygame.Rect(x, y, ancho_tarjeta, alto_tarjeta)

            if seleccionado:
                brillo = pygame.Surface((ancho_tarjeta + 16, alto_tarjeta + 16), pygame.SRCALPHA)
                alpha_brillo = int(120 + 60 * math.sin(fotograma * 3))
                pygame.draw.rect(brillo, (*ch["color"], alpha_brillo // 4), brillo.get_rect(), border_radius=16)
                self.pantalla.blit(brillo, (x - 8, y - 8))

            bg_color = (50, 55, 80) if seleccionado else (35, 38, 55)
            pygame.draw.rect(self.pantalla, bg_color, rect_tarjeta, border_radius=14)

            color_borde = ch["color"] if seleccionado else GRIS
            grosor_borde = 4 if seleccionado else 1
            pygame.draw.rect(self.pantalla, color_borde, rect_tarjeta, grosor_borde, border_radius=14)

            cx = x + ancho_tarjeta // 2
            char_y = y + int(alto_tarjeta * 0.18)
            rebote = int(math.sin(fotograma * 2 + i) * 4) if seleccionado else 0

            # Renderizar el modelo 3D del personaje dentro de la tarjeta
            sprite_3d = self.sprites_3d_tarjetas.get(clave)
            if sprite_3d:
                # Sombra 3D suave bajo el avatar
                ancho_s = sprite_3d.get_width() + 10
                sombra_av = pygame.Surface((ancho_s, 10), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_av, (0, 0, 0, 100), (0, 0, ancho_s, 10))
                self.pantalla.blit(sombra_av, (cx - ancho_s // 2, y + int(alto_tarjeta * 0.32)))

                rect_av = sprite_3d.get_rect(center=(cx, char_y + rebote))
                self.pantalla.blit(sprite_3d, rect_av)
            else:
                rect_cuerpo = pygame.Rect(cx - 18, char_y - 14 + rebote, 36, 32)
                pygame.draw.rect(self.pantalla, ch["color"], rect_cuerpo, border_radius=8)
                pygame.draw.rect(self.pantalla, ch["acento"], rect_cuerpo, 2, border_radius=8)

            # Nombre formateado
            txt_nombre = renderizar_texto_ajustado(self.fuente_media, ch["nombre"], ch["color"], ancho_tarjeta - 16)
            self.pantalla.blit(txt_nombre, txt_nombre.get_rect(center=(cx, y + int(alto_tarjeta * 0.38))))

            # Descripción formateada
            txt_desc = renderizar_texto_ajustado(self.fuente_pequetia, ch["descripcion"], GRIS_CLARO, ancho_tarjeta - 16)
            self.pantalla.blit(txt_desc, txt_desc.get_rect(center=(cx, y + int(alto_tarjeta * 0.48))))

            # Caja de estadísticas
            stat_y = y + int(alto_tarjeta * 0.60)
            estadisticas = [
                (f"Velocidad: {ch['velocidad']:.1f}", NEON_AZUL),
                (f"Fuego: {ch['potencia_fuego']}", (255, 69, 0)),
                (f"Bombas: {ch['bombas_maximas']}", (255, 140, 0)),
            ]
            for si, (st_texto, st_color) in enumerate(estadisticas):
                st = renderizar_texto_ajustado(self.fuente_pequetia, st_texto, st_color, ancho_tarjeta - 16)
                self.pantalla.blit(st, st.get_rect(center=(cx, stat_y + si * 20)))

            if seleccionado:
                txt_sel = renderizar_texto_ajustado(self.fuente_pequetia, ">> SELECCIONADO <<", DORADO, ancho_tarjeta - 16)
                self.pantalla.blit(txt_sel, txt_sel.get_rect(center=(cx, y + alto_tarjeta - 20)))

        indicador = renderizar_texto_ajustado(self.fuente_pequetia, "FLECHAS Izq/Der = Seleccionar | ENTER = Jugar | ESC = Volver", GRIS, self.ancho - 40)
        self.pantalla.blit(indicador, indicador.get_rect(center=(self.ancho // 2, self.alto - 25)))

    def dibujar_menu_multijugador(self, botones, posicion_mouse, lista_particulas):
        """Renderiza las opciones del vestíbulo multijugador perfectamente centrado."""
        self.pantalla.fill(COLOR_FONDO_OSCURO)
        self.dibujar_particulas(lista_particulas)

        titulo = renderizar_texto_ajustado(self.fuente_grande, "MODO MULTIJUGADOR", NEON_AZUL, self.ancho - 40)
        self.pantalla.blit(titulo, titulo.get_rect(center=(self.ancho // 2, int(self.alto * 0.15))))

        subtitulo = renderizar_texto_ajustado(self.fuente_pequetia, "Elige una opción para jugar en red", GRIS_CLARO, self.ancho - 40)
        self.pantalla.blit(subtitulo, subtitulo.get_rect(center=(self.ancho // 2, int(self.alto * 0.24))))

        for b in botones:
            b.actualizar(posicion_mouse)
            b.dibujar(self.pantalla, self.fuente_media)

    def dibujar_pantalla_conexion(self, entrada_nombre, entrada_ip, botones, estado_servidor, posicion_mouse, lista_particulas):
        """Renderiza el formulario para conectarse a un servidor IP perfectamente centrado."""
        self.pantalla.fill(COLOR_FONDO_OSCURO)
        self.dibujar_particulas(lista_particulas)

        titulo = renderizar_texto_ajustado(self.fuente_grande, "CONECTARSE A PARTIDA", NEON_AZUL, self.ancho - 40)
        self.pantalla.blit(titulo, titulo.get_rect(center=(self.ancho // 2, int(self.alto * 0.12))))

        lbl_nombre = renderizar_texto_ajustado(self.fuente_media, "Tu nombre de jugador:", BLANCO, self.ancho - 40)
        self.pantalla.blit(lbl_nombre, lbl_nombre.get_rect(center=(self.ancho // 2, int(self.alto * 0.24))))
        entrada_nombre.dibujar(self.pantalla, self.fuente_media)

        lbl_ip = renderizar_texto_ajustado(self.fuente_media, "Dirección IP del Servidor:", BLANCO, self.ancho - 40)
        self.pantalla.blit(lbl_ip, lbl_ip.get_rect(center=(self.ancho // 2, int(self.alto * 0.40))))
        entrada_ip.dibujar(self.pantalla, self.fuente_media)

        if estado_servidor:
            color_estado = VERDE if "Conectado" in estado_servidor or "Iniciado" in estado_servidor else ROJO
            txt_estado = renderizar_texto_ajustado(self.fuente_pequetia, estado_servidor, color_estado, self.ancho - 40)
            self.pantalla.blit(txt_estado, txt_estado.get_rect(center=(self.ancho // 2, int(self.alto * 0.56))))

        for b in botones:
            b.actualizar(posicion_mouse)
            b.dibujar(self.pantalla, self.fuente_media)

    def dibujar_configuracion(self, boton_sonido, boton_volver, administrador_sonido, posicion_mouse):
        """Renderiza el menú de configuración centrado."""
        self.pantalla.fill(COLOR_FONDO_OSCURO)

        titulo = renderizar_texto_ajustado(self.fuente_grande, "CONFIGURACIÓN", DORADO, self.ancho - 40)
        self.pantalla.blit(titulo, titulo.get_rect(center=(self.ancho // 2, int(self.alto * 0.12))))

        y = int(self.alto * 0.26)
        lbl_sonido = renderizar_texto_ajustado(self.fuente_media, "Efectos de Sonido:", BLANCO, 250)
        self.pantalla.blit(lbl_sonido, (self.ancho // 2 - 220, y))

        boton_sonido.texto = "SONIDO: ON" if administrador_sonido.activo else "SONIDO: OFF"
        boton_sonido.color_base = VERDE if administrador_sonido.activo else ROJO
        boton_sonido.actualizar(posicion_mouse)
        boton_sonido.dibujar(self.pantalla, self.fuente_pequetia)

        y = int(self.alto * 0.42)
        lbl_ctrl = renderizar_texto_ajustado(self.fuente_media, "Controles del Juego:", BLANCO, 250)
        self.pantalla.blit(lbl_ctrl, (self.ancho // 2 - 220, y))

        controles = [
            "WASD / Flechas Teclado - Mover Personaje",
            "ESPACIO / ENTER - Colocar Bomba",
            "ESC - Pausa / Volver al Menú Principal",
        ]
        for ci, ctrl in enumerate(controles):
            ct = renderizar_texto_ajustado(self.fuente_pequetia, ctrl, GRIS_CLARO, self.ancho // 2 + 100)
            self.pantalla.blit(ct, (self.ancho // 2 - 160, y + 40 + ci * 30))

        boton_volver.actualizar(posicion_mouse)
        boton_volver.dibujar(self.pantalla, self.fuente_media)
