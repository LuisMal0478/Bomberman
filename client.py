import pygame
import socket
import threading
import json
import math

pygame.init()

from sound_manager import SoundManager
from game import (COLS, ROWS, CELL, HUD_H, GAME_W, GAME_H, FPS,
                  CELL_EMPTY, CELL_WALL, CELL_BLOCK, CHARACTERS)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_BLUE = (0, 212, 255)
GOLD = (255, 215, 0)
RED = (255, 71, 87)
GREEN = (46, 213, 115)
GRAY = (100, 100, 120)
DARK_GRAY = (40, 40, 60)
LIGHT_GRAY = (180, 180, 200)

WALL_COLOR = (80, 80, 100)
BLOCK_COLOR = (180, 140, 60)
BLOCK_COLOR2 = (160, 120, 50)
FLOOR_COLOR = (40, 50, 30)
FLOOR_COLOR2 = (35, 45, 25)
BOMB_COLOR = (30, 30, 30)
EXPLOSION_COLOR = (255, 120, 0)
EXPLOSION_COLOR2 = (255, 200, 50)


def encode(msg):
    return json.dumps(msg).encode('utf-8') + b"\n"


def decode_line(line):
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


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
        return None


class MultiplayerClient:
    def __init__(self, host, port, player_name, char_key,
                 screen=None, clock=None, font_big=None, font_med=None, font_small=None):
        self.host = host
        self.port = port
        self.player_name = player_name
        self.char_key = char_key
        self.screen = screen or pygame.display.set_mode((GAME_W, GAME_H), pygame.RESIZABLE)
        self.clock = clock or pygame.time.Clock()
        self.font_big = font_big or pygame.font.SysFont("Arial", 36, bold=True)
        self.font_med = font_med or pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = font_small or pygame.font.SysFont("Arial", 16)
        self.sound = SoundManager()
        self.sock = None
        self.connected = False
        self.my_id = None
        self.state = {}
        self.state_lock = threading.Lock()
        self.receive_buffer = b""
        self.frame = 0.0
        self.img_play = load_image("boton_play.png", (200, 60))
        self.img_fondo = load_image("fondo.jpeg", (GAME_W, GAME_H))
        self.play_btn_rect = None

        self.game_surface = pygame.Surface((GAME_W, GAME_H))
        self.player_sprites = {}
        self.enemy_sprites = {}
        self._init_sprites()
        self.update_scale_and_offsets()

    def _init_sprites(self):
        base_h = int(CELL * 1.35)
        base_w = max(1, int(base_h * (230.0 / 485.0)))
        sprite_map = {
            "bomberman": "personaje_3d_bomberman.png",
            "fire": "personaje_3d_fuego.png",
            "speed": "personaje_3d_velocidad.png",
            "tank": "personaje_3d_tanque.png",
        }
        for k, fname in sprite_map.items():
            img = load_image(fname, (base_w, base_h))
            if img:
                self.player_sprites[k] = img

        for etype in ["balloom", "oneal", "doll", "minvo", "fantasma", "ovapi", "pass", "pontan"]:
            img = load_image(f"enemigo_{etype}.png", (int(CELL * 0.85), int(CELL * 0.85)))
            if img:
                self.enemy_sprites[etype] = img

    def update_scale_and_offsets(self):
        cur_w, cur_h = self.screen.get_size()
        scale = min(cur_w / float(GAME_W), cur_h / float(GAME_H))
        self.render_w = max(1, int(GAME_W * scale))
        self.render_h = max(1, int(GAME_H * scale))
        self.offset_x = (cur_w - self.render_w) // 2
        self.offset_y = (cur_h - self.render_h) // 2
        self.scale_factor = scale

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.connected = True
            self.sock.settimeout(None)
            join_msg = encode({"type": "join", "name": self.player_name, "char": self.char_key})
            self.sock.send(join_msg)
            self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._recv_thread.start()
            return True
        except Exception as e:
            print(f"Error de conexion a {self.host}:{self.port}: {e}")
            self.connected = False
            return False

    def _receive_loop(self):
        try:
            while self.connected:
                data = self.sock.recv(4096)
                if not data:
                    break
                self.receive_buffer += data
                while b"\n" in self.receive_buffer:
                    line, self.receive_buffer = self.receive_buffer.split(b"\n", 1)
                    msg = decode_line(line.decode('utf-8', errors='replace'))
                    if msg is None:
                        continue
                    msg_type = msg.get("type")
                    if msg_type == "join_ok":
                        self.my_id = msg.get("id")
                        self.send_ready()
                    elif msg_type == "state":
                        with self.state_lock:
                            old_exp = len(self.state.get("explosions", []))
                            new_exp = len(msg.get("explosions", []))
                            if new_exp > old_exp:
                                self.sound.play('explosion')

                            old_pu = len(self.state.get("powerups", []))
                            new_pu = len(msg.get("powerups", []))
                            if new_pu < old_pu:
                                self.sound.play('powerup')

                            old_lvl = self.state.get("level", 1)
                            new_lvl = msg.get("level", 1)
                            if new_lvl > old_lvl:
                                self.sound.play('level_up')

                            if self.my_id is not None:
                                old_p = self.state.get("players", {}).get(str(self.my_id), {})
                                new_p = msg.get("players", {}).get(str(self.my_id), {})
                                if old_p and new_p and old_p.get("lives", 3) > new_p.get("lives", 3):
                                    if new_p.get("lives", 3) <= 0:
                                        self.sound.play('death')
                                    else:
                                        self.sound.play('hurt')

                            self.state = msg
                    elif msg_type == "game_start":
                        self.sound.play('level_up')
                        with self.state_lock:
                            self.state["game_state"] = "playing"
                    elif msg_type == "player_join":
                        pass
                    elif msg_type == "player_leave":
                        pass
        except (ConnectionResetError, OSError):
            pass
        finally:
            self.connected = False

    def send_move(self, dx, dy):
        if self.connected and self.sock:
            try:
                self.sock.send(encode({"type": "move", "dx": dx, "dy": dy}))
            except Exception:
                pass

    def send_bomb(self):
        if self.connected and self.sock:
            try:
                self.sock.send(encode({"type": "bomb"}))
            except Exception:
                pass

    def send_ready(self):
        if self.connected and self.sock:
            try:
                self.sock.send(encode({"type": "ready", "ready": True}))
            except Exception:
                pass

    def draw_waiting(self):
        self.game_surface.blit(self.img_fondo, (0, 0))
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.game_surface.blit(overlay, (0, 0))
        dots = "." * ((int(self.frame * 2) % 3) + 1)
        title = self.font_big.render(f"Conectado{dots}", True, GOLD)
        self.game_surface.blit(title, title.get_rect(center=(GAME_W // 2, GAME_H // 2 - 40)))
        info = self.font_med.render("Esperando inicio del juego...", True, NEON_BLUE)
        self.game_surface.blit(info, info.get_rect(center=(GAME_W // 2, GAME_H // 2 + 20)))
        ctrl = self.font_small.render("ESC = Volver al menu", True, GRAY)
        self.game_surface.blit(ctrl, ctrl.get_rect(center=(GAME_W // 2, GAME_H - 30)))

    def draw_game(self):
        gs = self.state
        grid = gs.get("grid", [])
        for r in range(ROWS):
            for c in range(COLS):
                x = c * CELL
                y = r * CELL + HUD_H
                if r < len(grid) and c < len(grid[r]):
                    cell = grid[r][c]
                else:
                    cell = CELL_EMPTY
                if cell == CELL_EMPTY:
                    color = FLOOR_COLOR if (r + c) % 2 == 0 else FLOOR_COLOR2
                    pygame.draw.rect(self.game_surface, color, (x, y, CELL, CELL))
                elif cell == CELL_WALL:
                    pygame.draw.rect(self.game_surface, WALL_COLOR, (x, y, CELL, CELL))
                    pygame.draw.rect(self.game_surface, (60, 60, 80), (x, y, CELL, CELL), 2)
                elif cell == CELL_BLOCK:
                    color = BLOCK_COLOR if (r + c) % 2 == 0 else BLOCK_COLOR2
                    pygame.draw.rect(self.game_surface, color, (x, y, CELL, CELL))
                    pygame.draw.rect(self.game_surface, (140, 100, 40), (x, y, CELL, CELL), 2)
        self.draw_door()
        for b in gs.get("bombs", []):
            bx, by = int(b["x"]), int(b["y"])
            pulse = math.sin(self.frame * 5) * 3
            r = int(CELL * 0.35 + pulse)
            pygame.draw.circle(self.game_surface, BOMB_COLOR, (bx, by), r)
            pygame.draw.circle(self.game_surface, (80, 80, 80), (bx, by), r, 2)
            if b.get("timer", 180) < 60:
                if (b.get("timer", 180) // 5) % 2 == 0:
                    pygame.draw.circle(self.game_surface, (255, 200, 50), (bx + 4, by - r - 6), 4)
        for e in gs.get("explosions", []):
            ex, ey = int(e["x"]), int(e["y"])
            alpha = e.get("timer", 20) / 20.0
            r = int(CELL * 0.5 * alpha + CELL * 0.2)
            color = (min(255, int(EXPLOSION_COLOR[0] * alpha)),
                     min(255, int(EXPLOSION_COLOR[1] * alpha)),
                     min(255, int(EXPLOSION_COLOR[2] * alpha)))
            pygame.draw.circle(self.game_surface, color, (ex, ey), r)
            color2 = (min(255, int(EXPLOSION_COLOR2[0] * alpha)),
                       min(255, int(EXPLOSION_COLOR2[1] * alpha)),
                       min(255, int(EXPLOSION_COLOR2[2] * alpha)))
            pygame.draw.circle(self.game_surface, color2, (ex, ey), max(1, r - 4))
        for en in gs.get("enemies", []):
            ex, ey = int(en["x"]), int(en["y"])
            etype = en.get("type", "balloom")
            spr = self.enemy_sprites.get(etype)

            if en.get("pass_blocks"):
                aura_alpha = int(130 + 60 * math.sin(self.frame * 7 + ex))
                aura_surf = pygame.Surface((CELL + 10, CELL + 10), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (170, 60, 250, aura_alpha // 2), (CELL // 2 + 5, CELL // 2 + 5), int(CELL * 0.44))
                pygame.draw.circle(aura_surf, (210, 120, 255, aura_alpha), (CELL // 2 + 5, CELL // 2 + 5), int(CELL * 0.44), 2)
                self.game_surface.blit(aura_surf, (ex - CELL // 2 - 5, ey - CELL // 2 - 5))

            if spr:
                spr_draw = spr
                if en.get("dir", [1, 0])[0] < 0:
                    spr_draw = pygame.transform.flip(spr, True, False)
                self.game_surface.blit(spr_draw, spr_draw.get_rect(center=(ex, ey)))
            else:
                r = int(CELL * 0.35)
                ecolor = tuple(en.get("color", [180, 60, 180]))
                pygame.draw.circle(self.game_surface, ecolor, (ex, ey), r)
                pygame.draw.circle(self.game_surface, WHITE, (ex, ey), r, 2)
                edir = en.get("dir", [1, 0])
                eye_x = ex + edir[0] * 4
                eye_y = ey + edir[1] * 4 - 2
                pygame.draw.circle(self.game_surface, BLACK, (int(eye_x - 4), int(eye_y)), 3)
                pygame.draw.circle(self.game_surface, BLACK, (int(eye_x + 4), int(eye_y)), 3)

            if en.get("hp", 1) > 1:
                hp_t = self.font_small.render(f"♥{en['hp']}", True, (255, 90, 90))
                self.game_surface.blit(hp_t, hp_t.get_rect(center=(ex, ey - int(CELL * 0.45))))
        for pu in gs.get("powerups", []):
            px, py = int(pu["x"]), int(pu["y"])
            bob = math.sin(self.frame * 3 + px) * 3
            ry = int(py + bob)
            colors = {"bomb_up": (255, 140, 0), "fire_up": (255, 69, 0),
                      "speed_up": (0, 200, 200), "shield": (100, 200, 255)}
            color = colors.get(pu.get("type"), WHITE)
            pygame.draw.rect(self.game_surface, color, (px - 12, ry - 12, 24, 24), border_radius=6)
            pygame.draw.rect(self.game_surface, WHITE, (px - 12, ry - 12, 24, 24), 2, border_radius=6)
            labels = {"bomb_up": "B", "fire_up": "F", "speed_up": "S", "shield": "E"}
            lt = self.font_small.render(labels.get(pu.get("type", ""), "?"), True, WHITE)
            self.game_surface.blit(lt, lt.get_rect(center=(px, ry)))
        for pid, p in gs.get("players", {}).items():
            if not p.get("alive", True):
                continue
            px, py = int(p["x"]), int(p["y"])
            invuln = p.get("invuln_timer", 0)
            if invuln > 0 and (invuln // 4) % 2 == 0:
                continue

            char_k = p.get("char", p.get("char_key", "bomberman"))
            sprite = self.player_sprites.get(char_k, self.player_sprites.get("bomberman"))

            # Sombra 3D en el suelo
            sombra = pygame.Surface((28, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra, (0, 0, 0, 110), (0, 0, 28, 10))
            self.game_surface.blit(sombra, (px - 14, py + 10))

            shield = p.get("shield_timer", 0)
            if shield > 0:
                sa = int(140 + 60 * math.sin(self.frame * 5))
                escudo = pygame.Surface((56, 56), pygame.SRCALPHA)
                pygame.draw.circle(escudo, (0, 212, 255, sa // 3), (28, 28), 24)
                pygame.draw.circle(escudo, (0, 212, 255, sa), (28, 28), 24, 2)
                self.game_surface.blit(escudo, (px - 28, py - 28))

            if sprite:
                p_dx = p.get("dx", 0)
                spr_dir = pygame.transform.flip(sprite, True, False) if p_dx < 0 else sprite
                rect_spr = spr_dir.get_rect(center=(px, py - 6))
                self.game_surface.blit(spr_dir, rect_spr)
            else:
                pcolor = tuple(p.get("color", [255, 255, 255]))
                paccent = tuple(p.get("accent", [100, 100, 200]))
                r = int(CELL * 0.38)
                pygame.draw.circle(self.game_surface, pcolor, (px, py), r)
                pygame.draw.circle(self.game_surface, paccent, (px, py), r, 2)

            is_me = (str(pid) == str(self.my_id))
            marker = " (TÚ)" if is_me else ""
            txt_color = GOLD if is_me else WHITE
            name_t = self.font_small.render(f"{p.get('name', '???')}{marker}", True, txt_color)
            badge_rect = pygame.Rect(0, 0, name_t.get_width() + 8, name_t.get_height() + 2)
            badge_rect.center = (px, py - 36)
            pygame.draw.rect(self.game_surface, (20, 20, 35, 180), badge_rect, border_radius=4)
            pygame.draw.rect(self.game_surface, NEON_BLUE if is_me else GRAY, badge_rect, 1, border_radius=4)
            self.game_surface.blit(name_t, name_t.get_rect(center=badge_rect.center))

        pygame.draw.rect(self.game_surface, (15, 18, 35), (0, 0, GAME_W, HUD_H))
        pygame.draw.line(self.game_surface, NEON_BLUE, (0, HUD_H - 1), (GAME_W, HUD_H - 1), 2)
        x = 10
        for pid, p in gs.get("players", {}).items():
            name = p.get("name", "???")
            lives = p.get("lives", 0)
            alive = p.get("alive", True)
            hp_color = GREEN if alive else RED
            hp_t = self.font_med.render(f"{name}: HP {lives}", True, hp_color)
            self.game_surface.blit(hp_t, (x, 8))
            sc_t = self.font_small.render(f"Score: {p.get('score', 0)}", True, GOLD)
            self.game_surface.blit(sc_t, (x, 35))
            x += 250
        lvl_t = self.font_big.render(f"Nivel {gs.get('level', 1)}", True, GOLD)
        self.game_surface.blit(lvl_t, lvl_t.get_rect(center=(GAME_W // 2, 18)))
        sc_t = self.font_med.render(f"Score: {gs.get('score', 0)}", True, WHITE)
        self.game_surface.blit(sc_t, sc_t.get_rect(center=(GAME_W // 2, 42)))
        enemies_t = self.font_small.render(f"Enemigos: {len(gs.get('enemies', []))}", True, RED)
        self.game_surface.blit(enemies_t, (GAME_W - 145, 10))

        door = gs.get("door")
        if not door or not door.get("revealed"):
            door_txt = "Puerta: OCULTA"
            door_col = (170, 170, 185)
        elif not door.get("open"):
            door_txt = "Puerta: CERRADA"
            door_col = (255, 150, 50)
        else:
            door_txt = "Puerta: ¡ABIERTA!"
            door_col = GREEN
        txt_puerta = self.font_small.render(door_txt, True, door_col)
        self.game_surface.blit(txt_puerta, (GAME_W - 145, 32))

    def draw_door(self):
        door = self.state.get("door")
        if not door or not door.get("revealed"):
            return
        r = door.get("r", 0)
        c = door.get("c", 0)
        grid = self.state.get("grid", [])
        if r < len(grid) and c < len(grid[r]) and grid[r][c] == CELL_BLOCK:
            return

        dx = c * CELL
        dy = r * CELL + HUD_H
        rect = pygame.Rect(dx, dy, CELL, CELL)

        # Base de piedra / umbral
        pygame.draw.rect(self.game_surface, (25, 20, 38), rect)
        pygame.draw.rect(self.game_surface, (85, 80, 105), rect, 2)

        if door.get("open"):
            pulse = math.sin(self.frame * 7) * 3
            cx, cy = dx + CELL // 2, dy + CELL // 2
            pygame.draw.circle(self.game_surface, (15, 35, 75), (cx, cy), int(15 + pulse))
            pygame.draw.circle(self.game_surface, (0, 212, 255), (cx, cy), int(11 + pulse))
            pygame.draw.circle(self.game_surface, (255, 255, 255), (cx, cy), int(5 + pulse * 0.5))
            pygame.draw.rect(self.game_surface, GOLD, rect, 2, border_radius=4)
            bob = int(math.sin(self.frame * 8) * 3)
            pts_arrow = [
                (cx, dy + 6 + bob),
                (cx - 6, dy + bob),
                (cx + 6, dy + bob)
            ]
            pygame.draw.polygon(self.game_surface, GOLD, pts_arrow)
            txt_entrar = self.font_small.render("EXIT", True, (0, 255, 200))
            self.game_surface.blit(txt_entrar, txt_entrar.get_rect(center=(cx, dy + CELL - 9)))
        else:
            pygame.draw.rect(self.game_surface, (35, 30, 42), (dx + 4, dy + 4, CELL - 8, CELL - 8))
            for bar_x in range(dx + 8, dx + CELL - 6, 6):
                pygame.draw.line(self.game_surface, (130, 130, 145), (bar_x, dy + 5), (bar_x, dy + CELL - 5), 2)
            cx, cy = dx + CELL // 2, dy + CELL // 2
            pygame.draw.arc(self.game_surface, GOLD, (cx - 6, cy - 10, 12, 10), 0, 3.14159, 2)
            pygame.draw.rect(self.game_surface, (230, 180, 0), (cx - 7, cy - 3, 14, 11), border_radius=2)
            pygame.draw.circle(self.game_surface, (40, 30, 10), (cx, cy + 2), 2)

    def draw_game_over(self):
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.game_surface.blit(overlay, (0, 0))
        gs = self.state
        state = gs.get("game_state", "")
        if state == "victory":
            title = self.font_big.render("VICTORIA!", True, GOLD)
        else:
            title = self.font_big.render("GAME OVER", True, RED)
        self.game_surface.blit(title, title.get_rect(center=(GAME_W // 2, GAME_H // 2 - 40)))
        score_t = self.font_med.render(f"Score: {gs.get('score', 0)}", True, WHITE)
        self.game_surface.blit(score_t, score_t.get_rect(center=(GAME_W // 2, GAME_H // 2 + 10)))
        hint = self.font_small.render("ESC = Volver al menu", True, GRAY)
        self.game_surface.blit(hint, hint.get_rect(center=(GAME_W // 2, GAME_H // 2 + 60)))

    def run(self):
        info = pygame.display.Info()
        sw, sh = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
        pygame.display.set_caption("Bomberman - Multijugador")
        self.is_fullscreen = True
        self.game_surface = pygame.Surface((GAME_W, GAME_H))
        self.update_scale_and_offsets()
        running = True
        last_move_time = 0
        move_delay = 16
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.frame += dt * 3.0
            now_ms = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.VIDEORESIZE:
                    self.update_scale_and_offsets()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F11:
                        self.is_fullscreen = not self.is_fullscreen
                        if self.is_fullscreen:
                            cur_info = pygame.display.Info()
                            self.screen = pygame.display.set_mode((cur_info.current_w, cur_info.current_h), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((GAME_W, GAME_H), pygame.RESIZABLE)
                        self.update_scale_and_offsets()
                    with self.state_lock:
                        gs = self.state
                    game_state = gs.get("game_state", "waiting")
                    if game_state == "waiting":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.send_ready()
                    elif game_state == "playing":
                        if event.key == pygame.K_SPACE:
                            self.send_bomb()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    with self.state_lock:
                        gs = self.state
                    if gs.get("game_state") == "waiting":
                        gx = int((event.pos[0] - self.offset_x) / self.scale_factor)
                        gy = int((event.pos[1] - self.offset_y) / self.scale_factor)
                        if self.play_btn_rect and self.play_btn_rect.collidepoint((gx, gy)):
                            self.send_ready()
            with self.state_lock:
                gs = self.state
            game_state = gs.get("game_state", "waiting")
            if game_state == "playing":
                keys = pygame.key.get_pressed()
                if now_ms - last_move_time > move_delay:
                    dx, dy = 0, 0
                    if keys[pygame.K_w] or keys[pygame.K_UP]:
                        dy = -1
                    elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        dy = 1
                    elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        dx = -1
                    elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        dx = 1
                    if dx != 0 or dy != 0:
                        self.send_move(dx, dy)
                        last_move_time = now_ms
            self.game_surface.fill((0, 0, 0))
            if game_state == "waiting":
                self.draw_waiting()
            elif game_state in ("playing",):
                self.draw_game()
            elif game_state in ("game_over", "victory"):
                self.draw_game()
                self.draw_game_over()

            # Escalado suave adaptable a cualquier resolución de pantalla
            superficie_escalada = pygame.transform.smoothscale(self.game_surface, (self.render_w, self.render_h))
            self.screen.fill((15, 18, 30))
            self.screen.blit(superficie_escalada, (self.offset_x, self.offset_y))
            pygame.display.flip()
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.connected = False
        return "menu"
