"""
Componentes Visuales de la Interfaz (UI).
Incluye Botones, Campos de Texto, Partículas y Carga de Imágenes con ajuste automático de texto y aspecto proporcional.
"""

import os
import random
import pygame
from configuracion import (BLANCO, NEGRO, NEON_AZUL, DORADO, GRIS,
                           GRIS_OSCURO, GRIS_CLARO)


def cargar_imagen(ruta_archivo, tamano_defecto, preservar_aspecto=True):
    """Carga una imagen de disco (buscando también en recursos/) opcionalmente conservando su relación de aspecto."""
    rutas = [
        ruta_archivo,
        os.path.join("recursos", ruta_archivo),
        os.path.join("recursos", os.path.basename(ruta_archivo))
    ]
    for r in rutas:
        if os.path.exists(r):
            try:
                imagen = pygame.image.load(r).convert_alpha()
                ancho_orig, alto_orig = imagen.get_size()
                if tamano_defecto:
                    ancho_max, alto_max = tamano_defecto
                    if preservar_aspecto:
                        escala = min(ancho_max / float(ancho_orig), alto_max / float(alto_orig))
                        nuevo_ancho = max(1, int(ancho_orig * escala))
                        nuevo_alto = max(1, int(alto_orig * escala))
                        return pygame.transform.smoothscale(imagen, (nuevo_ancho, nuevo_alto))
                    else:
                        return pygame.transform.smoothscale(imagen, (ancho_max, alto_max))
                return imagen
            except Exception:
                pass

    superficie = pygame.Surface(tamano_defecto or (100, 100), pygame.SRCALPHA)
    pygame.draw.rect(superficie, (60, 80, 120), superficie.get_rect(), border_radius=15)
    return superficie


def renderizar_texto_ajustado(fuente, texto, color, ancho_maximo):
    """Renderiza un texto escalándolo si excede el ancho máximo disponible del contenedor."""
    surf_original = fuente.render(texto, True, color)
    if surf_original.get_width() <= ancho_maximo:
        return surf_original

    factor = ancho_maximo / float(surf_original.get_width())
    nuevo_ancho = int(surf_original.get_width() * factor)
    nuevo_alto = max(1, int(surf_original.get_height() * factor))
    return pygame.transform.smoothscale(surf_original, (nuevo_ancho, nuevo_alto))


class Particula:
    """Efecto visual de partículas en movimiento para fondos."""
    def __init__(self, x, y, color=None):
        self.posicion_x = x
        self.posicion_y = y
        self.velocidad_x = random.uniform(-1, 1)
        self.velocidad_y = random.uniform(-2, -0.5)
        self.vida = random.randint(60, 120)
        self.vida_maxima = self.vida
        self.tamano = random.randint(1, 3)
        self.color = color or random.choice([NEON_AZUL, DORADO, BLANCO, (255, 100, 150)])

    def actualizar(self):
        """Actualiza la física y vida útil de la partícula."""
        self.posicion_x += self.velocidad_x
        self.posicion_y += self.velocidad_y
        self.velocidad_y += 0.01
        self.vida -= 1

    def dibujar(self, superficie):
        """Dibuja la partícula con opacidad progresiva."""
        alpha = max(0, self.vida / self.vida_maxima)
        r = min(255, int(self.color[0] * alpha))
        g = min(255, int(self.color[1] * alpha))
        b = min(255, int(self.color[2] * alpha))
        if r > 0 or g > 0 or b > 0:
            pygame.draw.circle(superficie, (r, g, b), (int(self.posicion_x), int(self.posicion_y)), self.tamano)


class Boton:
    """Botón estilizado interactivo con animación de resaltado y texto autoajustado."""
    def __init__(self, x, y, ancho, alto, texto, color_base, color_hover=None):
        self.rectangulo = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color_base = color_base
        self.color_hover = color_hover or tuple(min(255, c + 40) for c in color_base)
        self.bajo_puntero = False
        self.escala_hover = 1.0
        self.animacion_click = 0

    def actualizar(self, posicion_mouse):
        """Actualiza la animación hover del botón."""
        self.bajo_puntero = self.rectangulo.collidepoint(posicion_mouse)
        objetivo = 1.05 if self.bajo_puntero else 1.0
        self.escala_hover += (objetivo - self.escala_hover) * 0.15
        if self.animacion_click > 0:
            self.animacion_click -= 1

    def dibujar(self, superficie, fuente):
        """Renderiza el botón asegurando que el texto quepa perfectamente en la caja."""
        ancho = int(self.rectangulo.w * self.escala_hover)
        alto = int(self.rectangulo.h * self.escala_hover)
        x = self.rectangulo.centerx - ancho // 2
        y = self.rectangulo.centery - alto // 2
        rect_render = pygame.Rect(x, y, ancho, alto)

        color = self.color_hover if self.bajo_puntero else self.color_base
        if self.animacion_click > 0:
            color = tuple(min(255, c + 80) for c in color)

        sombra = rect_render.copy()
        sombra.y += 4
        pygame.draw.rect(superficie, NEGRO, sombra, border_radius=12)
        pygame.draw.rect(superficie, color, rect_render, border_radius=12)

        color_borde = BLANCO if self.bajo_puntero else tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(superficie, color_borde, rect_render, 2, border_radius=12)

        if self.bajo_puntero:
            rect_brillo = rect_render.inflate(8, 8)
            pygame.draw.rect(superficie, color, rect_brillo, 3, border_radius=14)

        color_txt = BLANCO if self.bajo_puntero else (240, 240, 240)
        superficie_texto = renderizar_texto_ajustado(fuente, self.texto, color_txt, rect_render.width - 24)
        superficie.blit(superficie_texto, superficie_texto.get_rect(center=rect_render.center))

    def es_clicqueado(self, posicion_mouse):
        """Devuelve True si el botón ha sido presionado."""
        if self.rectangulo.collidepoint(posicion_mouse):
            self.animacion_click = 8
            return True
        return False


class CampoTexto:
    """Campo de entrada de texto interactivo con ajuste dinámico."""
    def __init__(self, x, y, ancho, alto, marcador_posicion="", max_caracteres=20):
        self.rectangulo = pygame.Rect(x, y, ancho, alto)
        self.texto = ""
        self.marcador_posicion = marcador_posicion
        self.max_caracteres = max_caracteres
        self.activo = False
        self.temporizador_cursor = 0

    def manejar_evento(self, evento):
        """Procesa entradas de teclado para modificar el texto."""
        if evento.type == pygame.MOUSEBUTTONDOWN:
            self.activo = self.rectangulo.collidepoint(evento.pos)

        if evento.type == pygame.KEYDOWN and self.activo:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif evento.key == pygame.K_RETURN:
                self.activo = False
            elif len(self.texto) < self.max_caracteres:
                if evento.unicode.isprintable():
                    self.texto += evento.unicode

        self.temporizador_cursor += 1

    def dibujar(self, superficie, fuente):
        """Dibuja la caja de texto ajustada al contenedor."""
        color_borde = NEON_AZUL if self.activo else GRIS
        pygame.draw.rect(superficie, GRIS_OSCURO, self.rectangulo, border_radius=8)
        pygame.draw.rect(superficie, color_borde, self.rectangulo, 2, border_radius=8)

        if self.texto:
            superficie_texto = renderizar_texto_ajustado(fuente, self.texto, BLANCO, self.rectangulo.width - 24)
        elif not self.activo:
            superficie_texto = renderizar_texto_ajustado(fuente, self.marcador_posicion, GRIS, self.rectangulo.width - 24)
        else:
            superficie_texto = renderizar_texto_ajustado(fuente, self.marcador_posicion, (80, 80, 100), self.rectangulo.width - 24)

        superficie.blit(superficie_texto, (self.rectangulo.x + 12, self.rectangulo.centery - superficie_texto.get_height() // 2))

        if self.activo and (self.temporizador_cursor // 30) % 2 == 0:
            cursor_x = self.rectangulo.x + 12 + superficie_texto.get_width() + 2
            cursor_x = min(cursor_x, self.rectangulo.right - 8)
            pygame.draw.line(superficie, BLANCO, (cursor_x, self.rectangulo.y + 8),
                             (cursor_x, self.rectangulo.y + self.rectangulo.height - 8), 2)
