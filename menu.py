import sys
import math
import random
import socket
import subprocess
import pygame

from sound_manager import SoundManager
from game import CHARACTERS, Game, GAME_W, GAME_H

pygame.init()

_info = pygame.display.Info()
WIDTH, HEIGHT = _info.current_w, _info.current_h
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BG = (26, 26, 46)
DARK_BG2 = (15, 52, 96)
NEON_BLUE = (0, 212, 255)
GOLD = (255, 215, 0)
RED = (255, 71, 87)
GREEN = (46, 213, 115)
GRAY = (100, 100, 120)
DARK_GRAY = (40, 40, 60)
LIGHT_GRAY = (180, 180, 200)
FIRE_COLOR = (255, 69, 0)
ORANGE = (255, 140, 0)


def is_server_running(host="127.0.0.1", port=5555):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


class Particle:
    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-2, -0.5)
        self.life = random.randint(60, 120)
        self.max_life = self.life
        self.size = random.randint(1, 3)
        self.color = color or random.choice([NEON_BLUE, GOLD, WHITE, (255, 100, 150)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.01
        self.life -= 1

    def draw(self, surface):
        alpha = max(0, self.life / self.max_life)
        r = min(255, int(self.color[0] * alpha))
        g = min(255, int(self.color[1] * alpha))
        b = min(255, int(self.color[2] * alpha))
        if r > 0 or g > 0 or b > 0:
            pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), self.size)


class Button:
    def __init__(self, x, y, w, h, text, color, hover_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color or tuple(min(255, c + 40) for c in color)
        self.hovered = False
        self.hover_scale = 1.0
        self.click_anim = 0

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.05 if self.hovered else 1.0
        self.hover_scale += (target - self.hover_scale) * 0.15
        if self.click_anim > 0:
            self.click_anim -= 1

    def draw(self, surface, font):
        w = int(self.rect.w * self.hover_scale)
        h = int(self.rect.h * self.hover_scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        draw_rect = pygame.Rect(x, y, w, h)
        color = self.hover_color if self.hovered else self.color
        if self.click_anim > 0:
            color = tuple(min(255, c + 80) for c in color)
        shadow = draw_rect.copy()
        shadow.y += 4
        pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=12)
        pygame.draw.rect(surface, color, draw_rect, border_radius=12)
        border_color = WHITE if self.hovered else tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(surface, border_color, draw_rect, 2, border_radius=12)
        if self.hovered:
            glow_rect = draw_rect.inflate(8, 8)
            pygame.draw.rect(surface, color, glow_rect, 3, border_radius=14)
        txt = font.render(self.text, True, WHITE if self.hovered else (240, 240, 240))
        surface.blit(txt, txt.get_rect(center=draw_rect.center))

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.click_anim = 8
            return True
        return False


class TextInput:
    def __init__(self, x, y, w, h, placeholder="", max_chars=60):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.max_chars = max_chars
        self.active = False
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    pasted = root.clipboard_get()
                    root.destroy()
                    for ch in pasted:
                        if ch.isprintable() and len(self.text) < self.max_chars:
                            self.text += ch
                except Exception:
                    pass
            elif len(self.text) < self.max_chars:
                if event.unicode.isprintable():
                    self.text += event.unicode
        self.cursor_timer += 1

    def draw(self, surface, font):
        color = NEON_BLUE if self.active else GRAY
        pygame.draw.rect(surface, DARK_GRAY, self.rect, border_radius=8)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=8)
        if self.text:
            txt = font.render(self.text, True, WHITE)
        elif not self.active:
            txt = font.render(self.placeholder, True, GRAY)
        else:
            txt = font.render(self.placeholder, True, (80, 80, 100))
        surface.blit(txt, (self.rect.x + 12, self.rect.centery - txt.get_height() // 2))
        if self.active and (self.cursor_timer // 30) % 2 == 0:
            cursor_x = self.rect.x + 12 + txt.get_width() + 2
            pygame.draw.line(surface, WHITE, (cursor_x, self.rect.y + 8),
                             (cursor_x, self.rect.y + self.rect.height - 8), 2)


import os

def load_image(path, default_size=None):
    ruta = path if os.path.exists(path) else os.path.join("recursos", path)
    try:
        img = pygame.image.load(ruta).convert_alpha()
        if default_size:
            return pygame.transform.smoothscale(img, default_size)
        return img
    except Exception:
        if default_size:
            surf = pygame.Surface(default_size, pygame.SRCALPHA)
            pygame.draw.rect(surf, (60, 80, 120), surf.get_rect(), border_radius=15)
            return surf
        return pygame.Surface((100, 100), pygame.SRCALPHA)


class MainMenu:
    def __init__(self):
        info = pygame.display.Info()
        self.width = info.current_w
        self.height = info.current_h
        self.fullscreen = True
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.display.set_caption("Bomberman - Menu Principal")
        self.clock = pygame.time.Clock()
        self.state = "main"
        self.sound = SoundManager()
        self.particles = []
        self.frame = 0.0
        self.selected_char = 0
        self.char_keys = list(CHARACTERS.keys())
        self.transition_alpha = 255
        self.transition_target = 0
        self.transition_speed = 8
        self.transitioning = False
        self.next_state = None
        self.high_score = 0
        self.server_status = ""
        self.host_process = None

        self._load_assets()
        self.recalculate_layout()

    def _load_assets(self):
        # Fondos e ilustraciones base
        self.img_fondo_raw = load_image("fondo.jpeg", (1920, 1080))
        self.img_texto_raw = load_image("texto.png", (400, 100))
        self.img_play_raw = load_image("boton_play.png", (200, 60))

        # Cargar modelos 3D de los personajes
        self.char_sprites_3d = {}
        sprite_map = {
            "bomberman": "personaje_3d_bomberman.png",
            "fire": "personaje_3d_fuego.png",
            "speed": "personaje_3d_velocidad.png",
            "tank": "personaje_3d_tanque.png",
        }
        for k, fname in sprite_map.items():
            img = load_image(fname)
            if img:
                self.char_sprites_3d[k] = img

    def recalculate_layout(self):
        cur_w, cur_h = self.screen.get_size()
        self.width = cur_w
        self.height = cur_h
        scale = min(cur_w / 1280.0, cur_h / 720.0)
        self.scale = max(0.6, scale)

        self.font_huge = pygame.font.SysFont("Arial", max(32, int(54 * self.scale)), bold=True)
        self.font_big = pygame.font.SysFont("Arial", max(24, int(40 * self.scale)), bold=True)
        self.font_med = pygame.font.SysFont("Arial", max(16, int(24 * self.scale)), bold=True)
        self.font_small = pygame.font.SysFont("Arial", max(12, int(15 * self.scale)))

        # Fondo escalado al 100% de la resolución actual
        self.img_fondo = pygame.transform.smoothscale(self.img_fondo_raw, (cur_w, cur_h))

        # Muñequito 3D destacado en el menú principal
        char_h = max(130, min(300, int(cur_h * 0.30)))
        char_w = max(60, int(char_h * (230.0 / 485.0)))
        b_sprite = self.char_sprites_3d.get("bomberman")
        if b_sprite:
            self.img_personaje_menu = pygame.transform.smoothscale(b_sprite, (char_w, char_h))
        else:
            self.img_personaje_menu = load_image("personaje_mirando_derecha.png", (char_w, char_h))

        # Título
        logo_w = min(420, int(cur_w * 0.36))
        logo_h = min(110, int(cur_h * 0.13))
        self.img_texto = pygame.transform.smoothscale(self.img_texto_raw, (logo_w, logo_h))

        # Botones del Menú Principal
        bw = max(240, min(380, int(cur_w * 0.30)))
        bh = max(44, min(56, int(cur_h * 0.072)))
        cx = cur_w // 2 - bw // 2
        start_y = int(cur_h * 0.48)
        spacing = int(bh * 1.25)

        self.btn_sp = Button(cx, start_y, bw, bh, "MODO SINGLE PLAYER", GREEN, (40, 180, 100))
        self.btn_mp = Button(cx, start_y + spacing, bw, bh, "MODO MULTIJUGADOR", NEON_BLUE, (0, 160, 200))
        self.btn_settings = Button(cx, start_y + spacing * 2, bw, bh, "CONFIGURACION", GRAY, (120, 120, 140))
        self.btn_exit = Button(cx, start_y + spacing * 3, bw, bh, "SALIR", RED, (200, 50, 60))

        # Botones de Multijugador
        mp_start_y = int(cur_h * 0.38)
        self.btn_host = Button(cx, mp_start_y, bw, bh, "HOSTEAR PARTIDA", GREEN, (40, 180, 100))
        self.btn_join = Button(cx, mp_start_y + spacing, bw, bh, "CONECTARSE", NEON_BLUE, (0, 160, 200))
        self.btn_back = Button(cx, mp_start_y + spacing * 2, bw, bh, "VOLVER", GRAY, (120, 120, 140))

        # Entradas de conexión
        old_name = getattr(self, "name_input", None)
        old_ip = getattr(self, "ip_input", None)
        name_val = old_name.text if old_name else ""
        ip_val = old_ip.text if old_ip else ""
        self.name_input = TextInput(cx, int(cur_h * 0.34), bw, 42, "Jugador", max_chars=25)
        self.ip_input = TextInput(cx, int(cur_h * 0.48), bw, 42, "127.0.0.1:5555", max_chars=60)
        self.name_input.text = name_val
        self.ip_input.text = ip_val
        self.btn_connect = Button(cx, int(cur_h * 0.62), bw, bh, "CONECTAR", NEON_BLUE, (0, 160, 200))
        self.btn_back2 = Button(cx, int(cur_h * 0.62) + spacing, bw, bh, "VOLVER", GRAY, (120, 120, 140))

        # Configuración
        self.btn_sound_on = Button(cur_w // 2 - 80, int(cur_h * 0.32), 160, 44, "SONIDO: ON", GREEN)
        self.btn_sound_off = Button(cur_w // 2 - 80, int(cur_h * 0.32), 160, 44, "SONIDO: OFF", RED)
        self.btn_back_settings = Button(cx, int(cur_h * 0.72), bw, bh, "VOLVER", GRAY, (120, 120, 140))

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
        self.recalculate_layout()

    def start_transition(self, target_state):
        self.transitioning = True
        self.transition_alpha = 0
        self.transition_target = 255
        self.next_state = target_state

    def finish_transition(self):
        self.state = self.next_state
        self.transitioning = False
        self.transition_alpha = 255
        self.transition_target = 0

    def spawn_menu_particles(self):
        if random.random() < 0.3:
            self.particles.append(Particle(
                random.randint(0, self.width), self.height + 10,
                random.choice([NEON_BLUE, GOLD, (255, 100, 150)])
            ))

    def update_particles(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    def draw_gradient_bg(self):
        for y in range(self.height):
            ratio = y / float(self.height)
            r = int(DARK_BG[0] * (1 - ratio) + DARK_BG2[0] * ratio)
            g = int(DARK_BG[1] * (1 - ratio) + DARK_BG2[1] * ratio)
            b = int(DARK_BG[2] * (1 - ratio) + DARK_BG2[2] * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

    def draw_grid_lines(self):
        for y in range(0, self.height, 60):
            pygame.draw.line(self.screen, (*NEON_BLUE[:3],), (0, y), (self.width, y), 1)
        for x in range(0, self.width, 60):
            pygame.draw.line(self.screen, (*NEON_BLUE[:3],), (x, 0), (x, self.height), 1)

    def draw_main_menu(self, mouse_pos):
        self.screen.blit(self.img_fondo, (0, 0))
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        self.draw_particles()

        # Título superior
        rect_texto = self.img_texto.get_rect(center=(self.width // 2, int(self.height * 0.12)))
        self.screen.blit(self.img_texto, rect_texto)

        # Muñequito 3D con animación flotante y sombra realista en el suelo
        if hasattr(self, 'img_personaje_menu') and self.img_personaje_menu:
            rebote = int(math.sin(self.frame * 2.5) * 8)
            y_base = int(self.height * 0.30)
            rect_p = self.img_personaje_menu.get_rect(center=(self.width // 2, y_base + rebote))

            # Sombra 3D suave bajo el personaje
            ancho_sombra = int(rect_p.width * 0.85)
            sombra_surf = pygame.Surface((ancho_sombra, 16), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra_surf, (0, 0, 0, 130), (0, 0, ancho_sombra, 16))
            self.screen.blit(sombra_surf, (self.width // 2 - ancho_sombra // 2, rect_p.bottom - 4))

            # Dibujar modelo 3D
            self.screen.blit(self.img_personaje_menu, rect_p)

        # Botones del Menú Principal
        for btn in [self.btn_sp, self.btn_mp, self.btn_settings, self.btn_exit]:
            btn.update(mouse_pos)
            btn.draw(self.screen, self.font_med)

        score_txt = self.font_small.render(f"Mejor Puntaje: {self.high_score}", True, GOLD)
        self.screen.blit(score_txt, score_txt.get_rect(center=(self.width // 2, self.height - 42)))
        ctrl = self.font_small.render("WASD/Flechas = Mover | ESPACIO = Bomba | F11 = Pantalla Completa", True, GRAY)
        self.screen.blit(ctrl, ctrl.get_rect(center=(self.width // 2, self.height - 18)))

    def draw_character_select(self, mouse_pos, title_text="SELECCIONA TU PERSONAJE"):
        self.screen.fill(DARK_BG)
        title = self.font_big.render(title_text, True, GOLD)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, int(self.height * 0.08))))

        num_cards = len(self.char_keys)
        espaciado = max(10, int(self.width * 0.016))
        card_w = max(160, min(240, int((self.width * 0.88 - (num_cards - 1) * espaciado) / num_cards)))
        card_h = max(260, min(390, int(self.height * 0.58)))
        total_w = num_cards * card_w + (num_cards - 1) * espaciado
        start_x = (self.width - total_w) // 2
        card_y = int(self.height * 0.16)

        for i, key in enumerate(self.char_keys):
            ch = CHARACTERS[key]
            x = start_x + i * (card_w + espaciado)
            y = card_y
            selected = i == self.selected_char
            card_rect = pygame.Rect(x, y, card_w, card_h)

            if selected:
                glow = pygame.Surface((card_w + 16, card_h + 16), pygame.SRCALPHA)
                glow_alpha = int(120 + 60 * math.sin(self.frame * 3))
                pygame.draw.rect(glow, (*ch["color"], glow_alpha // 4), glow.get_rect(), border_radius=16)
                self.screen.blit(glow, (x - 8, y - 8))

            bg_color = (50, 55, 80) if selected else (35, 38, 55)
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=14)
            border_color = ch["color"] if selected else GRAY
            border_w = 3 if selected else 1
            pygame.draw.rect(self.screen, border_color, card_rect, border_w, border_radius=14)

            cx = x + card_w // 2
            bounce = int(math.sin(self.frame * 2.5 + i) * 6) if selected else 0

            # Renderizado del Muñequito 3D correspondiente dentro de la tarjeta
            sprite_raw = self.char_sprites_3d.get(key)
            if sprite_raw:
                av_h = max(60, min(120, int(card_h * 0.32)))
                av_w = max(30, int(av_h * (230.0 / 485.0)))
                av_sprite = pygame.transform.smoothscale(sprite_raw, (av_w, av_h))

                # Sombra 3D suave en la base de la tarjeta
                sombra_base = pygame.Surface((av_w + 10, 10), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_base, (0, 0, 0, 100), (0, 0, av_w + 10, 10))
                self.screen.blit(sombra_base, (cx - (av_w + 10) // 2, y + int(card_h * 0.34)))

                av_rect = av_sprite.get_rect(center=(cx, y + int(card_h * 0.18) + bounce))
                self.screen.blit(av_sprite, av_rect)
            else:
                pygame.draw.circle(self.screen, ch["color"], (cx, y + int(card_h * 0.18) + bounce), 24)

            name_txt = self.font_med.render(ch["name"], True, ch["color"])
            self.screen.blit(name_txt, name_txt.get_rect(center=(cx, y + int(card_h * 0.42))))
            desc_txt = self.font_small.render(ch["desc"], True, LIGHT_GRAY)
            self.screen.blit(desc_txt, desc_txt.get_rect(center=(cx, y + int(card_h * 0.52))))

            stat_y = y + int(card_h * 0.62)
            stats = [
                (f"Vel: {ch['speed']:.1f}", NEON_BLUE),
                (f"Fuego: {ch['bomb_power']}", FIRE_COLOR),
                (f"Bombas: {ch['max_bombs']}", ORANGE),
            ]
            for si, (stat_text, stat_color) in enumerate(stats):
                st = self.font_small.render(stat_text, True, stat_color)
                self.screen.blit(st, st.get_rect(center=(cx, stat_y + si * int(card_h * 0.075))))

            if selected:
                sel_txt = self.font_small.render(">> SELECCIONADO <<", True, GOLD)
                self.screen.blit(sel_txt, sel_txt.get_rect(center=(cx, y + card_h - 22)))

        hint = self.font_small.render("FLECHAS = Seleccionar | ENTER = Jugar | ESC = Volver | F11 = Pantalla Completa", True, GRAY)
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 30)))

    def draw_multiplayer_menu(self, mouse_pos):
        self.screen.fill(DARK_BG)
        self.draw_particles()
        title = self.font_big.render("MULTIJUGADOR", True, NEON_BLUE)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, int(self.height * 0.14))))
        sub = self.font_small.render("Elige una opcion para jugar en red", True, LIGHT_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(self.width // 2, int(self.height * 0.22))))
        for btn in [self.btn_host, self.btn_join, self.btn_back]:
            btn.update(mouse_pos)
            btn.draw(self.screen, self.font_med)

    def draw_join_screen(self, mouse_pos):
        self.screen.fill(DARK_BG)
        self.draw_particles()
        title = self.font_big.render("CONECTARSE A PARTIDA", True, NEON_BLUE)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, int(self.height * 0.14))))
        name_label = self.font_med.render("Tu nombre:", True, WHITE)
        self.screen.blit(name_label, name_label.get_rect(center=(self.width // 2, int(self.height * 0.28))))
        self.name_input.draw(self.screen, self.font_med)
        ip_label = self.font_med.render("IP o Servidor Nube (ej: 127.0.0.1 o host:puerto):", True, WHITE)
        self.screen.blit(ip_label, ip_label.get_rect(center=(self.width // 2, int(self.height * 0.42))))
        self.ip_input.draw(self.screen, self.font_med)
        if self.server_status:
            status_color = GREEN if "Conectado" in self.server_status else RED
            status_txt = self.font_small.render(self.server_status, True, status_color)
            self.screen.blit(status_txt, status_txt.get_rect(center=(self.width // 2, int(self.height * 0.56))))
        for btn in [self.btn_connect, self.btn_back2]:
            btn.update(mouse_pos)
            btn.draw(self.screen, self.font_med)

    def draw_settings(self, mouse_pos):
        self.screen.fill(DARK_BG)
        title = self.font_big.render("CONFIGURACION", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, int(self.height * 0.14))))
        lbl = self.font_med.render("Sonido:", True, WHITE)
        self.screen.blit(lbl, (self.width // 2 - 200, int(self.height * 0.32)))
        sound_btn = self.btn_sound_off if self.sound.enabled else self.btn_sound_on
        sound_btn.text = "SONIDO: ON" if self.sound.enabled else "SONIDO: OFF"
        sound_btn.color = GREEN if self.sound.enabled else RED
        sound_btn.update(mouse_pos)
        sound_btn.draw(self.screen, self.font_small)

        lbl2 = self.font_med.render("Controles:", True, WHITE)
        self.screen.blit(lbl2, (self.width // 2 - 200, int(self.height * 0.44)))
        controls = [
            "WASD / Flechas - Mover",
            "ESPACIO - Colocar bomba",
            "F11 - Alternar Pantalla Completa",
            "ESC - Volver al menu",
        ]
        for ci, ctrl in enumerate(controls):
            ct = self.font_small.render(ctrl, True, LIGHT_GRAY)
            self.screen.blit(ct, (self.width // 2 - 150, int(self.height * 0.48) + ci * 28))
        self.btn_back_settings.update(mouse_pos)
        self.btn_back_settings.draw(self.screen, self.font_med)

    def draw_transition(self):
        if self.transitioning:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self.transition_alpha))
            self.screen.blit(overlay, (0, 0))
            if self.transition_target > 0:
                self.transition_alpha += self.transition_speed
                if self.transition_alpha >= 255:
                    self.finish_transition()
            else:
                self.transition_alpha -= self.transition_speed

    def run_single_player(self):
        game = Game(modo="single", char_keys=[self.char_keys[self.selected_char]], screen=self.screen)
        result = game.run()
        self.screen = game.screen
        self.recalculate_layout()
        if result > self.high_score:
            self.high_score = result
        return result

    def run_multiplayer(self, host, port):
        char_key = self.char_keys[self.selected_char]
        player_name = self.name_input.text.strip() or "Jugador"
        from client import MultiplayerClient
        client = MultiplayerClient(host, port, player_name, char_key, screen=self.screen)
        if not client.connect():
            self.server_status = f"No se pudo conectar a {host}:{port}"
            return "connection_failed"
        result = client.run()
        self.screen = client.screen
        self.recalculate_layout()
        return result

    def host_game(self):
        import time
        try:
            if is_server_running("127.0.0.1", 5555):
                self.server_status = "El servidor ya esta en ejecucion."
                self.hosted_locally = True
                return True
            self.server_status = "Iniciando servidor..."
            self.host_process = subprocess.Popen(
                [sys.executable, "server.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            timeout = 3.0
            elapsed = 0.0
            while elapsed < timeout:
                time.sleep(0.2)
                elapsed += 0.2
                if is_server_running("127.0.0.1", 5555):
                    self.server_status = "Servidor iniciado! Conectando..."
                    self.hosted_locally = True
                    return True
            self.server_status = "Timeout: el servidor no respondio"
            self.stop_hosted_server()
            return False
        except Exception as e:
            self.server_status = f"Error: {e}"
            return False

    def stop_hosted_server(self):
        if self.host_process:
            try:
                self.host_process.terminate()
            except Exception:
                pass
            self.host_process = None

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.frame += dt * 3.0
            mouse_pos = pygame.mouse.get_pos()
            self.spawn_menu_particles()
            self.update_particles()
            if self.transitioning:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                self.draw_transition()
                pygame.display.flip()
                continue
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.recalculate_layout()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if self.state == "main":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_sp.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("char_select")
                        elif self.btn_mp.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("multiplayer")
                        elif self.btn_settings.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("settings")
                        elif self.btn_exit.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.sound.play('menu_select')
                            self.start_transition("char_select")
                elif self.state == "char_select":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            self.selected_char = (self.selected_char - 1) % len(self.char_keys)
                            self.sound.play('menu_hover')
                        elif event.key == pygame.K_RIGHT:
                            self.selected_char = (self.selected_char + 1) % len(self.char_keys)
                            self.sound.play('menu_hover')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.sound.play('menu_select')
                            self.start_transition("playing_sp")
                        elif event.key == pygame.K_ESCAPE:
                            self.sound.play('menu_select')
                            self.start_transition("main")
                elif self.state == "multiplayer":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_host.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            if self.host_game():
                                self.start_transition("playing_mp")
                        elif self.btn_join.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("join")
                        elif self.btn_back.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("main")
                elif self.state == "join":
                    self.name_input.handle_event(event)
                    self.ip_input.handle_event(event)
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_connect.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.hosted_locally = False
                            ip = (self.ip_input.text or "127.0.0.1:5555").strip()
                            self.server_status = f"Conectando a {ip}..."
                            self.start_transition("playing_mp")
                        elif self.btn_back2.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("multiplayer")
                elif self.state == "settings":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.btn_sound_on.is_clicked(event.pos) or self.btn_sound_off.is_clicked(event.pos):
                            self.sound.toggle()
                            self.sound.play('menu_select')
                        elif self.btn_back_settings.is_clicked(event.pos):
                            self.sound.play('menu_select')
                            self.start_transition("main")
                elif self.state in ("playing_sp", "playing_mp"):
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.start_transition("main")
            if self.state == "main":
                self.draw_main_menu(mouse_pos)
            elif self.state == "char_select":
                self.draw_character_select(mouse_pos)
            elif self.state == "multiplayer":
                self.draw_multiplayer_menu(mouse_pos)
            elif self.state == "join":
                self.draw_join_screen(mouse_pos)
            elif self.state == "settings":
                self.draw_settings(mouse_pos)
            elif self.state == "playing_sp":
                self.draw_transition()
                pygame.display.flip()
                self.run_single_player()
                self.start_transition("main")
                continue
            elif self.state == "playing_mp":
                self.draw_transition()
                pygame.display.flip()
                if getattr(self, "hosted_locally", False):
                    host = "127.0.0.1"
                    port = 5555
                    self.hosted_locally = False
                else:
                    raw_host = (self.ip_input.text or "127.0.0.1:5555").strip()
                    if ":" in raw_host:
                        parts = raw_host.split(":", 1)
                        host = parts[0].strip()
                        try:
                            port = int(parts[1].strip())
                        except ValueError:
                            port = 5555
                    else:
                        host = raw_host
                        port = 5555
                result = self.run_multiplayer(host, port)
                if result == "connection_failed":
                    self.server_status = f"No se pudo conectar a {host}:{port}"
                self.start_transition("multiplayer")
                continue
            self.draw_transition()
            pygame.display.flip()
        self.stop_hosted_server()
        pygame.quit()
        sys.exit()
