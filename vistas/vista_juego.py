"""
Vista Principal del Juego (VistaJuego).
Renderiza el mapa, entidades (jugadores, bombas, explosiones, enemigos, power-ups) y HUD con escalado dinámico.
"""

import os
import pygame
import math
from configuracion import (ANCHO_CASILLA, COLUMNAS, FILAS, ALTO_HUD,
                           ANCHO_JUEGO, ALTO_JUEGO, CASILLA_VACIA,
                           CASILLA_PARED, CASILLA_BLOQUE, BLANCO, NEGRO,
                           NEON_AZUL, DORADO, ROJO, VERDE, GRIS,
                           COLOR_PARED, COLOR_BLOQUE, COLOR_BLOQUE2,
                           COLOR_SUELO, COLOR_SUELO2, COLOR_BOMBA,
                           COLOR_EXPLOSION, COLOR_EXPLOSION2)
from vistas.componentes import renderizar_texto_ajustado


class VistaJuego:
    def __init__(self, pantalla, superficie_juego, desfasaje_x, desfasaje_y):
        self.pantalla = pantalla
        self.superficie_juego = superficie_juego
        self.desfasaje_x = desfasaje_x
        self.desfasaje_y = desfasaje_y

        # Fuentes
        self.fuente_grande = pygame.font.SysFont("Arial", 32, bold=True)
        self.fuente_media = pygame.font.SysFont("Arial", 20, bold=True)
        self.fuente_pequetia = pygame.font.SysFont("Arial", 14, bold=True)

        # Cargar sprites 3D de los personajes
        self.sprites_3d = {}
        alto_sp = int(ANCHO_CASILLA * 1.35)
        ancho_sp = max(1, int(alto_sp * (230.0 / 485.0)))
        mapeo = {
            "bomberman": "personaje_3d_bomberman.png",
            "fuego": "personaje_3d_fuego.png",
            "fire": "personaje_3d_fuego.png",
            "velocidad": "personaje_3d_velocidad.png",
            "speed": "personaje_3d_velocidad.png",
            "tanque": "personaje_3d_tanque.png",
            "tank": "personaje_3d_tanque.png",
        }
        for k, fname in mapeo.items():
            path = fname if os.path.exists(fname) else os.path.join("recursos", fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites_3d[k] = pygame.transform.smoothscale(img, (ancho_sp, alto_sp))
                except Exception:
                    pass

        # Cargar los 8 sprites de enemigos
        self.sprites_enemigos = {}
        esize = int(ANCHO_CASILLA * 0.85)
        for etype in ["balloom", "globito", "oneal", "doll", "muneco", "minvo", "fantasma", "ovapi", "pass", "veloz", "pontan"]:
            real_type = "balloom" if etype == "globito" else ("doll" if etype == "muneco" else ("pass" if etype == "veloz" else etype))
            fname = f"enemigo_{real_type}.png"
            path = fname if os.path.exists(fname) else os.path.join("recursos", fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.sprites_enemigos[etype] = pygame.transform.smoothscale(img, (esize, esize))
                except Exception:
                    pass

    def renderizar_mapa(self, matriz_mapa):
        """Dibuja la grilla y bloques del escenario."""
        for r in range(FILAS):
            for c in range(COLUMNAS):
                x = c * ANCHO_CASILLA
                y = r * ANCHO_CASILLA + ALTO_HUD
                celda = matriz_mapa[r][c] if (r < len(matriz_mapa) and c < len(matriz_mapa[r])) else CASILLA_VACIA

                if celda == CASILLA_VACIA:
                    color = COLOR_SUELO if (r + c) % 2 == 0 else COLOR_SUELO2
                    pygame.draw.rect(self.superficie_juego, color, (x, y, ANCHO_CASILLA, ANCHO_CASILLA))
                elif celda == CASILLA_PARED:
                    pygame.draw.rect(self.superficie_juego, COLOR_PARED, (x, y, ANCHO_CASILLA, ANCHO_CASILLA))
                    pygame.draw.rect(self.superficie_juego, (60, 60, 80), (x, y, ANCHO_CASILLA, ANCHO_CASILLA), 2)
                    pygame.draw.rect(self.superficie_juego, (100, 100, 120), (x + 2, y + 2, ANCHO_CASILLA - 4, ANCHO_CASILLA - 4), 1)
                elif celda == CASILLA_BLOQUE:
                    color = COLOR_BLOQUE if (r + c) % 2 == 0 else COLOR_BLOQUE2
                    pygame.draw.rect(self.superficie_juego, color, (x, y, ANCHO_CASILLA, ANCHO_CASILLA))
                    pygame.draw.rect(self.superficie_juego, (140, 100, 40), (x, y, ANCHO_CASILLA, ANCHO_CASILLA), 2)
                    pygame.draw.line(self.superficie_juego, (120, 80, 30), (x, y + ANCHO_CASILLA // 2), (x + ANCHO_CASILLA, y + ANCHO_CASILLA // 2), 1)

    def renderizar_bombas(self, lista_bombas, fotograma):
        """Dibuja las bombas y sus mechas."""
        for b in lista_bombas:
            pos_x = getattr(b, 'posicion_x', b.get('x') if isinstance(b, dict) else 0)
            pos_y = getattr(b, 'posicion_y', b.get('y') if isinstance(b, dict) else 0)
            temporizador = getattr(b, 'temporizador', b.get('timer', 180) if isinstance(b, dict) else 180)

            x, y = int(pos_x), int(pos_y)
            pulso = math.sin(fotograma * 5) * 3
            radio = int(ANCHO_CASILLA * 0.35 + pulso)

            pygame.draw.circle(self.superficie_juego, COLOR_BOMBA, (x, y), radio)
            pygame.draw.circle(self.superficie_juego, (80, 80, 80), (x, y), radio, 2)
            mecha_y = y - radio
            pygame.draw.line(self.superficie_juego, (200, 200, 200), (x, mecha_y), (x + 4, mecha_y - 6), 2)

            if temporizador < 60 and (temporizador // 5) % 2 == 0:
                pygame.draw.circle(self.superficie_juego, (255, 200, 50), (x + 4, mecha_y - 6), 4)

    def renderizar_explosiones(self, lista_explosiones):
        """Dibuja el fuego producido por las explosiones."""
        for exp in lista_explosiones:
            pos_x = getattr(exp, 'posicion_x', exp.get('x') if isinstance(exp, dict) else 0)
            pos_y = getattr(exp, 'posicion_y', exp.get('y') if isinstance(exp, dict) else 0)
            temporizador = getattr(exp, 'temporizador', exp.get('timer', 20) if isinstance(exp, dict) else 20)

            x, y = int(pos_x), int(pos_y)
            alpha = temporizador / 20.0
            radio = int(ANCHO_CASILLA * 0.5 * alpha + ANCHO_CASILLA * 0.2)

            cr = min(255, int(COLOR_EXPLOSION[0] * alpha))
            cg = min(255, int(COLOR_EXPLOSION[1] * alpha))
            cb = min(255, int(COLOR_EXPLOSION[2] * alpha))
            pygame.draw.circle(self.superficie_juego, (cr, cg, cb), (x, y), radio)

            cr2 = min(255, int(COLOR_EXPLOSION2[0] * alpha))
            cg2 = min(255, int(COLOR_EXPLOSION2[1] * alpha))
            cb2 = min(255, int(COLOR_EXPLOSION2[2] * alpha))
            pygame.draw.circle(self.superficie_juego, (cr2, cg2, cb2), (x, y), max(1, radio - 4))

    def renderizar_puerta(self, modelo_o_estado, fotograma):
        """Renderiza la puerta de salida: reja cerrada con candado o portal místico abierto."""
        if isinstance(modelo_o_estado, dict):
            puerta = modelo_o_estado.get("door", {})
            revelada = puerta.get("revealed", False)
            abierta = puerta.get("open", False)
            pos = puerta.get("cell", (0, 0))
            matriz = modelo_o_estado.get("grid", [])
        else:
            revelada = modelo_o_estado.puerta_revelada
            abierta = modelo_o_estado.puerta_abierta
            pos = modelo_o_estado.posicion_puerta
            matriz = modelo_o_estado.matriz_mapa

        if not revelada:
            return

        r, c = pos
        if r < len(matriz) and c < len(matriz[r]) and matriz[r][c] == CASILLA_BLOQUE:
            return

        dx = c * ANCHO_CASILLA
        dy = r * ANCHO_CASILLA + ALTO_HUD
        rect = pygame.Rect(dx, dy, ANCHO_CASILLA, ANCHO_CASILLA)

        pygame.draw.rect(self.superficie_juego, (25, 20, 38), rect)
        pygame.draw.rect(self.superficie_juego, (85, 80, 105), rect, 2)

        if abierta:
            pulso = math.sin(fotograma * 7) * 3
            cx, cy = dx + ANCHO_CASILLA // 2, dy + ANCHO_CASILLA // 2
            pygame.draw.circle(self.superficie_juego, (15, 35, 75), (cx, cy), int(15 + pulso))
            pygame.draw.circle(self.superficie_juego, NEON_AZUL, (cx, cy), int(11 + pulso))
            pygame.draw.circle(self.superficie_juego, BLANCO, (cx, cy), int(5 + pulso * 0.5))
            pygame.draw.rect(self.superficie_juego, DORADO, rect, 2, border_radius=4)

            bob = int(math.sin(fotograma * 8) * 3)
            pts = [(cx, dy + 6 + bob), (cx - 6, dy + bob), (cx + 6, dy + bob)]
            pygame.draw.polygon(self.superficie_juego, DORADO, pts)
            txt = self.fuente_pequetia.render("EXIT", True, (0, 255, 200))
            self.superficie_juego.blit(txt, txt.get_rect(center=(cx, dy + ANCHO_CASILLA - 9)))
        else:
            pygame.draw.rect(self.superficie_juego, (35, 30, 42), (dx + 4, dy + 4, ANCHO_CASILLA - 8, ANCHO_CASILLA - 8))
            for bar_x in range(dx + 8, dx + ANCHO_CASILLA - 6, 6):
                pygame.draw.line(self.superficie_juego, (130, 130, 145), (bar_x, dy + 5), (bar_x, dy + ANCHO_CASILLA - 5), 2)
            cx, cy = dx + ANCHO_CASILLA // 2, dy + ANCHO_CASILLA // 2
            pygame.draw.arc(self.superficie_juego, DORADO, (cx - 6, cy - 10, 12, 10), 0, 3.14159, 2)
            pygame.draw.rect(self.superficie_juego, (230, 180, 0), (cx - 7, cy - 3, 14, 11), border_radius=2)
            pygame.draw.circle(self.superficie_juego, (40, 30, 10), (cx, cy + 2), 2)

    def renderizar_notificaciones(self, modelo_o_estado):
        """Renderiza el banner superior de notificación o alerta."""
        if isinstance(modelo_o_estado, dict):
            texto = modelo_o_estado.get("notification", "")
            es_abierta = modelo_o_estado.get("door", {}).get("open", False)
        else:
            texto = modelo_o_estado.notificacion_puerta if modelo_o_estado.temporizador_notificacion > 0 else ""
            es_abierta = modelo_o_estado.puerta_abierta

        if not texto:
            return

        banner_w = min(ANCHO_JUEGO - 40, max(280, len(texto) * 8 + 36))
        banner_h = 32
        bx = (ANCHO_JUEGO - banner_w) // 2
        by = ALTO_HUD + 6

        surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        surf.fill((12, 16, 32, 225))
        bcolor = DORADO if es_abierta else NEON_AZUL
        pygame.draw.rect(surf, bcolor, (0, 0, banner_w, banner_h), 2, border_radius=8)
        self.superficie_juego.blit(surf, (bx, by))

        txt = self.fuente_pequetia.render(texto, True, BLANCO)
        self.superficie_juego.blit(txt, txt.get_rect(center=(ANCHO_JUEGO // 2, by + banner_h // 2)))

    def renderizar_enemigos(self, lista_enemigos, fotograma=0, matriz_mapa=None):
        """Dibuja los 8 tipos de enemigos reales con animaciones y traspaso de bloques."""
        for e in lista_enemigos:
            pos_x = getattr(e, 'posicion_x', e.get('x') if isinstance(e, dict) else 0)
            pos_y = getattr(e, 'posicion_y', e.get('y') if isinstance(e, dict) else 0)
            color = getattr(e, 'color', e.get('color', [180, 60, 180]) if isinstance(e, dict) else [180, 60, 180])
            salud = getattr(e, 'salud', e.get('hp', 1) if isinstance(e, dict) else 1)
            direccion = [getattr(e, 'direccion_x', 1), getattr(e, 'direccion_y', 0)] if not isinstance(e, dict) else e.get('dir', [1, 0])
            tipo = getattr(e, 'tipo_enemigo', e.get('type', 'balloom') if isinstance(e, dict) else 'balloom')
            traspasa = getattr(e, 'traspasa_bloques', e.get('pass_blocks', False) if isinstance(e, dict) else False)

            x, y = int(pos_x), int(pos_y)

            # Efecto de aura fantasmal pulsante si traspasa ladrillos
            if traspasa:
                aura_alpha = int(130 + 60 * math.sin(fotograma * 7 + x))
                aura_surf = pygame.Surface((ANCHO_CASILLA + 10, ANCHO_CASILLA + 10), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (170, 60, 250, aura_alpha // 2), (ANCHO_CASILLA // 2 + 5, ANCHO_CASILLA // 2 + 5), int(ANCHO_CASILLA * 0.44))
                pygame.draw.circle(aura_surf, (210, 120, 255, aura_alpha), (ANCHO_CASILLA // 2 + 5, ANCHO_CASILLA // 2 + 5), int(ANCHO_CASILLA * 0.44), 2)
                self.superficie_juego.blit(aura_surf, (x - ANCHO_CASILLA // 2 - 5, y - ANCHO_CASILLA // 2 - 5))

            spr = self.sprites_enemigos.get(tipo)
            if spr:
                spr_draw = spr
                if direccion[0] < 0:
                    spr_draw = pygame.transform.flip(spr, True, False)

                dentro = False
                if matriz_mapa:
                    cur_c = int(pos_x) // ANCHO_CASILLA
                    cur_r = int(pos_y - ALTO_HUD) // ANCHO_CASILLA
                    if 0 <= cur_r < len(matriz_mapa) and 0 <= cur_c < len(matriz_mapa[0]):
                        dentro = (matriz_mapa[cur_r][cur_c] == CASILLA_BLOQUE)

                if dentro and traspasa:
                    spr_trans = spr_draw.copy()
                    spr_trans.set_alpha(180)
                    self.superficie_juego.blit(spr_trans, spr_trans.get_rect(center=(x, y)))
                else:
                    self.superficie_juego.blit(spr_draw, spr_draw.get_rect(center=(x, y)))
            else:
                radio = int(ANCHO_CASILLA * 0.35)
                pygame.draw.circle(self.superficie_juego, tuple(color), (x, y), radio)
                pygame.draw.circle(self.superficie_juego, BLANCO, (x, y), radio, 2)
                ojox = x + direccion[0] * 4
                ojoy = y + direccion[1] * 4 - 2
                pygame.draw.circle(self.superficie_juego, NEGRO, (int(ojox - 4), int(ojoy)), 3)
                pygame.draw.circle(self.superficie_juego, NEGRO, (int(ojox + 4), int(ojoy)), 3)

            if salud > 1:
                txt_salud = self.fuente_pequetia.render(f"♥{salud}", True, (255, 90, 90))
                self.superficie_juego.blit(txt_salud, txt_salud.get_rect(center=(x, y - int(ANCHO_CASILLA * 0.45))))

    def renderizar_mejoras(self, lista_mejoras, fotograma):
        """Dibuja las mejoras coleccionables (power-ups)."""
        for m in lista_mejoras:
            pos_x = getattr(m, 'posicion_x', m.get('x') if isinstance(m, dict) else 0)
            pos_y = getattr(m, 'posicion_y', m.get('y') if isinstance(m, dict) else 0)
            tipo = getattr(m, 'tipo_mejora', m.get('type', 'mas_bomba') if isinstance(m, dict) else 'mas_bomba')

            x, y = int(pos_x), int(pos_y)
            flotacion = math.sin(fotograma * 3 + x) * 3
            ry = int(y + flotacion)

            colores = {
                "mas_bomba": (255, 140, 0),
                "mas_fuego": (255, 69, 0),
                "mas_velocidad": (0, 200, 200),
                "escudo": (100, 200, 255),
            }
            etiquetas = {"mas_bomba": "B", "mas_fuego": "F", "mas_velocidad": "V", "escudo": "E"}

            color = colores.get(tipo, BLANCO)
            pygame.draw.rect(self.superficie_juego, color, (x - 12, ry - 12, 24, 24), border_radius=6)
            pygame.draw.rect(self.superficie_juego, BLANCO, (x - 12, ry - 12, 24, 24), 2, border_radius=6)

            txt = self.fuente_pequetia.render(etiquetas.get(tipo, "?"), True, BLANCO)
            self.superficie_juego.blit(txt, txt.get_rect(center=(x, ry)))

    def renderizar_jugadores(self, lista_jugadores, fotograma, id_mi_jugador=None):
        """Dibuja los avatares 3D de los jugadores con sombra, animación y nombre autoajustado."""
        for i, p in enumerate(lista_jugadores):
            if isinstance(p, dict):
                vivo = p.get("vivo", True)
                invuln = p.get("invuln_timer", 0)
                escudo = p.get("shield_timer", 0)
                pos_x, pos_y = p.get("x", 0), p.get("y", 0)
                color = tuple(p.get("color", [255, 255, 255]))
                acento = tuple(p.get("acento", [100, 100, 200]))
                nombre = p.get("nombre", f"P{i+1}")
                pid = p.get("id", i)
                char_k = p.get("clave_personaje", p.get("char_key", "bomberman"))
                dx = p.get("dx", 0)
            else:
                vivo = p.vivo
                invuln = p.temporizador_invulnerabilidad
                escudo = p.temporizador_escudo
                pos_x, pos_y = p.posicion_x, p.posicion_y
                color = p.color
                acento = p.acento
                nombre = p.nombre
                pid = p.indice
                char_k = getattr(p, "clave_personaje", "bomberman")
                dx = getattr(p, "dx", 0)

            if not vivo:
                continue

            x, y = int(pos_x), int(pos_y)

            if invuln > 0 and (invuln // 4) % 2 == 0:
                continue

            sprite = self.sprites_3d.get(char_k, self.sprites_3d.get("bomberman"))

            # Sombra 3D en el suelo
            sombra = pygame.Surface((28, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra, (0, 0, 0, 110), (0, 0, 28, 10))
            self.superficie_juego.blit(sombra, (x - 14, y + 10))

            if escudo > 0:
                shield_alpha = int(140 + 60 * math.sin(fotograma * 5))
                escudo_surf = pygame.Surface((56, 56), pygame.SRCALPHA)
                pygame.draw.circle(escudo_surf, (0, 212, 255, shield_alpha // 3), (28, 28), 24)
                pygame.draw.circle(escudo_surf, (0, 212, 255, shield_alpha), (28, 28), 24, 2)
                self.superficie_juego.blit(escudo_surf, (x - 28, y - 28))

            if sprite:
                spr_dir = pygame.transform.flip(sprite, True, False) if dx < 0 else sprite
                rect_spr = spr_dir.get_rect(center=(x, y - 6))
                self.superficie_juego.blit(spr_dir, rect_spr)
            else:
                radio = int(ANCHO_CASILLA * 0.38)
                pygame.draw.circle(self.superficie_juego, color, (x, y), radio)
                pygame.draw.circle(self.superficie_juego, acento, (x, y), radio, 2)

            es_propio = (id_mi_jugador is not None and str(pid) == str(id_mi_jugador))
            sufijo = " (TÚ)" if es_propio else ""
            txt_color = DORADO if es_propio else BLANCO
            txt_nombre = renderizar_texto_ajustado(self.fuente_pequetia, f"{nombre}{sufijo}", txt_color, 80)
            rect_insignia = pygame.Rect(0, 0, txt_nombre.get_width() + 8, txt_nombre.get_height() + 2)
            rect_insignia.center = (x, y - 36)
            pygame.draw.rect(self.superficie_juego, (20, 20, 35, 180), rect_insignia, border_radius=4)
            pygame.draw.rect(self.superficie_juego, NEON_AZUL if es_propio else acento, rect_insignia, 1, border_radius=4)
            self.superficie_juego.blit(txt_nombre, txt_nombre.get_rect(center=rect_insignia.center))

    def renderizar_hud(self, modelo_o_estado):
        """Renderiza la barra superior de interfaz sin solapamientos ni desbordamientos."""
        pygame.draw.rect(self.superficie_juego, (15, 18, 35), (0, 0, ANCHO_JUEGO, ALTO_HUD))
        pygame.draw.line(self.superficie_juego, NEON_AZUL, (0, ALTO_HUD - 1), (ANCHO_JUEGO, ALTO_HUD - 1), 2)

        if isinstance(modelo_o_estado, dict):
            nivel = modelo_o_estado.get("level", 1)
            puntaje = modelo_o_estado.get("score", 0)
            lista_jugadores = list(modelo_o_estado.get("players", {}).values())
            cantidad_enemigos = len(modelo_o_estado.get("enemies", []))
        else:
            nivel = modelo_o_estado.nivel
            puntaje = modelo_o_estado.puntaje
            lista_jugadores = modelo_o_estado.jugadores
            cantidad_enemigos = len(modelo_o_estado.enemigos)

        # Fila superior: Nivel, Puntaje, Enemigos
        txt_nivel = renderizar_texto_ajustado(self.fuente_grande, f"Nivel {nivel}", DORADO, 140)
        self.superficie_juego.blit(txt_nivel, (12, 6))

        txt_puntaje = renderizar_texto_ajustado(self.fuente_media, f"Score: {puntaje}", BLANCO, 160)
        self.superficie_juego.blit(txt_puntaje, txt_puntaje.get_rect(center=(ANCHO_JUEGO // 2, 20)))

        color_enemigos = VERDE if cantidad_enemigos == 0 else ROJO
        txt_enemigos = renderizar_texto_ajustado(self.fuente_media, f"Enemigos: {cantidad_enemigos}", color_enemigos, 140)
        self.superficie_juego.blit(txt_enemigos, (ANCHO_JUEGO - txt_enemigos.get_width() - 12, 6))

        # Estado de la puerta
        if isinstance(modelo_o_estado, dict):
            puerta = modelo_o_estado.get("door", {})
            revelada = puerta.get("revealed", False)
            abierta = puerta.get("open", False)
        else:
            revelada = modelo_o_estado.puerta_revelada
            abierta = modelo_o_estado.puerta_abierta

        if not revelada:
            txt_p = "Puerta: OCULTA"
            col_p = (170, 170, 185)
        elif not abierta:
            txt_p = "Puerta: CERRADA"
            col_p = (255, 150, 50)
        else:
            txt_p = "Puerta: ¡ABIERTA!"
            col_p = VERDE

        surf_p = renderizar_texto_ajustado(self.fuente_pequetia, txt_p, col_p, 130)
        self.superficie_juego.blit(surf_p, (ANCHO_JUEGO - surf_p.get_width() - 12, 34))

        # Fila inferior: Estadísticas de Jugadores distribuidas proporcionalmente
        n_jugadores = max(1, len(lista_jugadores))
        ancho_slot = (ANCHO_JUEGO - 24) // n_jugadores

        for i, p in enumerate(lista_jugadores):
            if isinstance(p, dict):
                nombre = p.get("nombre", f"P{i+1}")
                vidas = p.get("vidas", 3)
                vivo = p.get("vivo", True)
                bombas = p.get("bombas_maximas", 1)
                fuego = p.get("potencia_fuego", 1)
                vel = p.get("velocidad", 5.0)
            else:
                nombre = p.nombre
                vidas = p.vidas
                vivo = p.vivo
                bombas = p.bombas_maximas
                fuego = p.potencia_fuego
                vel = p.velocidad

            pos_x = 12 + i * ancho_slot
            txt_stat = f"{nombre} | HP:{vidas} B:{bombas} F:{fuego} V:{vel:.1f}"
            color_hp = VERDE if vivo else ROJO

            surf_stat = renderizar_texto_ajustado(self.fuente_pequetia, txt_stat, color_hp, ancho_slot - 10)
            self.superficie_juego.blit(surf_stat, (pos_x, 38))

    def renderizar_menu_subir_nivel(self, opciones, indice_seleccionado):
        """Renderiza el diálogo emergente asegurando ajuste dentro de las tarjetas."""
        capa = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 160))
        self.superficie_juego.blit(capa, (0, 0))

        ancho_caja, alto_caja = 500, 260
        bx = (ANCHO_JUEGO - ancho_caja) // 2
        by = (ALTO_JUEGO - alto_caja) // 2

        pygame.draw.rect(self.superficie_juego, (20, 25, 50), (bx, by, ancho_caja, alto_caja), border_radius=16)
        pygame.draw.rect(self.superficie_juego, NEON_AZUL, (bx, by, ancho_caja, alto_caja), 3, border_radius=16)

        titulo = renderizar_texto_ajustado(self.fuente_grande, "¡NIVEL COMPLETADO!", DORADO, ancho_caja - 40)
        self.superficie_juego.blit(titulo, titulo.get_rect(center=(ANCHO_JUEGO // 2, by + 35)))

        subtitulo = renderizar_texto_ajustado(self.fuente_pequetia, "Elige una mejora para tu personaje:", (180, 180, 200), ancho_caja - 40)
        self.superficie_juego.blit(subtitulo, subtitulo.get_rect(center=(ANCHO_JUEGO // 2, by + 70)))

        ancho_tarjeta = 130
        alto_tarjeta = 120
        espaciado = 20
        ancho_total = len(opciones) * ancho_tarjeta + (len(opciones) - 1) * espaciado
        inicio_x = (ANCHO_JUEGO - ancho_total) // 2

        for i, (tipo, etiqueta, color) in enumerate(opciones):
            cx = inicio_x + i * (ancho_tarjeta + espaciado)
            cy = by + 95
            seleccionado = (i == indice_seleccionado)
            rect = pygame.Rect(cx, cy, ancho_tarjeta, alto_tarjeta)

            bg = (40, 45, 70) if seleccionado else (30, 33, 50)
            pygame.draw.rect(self.superficie_juego, bg, rect, border_radius=10)
            color_borde = color if seleccionado else (100, 100, 120)
            grosor = 3 if seleccionado else 1
            pygame.draw.rect(self.superficie_juego, color_borde, rect, grosor, border_radius=10)

            if tipo == "mas_bomba":
                pygame.draw.circle(self.superficie_juego, color, (cx + ancho_tarjeta // 2, cy + 35), 18)
                txt = self.fuente_media.render("B", True, BLANCO)
                self.superficie_juego.blit(txt, txt.get_rect(center=(cx + ancho_tarjeta // 2, cy + 35)))
            elif tipo == "mas_fuego":
                puntos = [(cx + ancho_tarjeta // 2, cy + 15), (cx + ancho_tarjeta // 2 - 15, cy + 55),
                          (cx + ancho_tarjeta // 2 + 15, cy + 55)]
                pygame.draw.polygon(self.superficie_juego, (255, 69, 0), puntos)
            elif tipo == "mas_velocidad":
                flecha = [(cx + ancho_tarjeta // 2 + 20, cy + 35), (cx + ancho_tarjeta // 2 - 10, cy + 20),
                          (cx + ancho_tarjeta // 2 - 10, cy + 50)]
                pygame.draw.polygon(self.superficie_juego, color, flecha)
            elif tipo == "mas_vida":
                hx, hy = cx + ancho_tarjeta // 2, cy + 35
                corazon = [(hx, hy - 12), (hx + 14, hy - 4), (hx + 8, hy + 12),
                           (hx, hy + 6), (hx - 8, hy + 12), (hx - 14, hy - 4)]
                pygame.draw.polygon(self.superficie_juego, (46, 213, 115), corazon)

            txt_etiqueta = renderizar_texto_ajustado(self.fuente_pequetia, etiqueta, BLANCO if seleccionado else (150, 150, 170), ancho_tarjeta - 10)
            self.superficie_juego.blit(txt_etiqueta, txt_etiqueta.get_rect(center=(cx + ancho_tarjeta // 2, cy + alto_tarjeta - 20)))

        indicador = renderizar_texto_ajustado(self.fuente_pequetia, "FLECHAS = Navegar | ENTER = Seleccionar", (100, 100, 120), ancho_caja)
        self.superficie_juego.blit(indicador, indicador.get_rect(center=(ANCHO_JUEGO // 2, by + alto_caja + 20)))

    def renderizar_game_over(self, puntaje, nivel):
        """Renderiza la pantalla de fin de juego ajustando textos."""
        capa = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 180))
        self.superficie_juego.blit(capa, (0, 0))

        titulo = renderizar_texto_ajustado(self.fuente_grande, "GAME OVER", ROJO, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(titulo, titulo.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 - 60)))

        txt_puntaje = renderizar_texto_ajustado(self.fuente_media, f"Puntaje Final: {puntaje}", DORADO, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(txt_puntaje, txt_puntaje.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2)))

        txt_nivel = renderizar_texto_ajustado(self.fuente_media, f"Nivel alcanzado: {nivel}", BLANCO, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(txt_nivel, txt_nivel.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 + 40)))

        indicador = renderizar_texto_ajustado(self.fuente_pequetia, "ESC = Volver al menú principal", GRIS, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(indicador, indicador.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 + 90)))

    def renderizar_victoria(self, puntaje):
        """Renderiza la pantalla de victoria total ajustando textos."""
        capa = pygame.Surface((ANCHO_JUEGO, ALTO_JUEGO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 180))
        self.superficie_juego.blit(capa, (0, 0))

        titulo = renderizar_texto_ajustado(self.fuente_grande, "¡VICTORIA TOTAL!", DORADO, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(titulo, titulo.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 - 60)))

        txt_puntaje = renderizar_texto_ajustado(self.fuente_media, f"Puntaje Final: {puntaje}", BLANCO, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(txt_puntaje, txt_puntaje.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2)))

        indicador = renderizar_texto_ajustado(self.fuente_pequetia, "ESC = Volver al menú principal", GRIS, ANCHO_JUEGO - 40)
        self.superficie_juego.blit(indicador, indicador.get_rect(center=(ANCHO_JUEGO // 2, ALTO_JUEGO // 2 + 60)))

    def actualizar_pantalla(self):
        """Escala dinámicamente la superficie del juego para adaptarse a cualquier resolución de pantalla."""
        ancho_p, alto_p = self.pantalla.get_size()
        escala = min(ancho_p / float(ANCHO_JUEGO), alto_p / float(ALTO_JUEGO))
        nuevo_ancho = max(1, int(ANCHO_JUEGO * escala))
        nuevo_alto = max(1, int(ALTO_JUEGO * escala))

        superficie_escalada = pygame.transform.smoothscale(self.superficie_juego, (nuevo_ancho, nuevo_alto))
        pos_x = (ancho_p - nuevo_ancho) // 2
        pos_y = (alto_p - nuevo_alto) // 2

        self.pantalla.fill(NEGRO)
        self.pantalla.blit(superficie_escalada, (pos_x, pos_y))
        pygame.display.flip()
