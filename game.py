import pygame
import math
import random
import time
import os

from sound_manager import SoundManager

CELL = 40
COLS, ROWS = 17, 13
HUD_H = 60
GAME_W = COLS * CELL
GAME_H = ROWS * CELL + HUD_H
FPS = 60
MAX_LEVEL = 10

CELL_EMPTY = 0
CELL_WALL = 1
CELL_BLOCK = 2

CHARACTERS = {
    "bomberman": {"name": "Bomberman", "color": (255, 255, 255), "accent": (50, 100, 220),
                  "bomb_power": 2, "max_bombs": 1, "speed": 3.0, "desc": "Equilibrado"},
    "fire": {"name": "Fire Starter", "color": (220, 40, 40), "accent": (255, 140, 0),
             "bomb_power": 3, "max_bombs": 1, "speed": 2.7, "desc": "Explosiones largas"},
    "speed": {"name": "Speed Demon", "color": (0, 200, 200), "accent": (34, 139, 34),
              "bomb_power": 1, "max_bombs": 1, "speed": 3.8, "desc": "Velocidad extrema"},
    "tank": {"name": "Tank", "color": (80, 80, 80), "accent": (139, 90, 43),
             "bomb_power": 2, "max_bombs": 3, "speed": 2.4, "desc": "Multiples bombas"},
}

ENEMY_TYPES = {
    "balloom": {"name": "Globo", "hp": 1, "speed": 1.2, "score": 100, "color": (230, 80, 80), "chase_chance": 0.30, "pass_blocks": False, "sprite_file": "enemigo_balloom.png"},
    "oneal": {"name": "Gota Azul", "hp": 1, "speed": 1.6, "score": 200, "color": (80, 180, 240), "chase_chance": 0.55, "pass_blocks": False, "sprite_file": "enemigo_oneal.png"},
    "doll": {"name": "Barril", "hp": 1, "speed": 1.8, "score": 300, "color": (190, 40, 80), "chase_chance": 0.65, "pass_blocks": False, "sprite_file": "enemigo_doll.png"},
    "minvo": {"name": "Minvo", "hp": 2, "speed": 2.1, "score": 400, "color": (240, 100, 80), "chase_chance": 0.80, "pass_blocks": False, "sprite_file": "enemigo_minvo.png"},
    "fantasma": {"name": "Fantasma", "hp": 1, "speed": 1.9, "score": 500, "color": (210, 30, 90), "chase_chance": 0.85, "pass_blocks": True, "sprite_file": "enemigo_fantasma.png"},
    "ovapi": {"name": "Masa Celeste", "hp": 1, "speed": 1.7, "score": 600, "color": (70, 200, 255), "chase_chance": 0.70, "pass_blocks": True, "sprite_file": "enemigo_ovapi.png"},
    "pass": {"name": "Fiera", "hp": 2, "speed": 2.4, "score": 700, "color": (240, 120, 110), "chase_chance": 0.90, "pass_blocks": False, "sprite_file": "enemigo_pass.png"},
    "pontan": {"name": "Pontan", "hp": 2, "speed": 2.5, "score": 800, "color": (240, 80, 80), "chase_chance": 0.95, "pass_blocks": True, "sprite_file": "enemigo_pontan.png"},
}

POWERUP_TYPES = ["bomb_up", "fire_up", "speed_up", "shield"]

WALL_COLOR = (80, 80, 100)
BLOCK_COLOR = (180, 140, 60)
BLOCK_COLOR2 = (160, 120, 50)
FLOOR_COLOR = (40, 50, 30)
FLOOR_COLOR2 = (35, 45, 25)
BOMB_COLOR = (30, 30, 30)
EXPLOSION_COLOR = (255, 120, 0)
EXPLOSION_COLOR2 = (255, 200, 50)


def generate_world(level, player_positions):
    grid = [[CELL_EMPTY] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            if r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1:
                grid[r][c] = CELL_WALL
            elif r % 2 == 0 and c % 2 == 0:
                grid[r][c] = CELL_WALL

    # Zona segura para cada jugador: su casilla y casillas adyacentes NUNCA tendrán ladrillos
    safe = set()
    for px, py in player_positions:
        px_c = int(px) // CELL
        py_c = int(py - HUD_H) // CELL
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = py_c + dr, px_c + dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    safe.add((nr, nc))

    # Esquinas de spawn clásicas protegidas siempre (evita bloqueos en cualquier modo)
    corner_spawns = [
        (1, 1), (1, 2), (2, 1),
        (1, COLS - 2), (1, COLS - 3), (2, COLS - 2),
        (ROWS - 2, 1), (ROWS - 3, 1), (ROWS - 2, 2),
        (ROWS - 2, COLS - 2), (ROWS - 3, COLS - 2), (ROWS - 2, COLS - 3)
    ]
    for cr, cc in corner_spawns:
        safe.add((cr, cc))

    density = min(0.68, 0.52 + level * 0.02)
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == CELL_EMPTY and (r, c) not in safe:
                if random.random() < density:
                    grid[r][c] = CELL_BLOCK

    # Garantía absoluta: las casillas de los jugadores siempre libres
    for px, py in player_positions:
        pc = int(px) // CELL
        pr = int(py - HUD_H) // CELL
        if 0 <= pr < ROWS and 0 <= pc < COLS:
            grid[pr][pc] = CELL_EMPTY

    return grid


def spawn_enemies(level, grid, player_positions):
    enemies = []
    count = min(3 + level * 2, 16)
    available = []

    # Progresión de tipos de enemigos según el nivel
    if level == 1:
        types_unlocked = ["balloom"]
    elif level == 2:
        types_unlocked = ["balloom", "oneal", "doll"]
    elif level == 3:
        # Nivel 3 en adelante: aparecen enemigos que traspasan ladrillos
        types_unlocked = ["oneal", "doll", "fantasma", "ovapi"]
    elif level == 4:
        types_unlocked = ["minvo", "fantasma", "ovapi", "pass"]
    else:
        # Nivel 5 en adelante: máxima agresividad y velocidad
        types_unlocked = ["fantasma", "ovapi", "pass", "pontan"]

    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == CELL_EMPTY:
                too_close = False
                for px, py in player_positions:
                    if abs(c * CELL + CELL // 2 - px) < CELL * 3 and abs(r * CELL + CELL // 2 + HUD_H - py) < CELL * 3:
                        too_close = True
                        break
                if not too_close:
                    available.append((r, c))

    random.shuffle(available)
    speed_boost = 1.0 + (level - 1) * 0.10
    chase_boost = min(0.35, (level - 1) * 0.08)

    for i in range(min(count, len(available))):
        r, c = available[i]
        etype = random.choice(types_unlocked)
        info = ENEMY_TYPES[etype]
        # Fantasmas y masas celestes siempre traspasan ladrillos; otros pueden adquirirlo en niveles 4+
        can_pass = info["pass_blocks"] or (level >= 4 and random.random() < 0.25)
        enemies.append({
            "x": float(c * CELL + CELL // 2),
            "y": float(r * CELL + CELL // 2 + HUD_H),
            "target_x": float(c * CELL + CELL // 2),
            "target_y": float(r * CELL + CELL // 2 + HUD_H),
            "type": etype,
            "hp": info["hp"],
            "speed": info["speed"] * speed_boost,
            "score": info["score"],
            "color": info["color"],
            "dir": random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]),
            "move_timer": 0,
            "chase_chance": min(0.98, info["chase_chance"] + chase_boost),
            "pass_blocks": can_pass,
        })
    return enemies


def spawn_powerup(x, y):
    return {
        "x": x, "y": y,
        "type": random.choice(POWERUP_TYPES),
        "timer": 0,
    }


class LevelUpMenu:
    def __init__(self, player):
        self.active = False
        self.options = []
        self.selected = 0
        self.player = player
        self.generate()

    def generate(self):
        pool = []
        if self.player["bombs_max"] < 8:
            pool.append(("bomb_up", "+1 Bomba", (255, 140, 0)))
        if self.player["fire_power"] < 8:
            pool.append(("fire_up", "+1 Fuego", (255, 69, 0)))
        if self.player["speed"] < 4.8:
            pool.append(("speed_up", "+1 Velocidad", (0, 200, 200)))
        if self.player["lives"] < 5:
            pool.append(("life", "+1 Vida", (46, 213, 115)))
        if not pool:
            pool.append(("shield", "Escudo 5s", (100, 200, 255)))
            pool.append(("score", "+1000 Pts", (255, 215, 0)))
        random.shuffle(pool)
        self.options = pool[:3]
        self.selected = 0

    def handle_input(self, event):
        if not self.active:
            return None
        if not self.options:
            self.active = False
            return "done"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected = (self.selected - 1) % len(self.options)
                return "hover"
            elif event.key == pygame.K_RIGHT:
                self.selected = (self.selected + 1) % len(self.options)
                return "hover"
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.select()
            elif event.key == pygame.K_ESCAPE:
                self.active = False
                return "done"
        return None

    def select(self):
        if not self.options:
            self.active = False
            return "done"
        self.selected = max(0, min(len(self.options) - 1, self.selected))
        ptype, _, _ = self.options[self.selected]
        if ptype == "bomb_up":
            self.player["bombs_max"] = min(8, self.player["bombs_max"] + 1)
        elif ptype == "fire_up":
            self.player["fire_power"] = min(8, self.player["fire_power"] + 1)
        elif ptype == "speed_up":
            self.player["speed"] = min(4.8, self.player["speed"] + 0.3)
        elif ptype == "life":
            self.player["lives"] = min(5, self.player["lives"] + 1)
        elif ptype == "shield":
            self.player["shield_timer"] = 300
        elif ptype == "score":
            self.player["score"] = self.player.get("score", 0) + 1000
        self.active = False
        return ptype

    def draw(self, surface, font_big, font_med, font_small):
        if not self.active:
            return
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        box_w, box_h = 500, 260
        bx = (GAME_W - box_w) // 2
        by = (GAME_H - box_h) // 2
        pygame.draw.rect(surface, (20, 25, 50), (bx, by, box_w, box_h), border_radius=16)
        pygame.draw.rect(surface, (0, 212, 255), (bx, by, box_w, box_h), 3, border_radius=16)
        title = font_big.render("LEVEL UP!", True, (255, 215, 0))
        surface.blit(title, title.get_rect(center=(GAME_W // 2, by + 40)))
        subtitle = font_small.render("Elige una mejora:", True, (180, 180, 200))
        surface.blit(subtitle, subtitle.get_rect(center=(GAME_W // 2, by + 75)))
        card_w = 130
        card_h = 120
        gap = 20
        total_w = len(self.options) * card_w + (len(self.options) - 1) * gap
        start_x = (GAME_W - total_w) // 2
        for i, (ptype, label, color) in enumerate(self.options):
            cx = start_x + i * (card_w + gap)
            cy = by + 100
            selected = i == self.selected
            rect = pygame.Rect(cx, cy, card_w, card_h)
            bg = (40, 45, 70) if selected else (30, 33, 50)
            pygame.draw.rect(surface, bg, rect, border_radius=10)
            bcolor = color if selected else (100, 100, 120)
            bw = 3 if selected else 1
            pygame.draw.rect(surface, bcolor, rect, bw, border_radius=10)
            icon_color = color
            if ptype == "bomb_up":
                pygame.draw.circle(surface, icon_color, (cx + card_w // 2, cy + 35), 18)
                pygame.draw.circle(surface, (255, 255, 255), (cx + card_w // 2, cy + 35), 18, 2)
                txt = font_med.render("B", True, (255, 255, 255))
                surface.blit(txt, txt.get_rect(center=(cx + card_w // 2, cy + 35)))
            elif ptype == "fire_up":
                pts = [(cx + card_w // 2, cy + 15), (cx + card_w // 2 - 15, cy + 55),
                       (cx + card_w // 2 + 15, cy + 55)]
                pygame.draw.polygon(surface, (255, 69, 0), pts)
                pts2 = [(cx + card_w // 2, cy + 25), (cx + card_w // 2 - 8, cy + 50),
                        (cx + card_w // 2 + 8, cy + 50)]
                pygame.draw.polygon(surface, (255, 200, 0), pts2)
            elif ptype == "speed_up":
                arrow_pts = [(cx + card_w // 2 + 20, cy + 35), (cx + card_w // 2 - 10, cy + 20),
                             (cx + card_w // 2 - 10, cy + 50)]
                pygame.draw.polygon(surface, icon_color, arrow_pts)
            elif ptype == "life":
                hx, hy = cx + card_w // 2, cy + 35
                pts = [(hx, hy - 12), (hx + 14, hy - 4), (hx + 8, hy + 12),
                       (hx, hy + 6), (hx - 8, hy + 12), (hx - 14, hy - 4)]
                pygame.draw.polygon(surface, (46, 213, 115), pts)
            lt = font_small.render(label, True, WHITE if selected else (150, 150, 170))
            surface.blit(lt, lt.get_rect(center=(cx + card_w // 2, cy + card_h - 20)))
            if selected:
                sel = font_small.render(">>", True, (255, 215, 0))
                surface.blit(sel, sel.get_rect(center=(cx + card_w // 2, cy - 10)))
        hint = font_small.render("FLECHAS = Elegir | ENTER = Confirmar", True, (100, 100, 120))
        surface.blit(hint, hint.get_rect(center=(GAME_W // 2, by + box_h + 20)))


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_BLUE = (0, 212, 255)
GOLD = (255, 215, 0)
RED = (255, 71, 87)
GREEN = (46, 213, 115)


class Game:
    def __init__(self, modo="single", char_keys=None, screen=None):
        self.modo = modo
        self.char_keys = char_keys or ["bomberman"]
        self.screen = screen
        self.game_surface = None
        self.clock = None
        self.font_big = None
        self.font_med = None
        self.font_small = None
        self.sound = SoundManager()
        self.state = "playing"
        self.level = 1
        self.score = 0
        self.grid = []
        self.players = []
        self.enemies = []
        self.bombs = []
        self.explosions = []
        self.powerups = []
        self.level_up_menu = None
        self.level_transition = 0
        self.death_timer = 0
        self.frame = 0.0
        self.keys_pressed = set()
        self._step_sound_timer = 0
        self.fullscreen = True
        self.render_w = GAME_W
        self.render_h = GAME_H
        self.offset_x = 0
        self.offset_y = 0
        self.scale_factor = 1.0
        self.player_sprites_game = {}
        self.enemy_sprites = {}
        self.door_cell = (0, 0)
        self.door_revealed = False
        self.door_open = False
        self.door_notification_timer = 0
        self.door_notification_text = ""
        self.door_unlocked_sound_played = False

    def _init_sprites(self):
        base_h = int(CELL * 1.35)
        base_w = max(1, int(base_h * (230.0 / 485.0)))
        sprite_map = {
            "bomberman": "personaje_3d_bomberman.png",
            "fire": "personaje_3d_fuego.png",
            "fuego": "personaje_3d_fuego.png",
            "speed": "personaje_3d_velocidad.png",
            "velocidad": "personaje_3d_velocidad.png",
            "tank": "personaje_3d_tanque.png",
            "tanque": "personaje_3d_tanque.png",
        }
        for k, fname in sprite_map.items():
            path = fname if os.path.exists(fname) else os.path.join("recursos", fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.player_sprites_game[k] = pygame.transform.smoothscale(img, (base_w, base_h))
                except Exception:
                    pass

        # Cargar los 8 sprites de enemigos reales
        esize = int(CELL * 0.85)
        for etype, einfo in ENEMY_TYPES.items():
            fname = einfo.get("sprite_file", f"enemigo_{etype}.png")
            path = fname if os.path.exists(fname) else os.path.join("recursos", fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.enemy_sprites[etype] = pygame.transform.smoothscale(img, (esize, esize))
                except Exception:
                    pass

    def update_scale_and_offsets(self):
        cur_w, cur_h = self.screen.get_size()
        self.screen_w = cur_w
        self.screen_h = cur_h
        scale = min(cur_w / float(GAME_W), cur_h / float(GAME_H))
        self.render_w = max(1, int(GAME_W * scale))
        self.render_h = max(1, int(GAME_H * scale))
        self.offset_x = (cur_w - self.render_w) // 2
        self.offset_y = (cur_h - self.render_h) // 2
        self.scale_factor = scale

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
        self.update_scale_and_offsets()

    def init_display(self):
        if self.screen is None:
            pygame.init()
            info = pygame.display.Info()
            self.screen_w = info.current_w
            self.screen_h = info.current_h
            self.fullscreen = True
            self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), pygame.FULLSCREEN)
        else:
            self.fullscreen = bool(self.screen.get_flags() & pygame.FULLSCREEN)
            self.screen_w, self.screen_h = self.screen.get_size()

        self.game_surface = pygame.Surface((GAME_W, GAME_H))
        self.update_scale_and_offsets()
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)
        self._init_sprites()
        pygame.display.set_caption("Bomberman")

    def make_player(self, index, char_key):
        ch = CHARACTERS[char_key]
        spawn_positions = [
            (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            (CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
        ]
        sx, sy = spawn_positions[index % len(spawn_positions)]
        return {
            "x": sx, "y": sy,
            "speed": ch["speed"],
            "fire_power": ch["bomb_power"],
            "bombs_max": ch["max_bombs"],
            "bombs_active": 0,
            "lives": 3,
            "color": ch["color"],
            "accent": ch["accent"],
            "name": ch["name"],
            "char_key": char_key,
            "invuln_timer": 0,
            "shield_timer": 0,
            "score": 0,
            "alive": True,
            "dx": 0, "dy": 1,
        }

    def reset_player_positions(self):
        spawn_positions = [
            (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            (CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
        ]
        for i, p in enumerate(self.players):
            sx, sy = spawn_positions[i % len(spawn_positions)]
            p["x"] = float(sx)
            p["y"] = float(sy)
            p["target_x"] = float(sx)
            p["target_y"] = float(sy)
            p["dx"] = 0
            p["dy"] = 1
            p["bombs_active"] = 0
            p["invuln_timer"] = 60

    def start_level(self):
        self.bombs.clear()
        self.explosions.clear()
        self.powerups.clear()
        self.level_up_menu = None
        self.reset_player_positions()
        positions = [(p["x"], p["y"]) for p in self.players]
        self.grid = generate_world(self.level, positions)
        self.enemies = spawn_enemies(self.level, self.grid, positions)

        # Ocultar la puerta de salida bajo un bloque de ladrillos aleatorio
        blocks = [(r, c) for r in range(ROWS) for c in range(COLS) if self.grid[r][c] == CELL_BLOCK]
        if blocks:
            self.door_cell = random.choice(blocks)
        else:
            self.door_cell = (ROWS // 2, COLS // 2)
        self.door_revealed = False
        self.door_open = False
        self.door_unlocked_sound_played = False

        if self.level == 1:
            self.door_notification_text = "¡NIVEL 1! Destruye ladrillos para encontrar la puerta secreta."
        elif self.level == 3:
            self.door_notification_text = "¡CUIDADO! Aparecen enemigos que traspasan los ladrillos."
        elif self.level >= 5:
            self.door_notification_text = f"¡NIVEL {self.level}! Máxima dificultad. ¡Halla la salida!"
        else:
            self.door_notification_text = f"¡NIVEL {self.level}! Encuentra la puerta oculta bajo los ladrillos."
        self.door_notification_timer = 200

    def init_game(self):
        self.players.clear()
        for i, ck in enumerate(self.char_keys):
            self.players.append(self.make_player(i, ck))
        self.level = 1
        self.score = 0
        self.start_level()

    def place_bomb(self, player):
        if player["bombs_active"] >= player["bombs_max"]:
            return
        bx = int(player["x"]) // CELL * CELL + CELL // 2
        by = int(player["y"] - HUD_H) // CELL * CELL + CELL // 2 + HUD_H
        for b in self.bombs:
            if b["x"] == bx and b["y"] == by:
                return
        self.bombs.append({
            "x": bx, "y": by,
            "power": player["fire_power"],
            "timer": 180,
            "owner": player,
        })
        player["bombs_active"] += 1
        self.sound.play('bomb_place')

    def explode_bomb(self, bomb):
        owner = bomb["owner"]
        if owner:
            owner["bombs_active"] = max(0, owner["bombs_active"] - 1)
        power = bomb["power"]
        bx = int(bomb["x"]) // CELL
        by = int(bomb["y"] - HUD_H) // CELL
        cells = [(bx, by)]
        if 0 <= bx < COLS and 0 <= by < ROWS and self.grid[by][bx] == CELL_BLOCK:
            self.grid[by][bx] = CELL_EMPTY
            if (by, bx) == self.door_cell:
                self.door_revealed = True
                self.sound.play('powerup')
                if len(self.enemies) == 0:
                    self.door_notification_text = "¡PUERTA ENCONTRADA Y ABIERTA! ¡ENTRA PARA AVANZAR!"
                else:
                    self.door_notification_text = f"¡PUERTA ENCONTRADA! Elimina a los {len(self.enemies)} enemigos para abrirla."
                self.door_notification_timer = 200
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for i in range(1, power + 1):
                nx, ny = bx + dx * i, by + dy * i
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if self.grid[ny][nx] == CELL_WALL:
                        break
                    cells.append((nx, ny))
                    if self.grid[ny][nx] == CELL_BLOCK:
                        self.grid[ny][nx] = CELL_EMPTY
                        # ¿Estaba aquí la puerta oculta?
                        if (ny, nx) == self.door_cell:
                            self.door_revealed = True
                            self.sound.play('powerup')
                            if len(self.enemies) == 0:
                                self.door_notification_text = "¡PUERTA ENCONTRADA Y ABIERTA! ¡ENTRA PARA AVANZAR!"
                            else:
                                self.door_notification_text = f"¡PUERTA ENCONTRADA! Elimina a los {len(self.enemies)} enemigos para abrirla."
                            self.door_notification_timer = 200
                        elif random.random() < 0.25:
                            self.powerups.append(spawn_powerup(
                                nx * CELL + CELL // 2,
                                ny * CELL + CELL // 2 + HUD_H))
                        break
                else:
                    break
        for cx, cy in cells:
            self.explosions.append({
                "x": cx * CELL + CELL // 2,
                "y": cy * CELL + CELL // 2 + HUD_H,
                "timer": 20,
            })
        self.sound.play('explosion')

    def update_bombs(self):
        new_bombs = []
        for b in self.bombs:
            b["timer"] -= 1
            if b["timer"] <= 0:
                self.explode_bomb(b)
            else:
                new_bombs.append(b)
        self.bombs = new_bombs

    def update_explosions(self):
        new_exp = []
        for e in self.explosions:
            e["timer"] -= 1
            if e["timer"] > 0:
                new_exp.append(e)
        self.explosions = new_exp

    def update_enemies(self):
        alive_players = [p for p in self.players if p["alive"]]
        for e in self.enemies:
            # Velocidad de movimiento suave por fotograma (calibrada para 60-120 FPS)
            step = max(0.5, e["speed"] * 0.95)

            # Inicializar destino si no existe
            if "target_x" not in e or "target_y" not in e:
                e["target_x"] = float(e["x"])
                e["target_y"] = float(e["y"])

            dist_to_target = math.hypot(e["target_x"] - e["x"], e["target_y"] - e["y"])
            if dist_to_target <= step:
                e["x"] = e["target_x"]
                e["y"] = e["target_y"]

                # Coordenadas de celda actual
                cur_c = int(round((e["x"] - CELL // 2) / CELL))
                cur_r = int(round((e["y"] - HUD_H - CELL // 2) / CELL))
                cur_c = max(1, min(COLS - 2, cur_c))
                cur_r = max(1, min(ROWS - 2, cur_r))

                # Evaluar las 4 direcciones posibles
                valid_dirs = []
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nc = cur_c + dx
                    nr = cur_r + dy
                    if 0 <= nc < COLS and 0 <= nr < ROWS:
                        # Pared indestructible siempre bloquea
                        if self.grid[nr][nc] == CELL_WALL:
                            continue
                        # Ladrillo bloquea si el enemigo NO traspasa bloques
                        if self.grid[nr][nc] == CELL_BLOCK and not e.get("pass_blocks", False):
                            continue
                        # Bombas activas bloquean el paso (a menos que traspase bloques)
                        bomb_at_dest = any(int(b["x"]) // CELL == nc and int(b["y"] - HUD_H) // CELL == nr for b in self.bombs)
                        if bomb_at_dest and not e.get("pass_blocks", False):
                            continue
                        valid_dirs.append((dx, dy))

                if not valid_dirs:
                    continue

                # Persecución inteligente del jugador más cercano
                target_p = None
                if alive_players:
                    target_p = min(alive_players, key=lambda p: (p["x"] - e["x"])**2 + (p["y"] - e["y"])**2)

                chosen_dir = None
                if target_p and random.random() < e.get("chase_chance", 0.4):
                    def dist_score(d):
                        next_x = (cur_c + d[0]) * CELL + CELL // 2
                        next_y = (cur_r + d[1]) * CELL + CELL // 2 + HUD_H
                        return (next_x - target_p["x"])**2 + (next_y - target_p["y"])**2

                    valid_dirs.sort(key=dist_score)
                    chosen_dir = valid_dirs[0]
                else:
                    cur_dir_tuple = tuple(e.get("dir", (1, 0)))
                    if cur_dir_tuple in valid_dirs and random.random() < 0.65:
                        chosen_dir = cur_dir_tuple
                    else:
                        chosen_dir = random.choice(valid_dirs)

                e["dir"] = list(chosen_dir)
                e["target_x"] = float((cur_c + chosen_dir[0]) * CELL + CELL // 2)
                e["target_y"] = float((cur_r + chosen_dir[1]) * CELL + CELL // 2 + HUD_H)
            else:
                # Desplazamiento fluido continuo hacia la celda objetivo
                dir_x = e["target_x"] - e["x"]
                dir_y = e["target_y"] - e["y"]
                if abs(dir_x) <= step:
                    e["x"] = e["target_x"]
                else:
                    e["x"] += math.copysign(step, dir_x)
                if abs(dir_y) <= step:
                    e["y"] = e["target_y"]
                else:
                    e["y"] += math.copysign(step, dir_y)

    def check_collisions(self):
        for p in self.players:
            if not p["alive"]:
                continue
            if p["invuln_timer"] > 0:
                p["invuln_timer"] -= 1
            if p["shield_timer"] > 0:
                p["shield_timer"] -= 1
            for e in self.enemies[:]:
                if abs(p["x"] - e["x"]) < CELL * 0.6 and abs(p["y"] - e["y"]) < CELL * 0.6:
                    if p["shield_timer"] <= 0 and p["invuln_timer"] <= 0:
                        p["lives"] -= 1
                        self.sound.play('hurt')
                        if p["lives"] <= 0:
                            p["alive"] = False
                            self.sound.play('death')
                        else:
                            p["invuln_timer"] = 120
                            sx = (CELL + CELL // 2) if self.players.index(p) == 0 else (
                                COLS - 2) * CELL + CELL // 2
                            sy = CELL + CELL // 2 + HUD_H
                            p["x"], p["y"] = sx, sy
            for exp in self.explosions:
                if abs(p["x"] - exp["x"]) < CELL * 0.6 and abs(p["y"] - exp["y"]) < CELL * 0.6:
                    if p["shield_timer"] <= 0 and p["invuln_timer"] <= 0:
                        p["lives"] -= 1
                        self.sound.play('hurt')
                        if p["lives"] <= 0:
                            p["alive"] = False
                            self.sound.play('death')
                        else:
                            p["invuln_timer"] = 120
                            sx = (CELL + CELL // 2) if self.players.index(p) == 0 else (
                                COLS - 2) * CELL + CELL // 2
                            sy = CELL + CELL // 2 + HUD_H
                            p["x"], p["y"] = sx, sy
        for e in self.enemies[:]:
            for exp in self.explosions:
                if abs(e["x"] - exp["x"]) < CELL * 0.6 and abs(e["y"] - exp["y"]) < CELL * 0.6:
                    e["hp"] -= 1
                    if e["hp"] <= 0:
                        self.enemies.remove(e)
                        self.score += e["score"]
                        for p in self.players:
                            if p["alive"]:
                                p["score"] += e["score"]
                        if self.modo == "single" and self.players and self.players[0]["alive"]:
                            self.level_up_menu = LevelUpMenu(self.players[0])
                            if self.level_up_menu.options:
                                self.level_up_menu.active = True
                                self.state = "level_up"
                        break

    def check_powerups(self):
        for p in self.players:
            if not p["alive"]:
                continue
            for pu in self.powerups[:]:
                if abs(p["x"] - pu["x"]) < CELL * 0.6 and abs(p["y"] - pu["y"]) < CELL * 0.6:
                    if pu["type"] == "bomb_up":
                        p["bombs_max"] = min(8, p["bombs_max"] + 1)
                    elif pu["type"] == "fire_up":
                        p["fire_power"] = min(8, p["fire_power"] + 1)
                    elif pu["type"] == "speed_up":
                        p["speed"] = min(4.8, p["speed"] + 0.3)
                    elif pu["type"] == "shield":
                        p["shield_timer"] = 300
                    self.powerups.remove(pu)
                    self.sound.play('powerup')

    def move_player(self, player, dx, dy):
        if not player["alive"]:
            return
        player["dx"] = dx
        player["dy"] = dy

        # Velocidad calibrada en píxeles por fotograma
        speed = player["speed"] * (60.0 / FPS)
        r = 10  # Caja de colisión óptima (20x20 en casilla de 40x40 para no trabarse en muros)

        def is_free(tx, ty):
            # Límites de la arena
            if (tx - r < CELL or tx + r > (COLS - 1) * CELL or
                    ty - r < HUD_H + CELL or ty + r > HUD_H + (ROWS - 1) * CELL):
                return False
            # 4 esquinas de la caja de colisión contra celdas sólidas
            for ox, oy in [(-r, -r), (r, -r), (-r, r), (r, r)]:
                cx = int(tx + ox) // CELL
                cy = int(ty + oy - HUD_H) // CELL
                if cx < 0 or cx >= COLS or cy < 0 or cy >= ROWS:
                    return False
                if self.grid[cy][cx] != CELL_EMPTY:
                    return False
            # Las bombas no bloquean al jugador para que pueda pasar a través de ellas y nunca quedar atrapado
            return True

        if dx != 0 and dy == 0:
            # --- MOVIMIENTO HORIZONTAL: AUTO-CENTRADO EN LA FILA Y DESLIZAMIENTO DE ESQUINAS ---
            cur_r = int(round((player["y"] - HUD_H - CELL // 2) / CELL))
            cur_r = max(1, min(ROWS - 2, cur_r))
            center_y = cur_r * CELL + CELL // 2 + HUD_H
            diff_y = center_y - player["y"]

            nudge_y = math.copysign(min(abs(diff_y), speed * 0.7), diff_y) if abs(diff_y) > 0.5 else 0.0
            next_x = player["x"] + dx * speed
            next_y = player["y"] + nudge_y

            if is_free(next_x, next_y):
                player["x"] = next_x
                player["y"] = next_y
            elif is_free(next_x, player["y"]):
                player["x"] = next_x
            elif abs(diff_y) > 0.5 and is_free(player["x"] + dx * (speed * 0.5), center_y):
                # Deslizamiento suave en la esquina hacia el centro del pasillo
                player["y"] += math.copysign(min(abs(diff_y), speed), diff_y)
                if is_free(player["x"] + dx * (speed * 0.5), player["y"]):
                    player["x"] += dx * (speed * 0.5)

        elif dy != 0 and dx == 0:
            # --- MOVIMIENTO VERTICAL: AUTO-CENTRADO EN LA COLUMNA Y DESLIZAMIENTO DE ESQUINAS ---
            cur_c = int(round((player["x"] - CELL // 2) / CELL))
            cur_c = max(1, min(COLS - 2, cur_c))
            center_x = cur_c * CELL + CELL // 2
            diff_x = center_x - player["x"]

            nudge_x = math.copysign(min(abs(diff_x), speed * 0.7), diff_x) if abs(diff_x) > 0.5 else 0.0
            next_x = player["x"] + nudge_x
            next_y = player["y"] + dy * speed

            if is_free(next_x, next_y):
                player["x"] = next_x
                player["y"] = next_y
            elif is_free(player["x"], next_y):
                player["y"] = next_y
            elif abs(diff_x) > 0.5 and is_free(center_x, player["y"] + dy * (speed * 0.5)):
                # Deslizamiento suave en la esquina hacia el centro del pasillo
                player["x"] += math.copysign(min(abs(diff_x), speed), diff_x)
                if is_free(player["x"], player["y"] + dy * (speed * 0.5)):
                    player["y"] += dy * (speed * 0.5)

    def handle_input_single(self):
        keys = pygame.key.get_pressed()
        p = self.players[0] if self.players else None
        if not p or not p["alive"]:
            return
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
            self.move_player(p, dx, dy)

    def handle_input_local(self):
        keys = pygame.key.get_pressed()
        if len(self.players) >= 1:
            p1 = self.players[0]
            if p1["alive"]:
                dx, dy = 0, 0
                if keys[pygame.K_w]:
                    dy = -1
                elif keys[pygame.K_s]:
                    dy = 1
                elif keys[pygame.K_a]:
                    dx = -1
                elif keys[pygame.K_d]:
                    dx = 1
                if dx != 0 or dy != 0:
                    self.move_player(p1, dx, dy)
        if len(self.players) >= 2:
            p2 = self.players[1]
            if p2["alive"]:
                dx, dy = 0, 0
                if keys[pygame.K_UP]:
                    dy = -1
                elif keys[pygame.K_DOWN]:
                    dy = 1
                elif keys[pygame.K_LEFT]:
                    dx = -1
                elif keys[pygame.K_RIGHT]:
                    dx = 1
                if dx != 0 or dy != 0:
                    self.move_player(p2, dx, dy)

    def draw_grid(self):
        for r in range(ROWS):
            for c in range(COLS):
                x = c * CELL
                y = r * CELL + HUD_H
                if self.grid[r][c] == CELL_EMPTY:
                    color = FLOOR_COLOR if (r + c) % 2 == 0 else FLOOR_COLOR2
                    pygame.draw.rect(self.game_surface, color, (x, y, CELL, CELL))
                elif self.grid[r][c] == CELL_WALL:
                    pygame.draw.rect(self.game_surface, WALL_COLOR, (x, y, CELL, CELL))
                    pygame.draw.rect(self.game_surface, (60, 60, 80), (x, y, CELL, CELL), 2)
                    pygame.draw.rect(self.game_surface, (100, 100, 120), (x + 2, y + 2, CELL - 4, CELL - 4), 1)
                elif self.grid[r][c] == CELL_BLOCK:
                    color = BLOCK_COLOR if (r + c) % 2 == 0 else BLOCK_COLOR2
                    pygame.draw.rect(self.game_surface, color, (x, y, CELL, CELL))
                    pygame.draw.rect(self.game_surface, (140, 100, 40), (x, y, CELL, CELL), 2)
                    pygame.draw.line(self.game_surface, (120, 80, 30), (x, y + CELL // 2), (x + CELL, y + CELL // 2), 1)

    def draw_bombs(self):
        for b in self.bombs:
            x, y = int(b["x"]), int(b["y"])
            pulse = math.sin(self.frame * 5) * 3
            r = int(CELL * 0.35 + pulse)
            pygame.draw.circle(self.game_surface, BOMB_COLOR, (x, y), r)
            pygame.draw.circle(self.game_surface, (80, 80, 80), (x, y), r, 2)
            fuse_y = y - r
            pygame.draw.line(self.game_surface, (200, 200, 200), (x, fuse_y), (x + 4, fuse_y - 6), 2)
            if b["timer"] < 60:
                if (b["timer"] // 5) % 2 == 0:
                    pygame.draw.circle(self.game_surface, (255, 200, 50), (x + 4, fuse_y - 6), 4)

    def draw_explosions(self):
        for e in self.explosions:
            x, y = int(e["x"]), int(e["y"])
            alpha = e["timer"] / 20.0
            r = int(CELL * 0.5 * alpha + CELL * 0.2)
            color_r = min(255, int(EXPLOSION_COLOR[0] * alpha))
            color_g = min(255, int(EXPLOSION_COLOR[1] * alpha))
            color_b = min(255, int(EXPLOSION_COLOR[2] * alpha))
            color = (color_r, color_g, color_b)
            pygame.draw.circle(self.game_surface, color, (x, y), r)
            color2 = (min(255, int(EXPLOSION_COLOR2[0] * alpha)),
                       min(255, int(EXPLOSION_COLOR2[1] * alpha)),
                       min(255, int(EXPLOSION_COLOR2[2] * alpha)))
            pygame.draw.circle(self.game_surface, color2, (x, y), max(1, r - 4))

    def draw_door(self):
        if not self.door_revealed:
            return
        r, c = self.door_cell
        # Si el ladrillo aún no ha sido destruido, la puerta permanece oculta debajo
        if self.grid[r][c] == CELL_BLOCK:
            return

        dx = c * CELL
        dy = r * CELL + HUD_H
        rect = pygame.Rect(dx, dy, CELL, CELL)

        # Base de piedra / umbral
        pygame.draw.rect(self.game_surface, (25, 20, 38), rect)
        pygame.draw.rect(self.game_surface, (85, 80, 105), rect, 2)

        if self.door_open:
            # --- PUERTA ABIERTA: PORTAL VÓRTICE CÓSMICO ---
            pulse = math.sin(self.frame * 7) * 3
            cx, cy = dx + CELL // 2, dy + CELL // 2

            # Vórtice de energía mística
            pygame.draw.circle(self.game_surface, (15, 35, 75), (cx, cy), int(15 + pulse))
            pygame.draw.circle(self.game_surface, (0, 212, 255), (cx, cy), int(11 + pulse))
            pygame.draw.circle(self.game_surface, (255, 255, 255), (cx, cy), int(5 + pulse * 0.5))

            # Borde exterior dorado resplandeciente
            pygame.draw.rect(self.game_surface, GOLD, rect, 2, border_radius=4)

            # Flecha indicadora flotante
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
            # --- PUERTA CERRADA: REJA DE HIERRO CON CANDADO DORADO ---
            pygame.draw.rect(self.game_surface, (35, 30, 42), (dx + 4, dy + 4, CELL - 8, CELL - 8))

            # Barrotes de hierro verticales
            for bar_x in range(dx + 8, dx + CELL - 6, 6):
                pygame.draw.line(self.game_surface, (130, 130, 145), (bar_x, dy + 5), (bar_x, dy + CELL - 5), 2)

            cx, cy = dx + CELL // 2, dy + CELL // 2
            # Grillete del candado
            pygame.draw.arc(self.game_surface, GOLD, (cx - 6, cy - 10, 12, 10), 0, 3.14159, 2)
            # Cuerpo del candado
            pygame.draw.rect(self.game_surface, (230, 180, 0), (cx - 7, cy - 3, 14, 11), border_radius=2)
            pygame.draw.circle(self.game_surface, (40, 30, 10), (cx, cy + 2), 2)

    def draw_notifications(self):
        if self.door_notification_timer > 0 and self.door_notification_text:
            self.door_notification_timer -= 1
            banner_w = min(GAME_W - 40, max(280, len(self.door_notification_text) * 8 + 36))
            banner_h = 32
            bx = (GAME_W - banner_w) // 2
            by = HUD_H + 6

            surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            surf.fill((12, 16, 32, 225))
            bcolor = GOLD if self.door_open else NEON_BLUE
            pygame.draw.rect(surf, bcolor, (0, 0, banner_w, banner_h), 2, border_radius=8)
            self.game_surface.blit(surf, (bx, by))

            txt = self.font_small.render(self.door_notification_text, True, WHITE)
            self.game_surface.blit(txt, txt.get_rect(center=(GAME_W // 2, by + banner_h // 2)))

    def draw_enemies(self):
        for e in self.enemies:
            x, y = int(e["x"]), int(e["y"])
            etype = e.get("type", "balloom")
            spr = self.enemy_sprites.get(etype)

            # Aura fantasmal pulsante para enemigos que traspasan bloques
            if e.get("pass_blocks", False):
                aura_alpha = int(130 + 60 * math.sin(self.frame * 7 + x))
                aura_surf = pygame.Surface((CELL + 10, CELL + 10), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (170, 60, 250, aura_alpha // 2), (CELL // 2 + 5, CELL // 2 + 5), int(CELL * 0.44))
                pygame.draw.circle(aura_surf, (210, 120, 255, aura_alpha), (CELL // 2 + 5, CELL // 2 + 5), int(CELL * 0.44), 2)
                self.game_surface.blit(aura_surf, (x - CELL // 2 - 5, y - CELL // 2 - 5))

            if spr:
                # Voltear horizontalmente si se mueve hacia la izquierda
                spr_draw = spr
                if e.get("dir", [1, 0])[0] < 0:
                    spr_draw = pygame.transform.flip(spr, True, False)

                cur_c = int(e["x"]) // CELL
                cur_r = int(e["y"] - HUD_H) // CELL
                dentro_bloque = (0 <= cur_r < ROWS and 0 <= cur_c < COLS and self.grid[cur_r][cur_c] == CELL_BLOCK)

                if dentro_bloque and e.get("pass_blocks", False):
                    spr_trans = spr_draw.copy()
                    spr_trans.set_alpha(180)
                    self.game_surface.blit(spr_trans, spr_trans.get_rect(center=(x, y)))
                else:
                    self.game_surface.blit(spr_draw, spr_draw.get_rect(center=(x, y)))
            else:
                r = int(CELL * 0.35)
                pygame.draw.circle(self.game_surface, e["color"], (x, y), r)
                pygame.draw.circle(self.game_surface, (255, 255, 255), (x, y), r, 2)
                ex = x + e.get("dir", [1, 0])[0] * 4
                ey = y + e.get("dir", [0, 1])[1] * 4 - 2
                pygame.draw.circle(self.game_surface, BLACK, (int(ex - 4), int(ey)), 3)
                pygame.draw.circle(self.game_surface, BLACK, (int(ex + 4), int(ey)), 3)

            if e["hp"] > 1:
                hp_text = self.font_small.render(f"♥{e['hp']}", True, (255, 90, 90))
                self.game_surface.blit(hp_text, hp_text.get_rect(center=(x, y - int(CELL * 0.45))))

    def draw_powerups(self):
        for pu in self.powerups:
            x, y = int(pu["x"]), int(pu["y"])
            bob = math.sin(self.frame * 3 + x) * 3
            ry = int(y + bob)
            colors = {
                "bomb_up": (255, 140, 0),
                "fire_up": (255, 69, 0),
                "speed_up": (0, 200, 200),
                "shield": (100, 200, 255),
            }
            color = colors.get(pu["type"], WHITE)
            pygame.draw.rect(self.game_surface, color, (x - 12, ry - 12, 24, 24), border_radius=6)
            pygame.draw.rect(self.game_surface, WHITE, (x - 12, ry - 12, 24, 24), 2, border_radius=6)
            labels = {"bomb_up": "B", "fire_up": "F", "speed_up": "S", "shield": "E"}
            lt = self.font_small.render(labels.get(pu["type"], "?"), True, WHITE)
            self.game_surface.blit(lt, lt.get_rect(center=(x, ry)))

    def draw_players(self):
        for i, p in enumerate(self.players):
            if not p["alive"]:
                continue
            x, y = int(p["x"]), int(p["y"])
            if p["invuln_timer"] > 0 and (p["invuln_timer"] // 4) % 2 == 0:
                continue

            char_key = p.get("char_key", "bomberman")
            sprite = self.player_sprites_game.get(char_key, self.player_sprites_game.get("bomberman"))

            # Sombra 3D suave en el suelo
            sombra = pygame.Surface((28, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(sombra, (0, 0, 0, 110), (0, 0, 28, 10))
            self.game_surface.blit(sombra, (x - 14, y + 10))

            # Efecto de escudo activo
            if p["shield_timer"] > 0:
                shield_alpha = int(140 + 60 * math.sin(self.frame * 5))
                escudo_surf = pygame.Surface((56, 56), pygame.SRCALPHA)
                pygame.draw.circle(escudo_surf, (0, 212, 255, shield_alpha // 3), (28, 28), 24)
                pygame.draw.circle(escudo_surf, (0, 212, 255, shield_alpha), (28, 28), 24, 2)
                self.game_surface.blit(escudo_surf, (x - 28, y - 28))

            if sprite:
                # Animación de pasos (rebote suave) si se está moviendo
                moviendose = (p.get("dx", 0) != 0 or p.get("dy", 0) != 0)
                rebote = int(abs(math.sin(self.frame * 8)) * 3) if moviendose else 0

                # Orientación horizontal (espejo si mira a la izquierda)
                sprite_orientado = sprite
                if p.get("dx", 0) < 0:
                    sprite_orientado = pygame.transform.flip(sprite, True, False)

                rect_spr = sprite_orientado.get_rect(center=(x, y - 6 - rebote))
                self.game_surface.blit(sprite_orientado, rect_spr)
            else:
                # Fallback gráfico básico
                r = int(CELL * 0.38)
                body_color = p["color"]
                pygame.draw.circle(self.game_surface, body_color, (x, y), r)
                pygame.draw.circle(self.game_surface, p["accent"], (x, y), r, 2)

            # Insignia flotante con el número de jugador
            y_insignia = y - 36
            txt_jugador = self.font_small.render(str(i + 1), True, WHITE)
            fondo_insignia = pygame.Rect(0, 0, txt_jugador.get_width() + 8, txt_jugador.get_height() + 2)
            fondo_insignia.center = (x, y_insignia)
            pygame.draw.rect(self.game_surface, (20, 20, 35, 180), fondo_insignia, border_radius=4)
            pygame.draw.rect(self.game_surface, p.get("accent", (0, 212, 255)), fondo_insignia, 1, border_radius=4)
            self.game_surface.blit(txt_jugador, txt_jugador.get_rect(center=fondo_insignia.center))

    def draw_hud(self):
        pygame.draw.rect(self.game_surface, (15, 18, 35), (0, 0, GAME_W, HUD_H))
        pygame.draw.line(self.game_surface, NEON_BLUE, (0, HUD_H - 1), (GAME_W, HUD_H - 1), 2)
        x = 10
        for i, p in enumerate(self.players):
            prefix = f"P{i + 1}: " if len(self.players) > 1 else ""
            lives_text = self.font_med.render(f"{prefix}HP: {p['lives']}", True, GREEN if p["alive"] else RED)
            self.game_surface.blit(lives_text, (x, 8))
            bombs_text = self.font_small.render(f"Bombas: {p['bombs_max']}", True, (255, 140, 0))
            self.game_surface.blit(bombs_text, (x, 35))
            fire_text = self.font_small.render(f"Fuego: {p['fire_power']}", True, (255, 69, 0))
            self.game_surface.blit(fire_text, (x + 100, 35))
            spd_text = self.font_small.render(f"Vel: {p['speed']:.1f}", True, (0, 200, 200))
            self.game_surface.blit(spd_text, (x + 200, 35))
            x += 320
        lvl_text = self.font_big.render(f"Nivel {self.level}", True, GOLD)
        self.game_surface.blit(lvl_text, lvl_text.get_rect(center=(GAME_W // 2, 18)))
        score_text = self.font_med.render(f"Score: {self.score}", True, WHITE)
        self.game_surface.blit(score_text, score_text.get_rect(center=(GAME_W // 2, 42)))

        enemies_color = GREEN if len(self.enemies) == 0 else RED
        enemies_text = self.font_small.render(f"Enemigos: {len(self.enemies)}", True, enemies_color)
        self.game_surface.blit(enemies_text, (GAME_W - 145, 10))

        if not self.door_revealed:
            door_txt = "Puerta: OCULTA"
            door_col = (170, 170, 185)
        elif not self.door_open:
            door_txt = "Puerta: CERRADA"
            door_col = (255, 150, 50)
        else:
            door_txt = "Puerta: ¡ABIERTA!"
            door_col = GREEN
        txt_puerta = self.font_small.render(door_txt, True, door_col)
        self.game_surface.blit(txt_puerta, (GAME_W - 145, 32))

    def draw_game_over(self):
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.game_surface.blit(overlay, (0, 0))
        title = self.font_big.render("GAME OVER", True, RED)
        self.game_surface.blit(title, title.get_rect(center=(GAME_W // 2, GAME_H // 2 - 60)))
        score_text = self.font_med.render(f"Score Final: {self.score}", True, GOLD)
        self.game_surface.blit(score_text, score_text.get_rect(center=(GAME_W // 2, GAME_H // 2)))
        lvl_text = self.font_med.render(f"Nivel alcanzado: {self.level}", True, WHITE)
        self.game_surface.blit(lvl_text, lvl_text.get_rect(center=(GAME_W // 2, GAME_H // 2 + 40)))
        hint = self.font_small.render("ESC = Volver al menu", True, (150, 150, 170))
        self.game_surface.blit(hint, hint.get_rect(center=(GAME_W // 2, GAME_H // 2 + 90)))

    def draw_victory(self):
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.game_surface.blit(overlay, (0, 0))
        title = self.font_big.render("VICTORIA!", True, GOLD)
        self.game_surface.blit(title, title.get_rect(center=(GAME_W // 2, GAME_H // 2 - 60)))
        score_text = self.font_med.render(f"Score Final: {self.score}", True, WHITE)
        self.game_surface.blit(score_text, score_text.get_rect(center=(GAME_W // 2, GAME_H // 2)))
        hint = self.font_small.render("ESC = Volver al menu", True, (150, 150, 170))
        self.game_surface.blit(hint, hint.get_rect(center=(GAME_W // 2, GAME_H // 2 + 60)))

    def draw_level_transition(self):
        overlay = pygame.Surface((GAME_W, GAME_H), pygame.SRCALPHA)
        alpha = min(255, int(self.level_transition * 4))
        overlay.fill((0, 0, 0, alpha))
        self.game_surface.blit(overlay, (0, 0))
        if self.level_transition > 30:
            txt = self.font_big.render(f"Nivel {self.level}", True, GOLD)
            self.game_surface.blit(txt, txt.get_rect(center=(GAME_W // 2, GAME_H // 2)))
            bonus = self.font_med.render(f"+{self.level * 1000} puntos bonus", True, GREEN)
            self.game_surface.blit(bonus, bonus.get_rect(center=(GAME_W // 2, GAME_H // 2 + 50)))

    def update(self):
        if self.state == "level_up":
            return
        if self.state == "level_transition":
            self.level_transition += 1
            if self.level_transition > 120:
                self.level += 1
                if self.level > MAX_LEVEL:
                    self.state = "victory"
                    self.sound.play('victory')
                    return
                self.score += self.level * 1000
                self.start_level()
                self.state = "playing"
                self.level_transition = 0
            return
        if self.state in ("game_over", "victory"):
            return
        if self.modo == "single" or self.modo == "local":
            if self.modo == "single":
                self.handle_input_single()
            else:
                self.handle_input_local()
        self.update_bombs()
        self.update_explosions()
        self.update_enemies()
        self.check_collisions()
        self.check_powerups()

        all_dead = all(not p["alive"] for p in self.players)
        if all_dead:
            self.state = "game_over"
            self.sound.play('death')
        else:
            # Comprobar si se eliminaron todos los enemigos para abrir la puerta
            if len(self.enemies) == 0 and not self.door_open:
                self.door_open = True
                if not self.door_unlocked_sound_played:
                    self.door_unlocked_sound_played = True
                    self.sound.play('powerup')
                    if self.door_revealed:
                        self.door_notification_text = "¡ENEMIGOS ELIMINADOS! ¡LA PUERTA ESTÁ ABIERTA! ¡ENTRA!"
                    else:
                        self.door_notification_text = "¡ENEMIGOS ELIMINADOS! ¡HALLA LA PUERTA BAJO LOS LADRILLOS!"
                    self.door_notification_timer = 220

            # Comprobar si un jugador pisa la puerta
            if self.door_revealed and self.grid[self.door_cell[0]][self.door_cell[1]] != CELL_BLOCK:
                dr, dc = self.door_cell
                door_x = dc * CELL + CELL // 2
                door_y = dr * CELL + CELL // 2 + HUD_H
                for p in self.players:
                    if p["alive"]:
                        if math.hypot(p["x"] - door_x, p["y"] - door_y) < CELL * 0.55:
                            if self.door_open:
                                # ¡Completó el nivel entrando por la puerta!
                                self.state = "level_transition"
                                self.level_transition = 0
                                self.sound.play('level_up')
                                self.score += self.level * 1000
                                for pl in self.players:
                                    pl["score"] += self.level * 1000
                                break
                            else:
                                if self.door_notification_timer <= 0:
                                    self.door_notification_text = f"¡PUERTA CERRADA! Elimina a los {len(self.enemies)} enemigos restantes"
                                    self.door_notification_timer = 90

    def draw(self):
        self.game_surface.fill((0, 0, 0))
        self.draw_grid()
        self.draw_door()
        self.draw_bombs()
        self.draw_explosions()
        self.draw_enemies()
        self.draw_powerups()
        self.draw_players()
        self.draw_hud()
        self.draw_notifications()

        if self.state == "level_transition":
            self.draw_level_transition()
        elif self.state == "level_up" and self.level_up_menu:
            self.level_up_menu.draw(self.game_surface, self.font_big, self.font_med, self.font_small)
        elif self.state == "game_over":
            self.draw_game_over()
        elif self.state == "victory":
            self.draw_victory()
        # Escalado dinámico y suave para cubrir cualquier resolución de pantalla
        superficie_escalada = pygame.transform.smoothscale(self.game_surface, (self.render_w, self.render_h))
        self.screen.fill((15, 18, 30))
        self.screen.blit(superficie_escalada, (self.offset_x, self.offset_y))

    def run(self):
        self.init_display()
        self.init_game()
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.frame += dt * 3.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.update_scale_and_offsets()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == "game_over" or self.state == "victory":
                            return self.score
                        elif self.state == "level_up":
                            pass
                        else:
                            return self.score
                    elif self.state == "playing":
                        p = self.players[0] if self.players else None
                        if p and p["alive"]:
                            if event.key == pygame.K_SPACE:
                                self.place_bomb(p)
                            if self.modo == "local" and len(self.players) >= 2:
                                p2 = self.players[1]
                                if p2["alive"] and event.key == pygame.K_RETURN:
                                    self.place_bomb(p2)
                    elif self.state == "level_up" and self.level_up_menu:
                        result = self.level_up_menu.handle_input(event)
                        if result and result != "hover":
                            self.state = "playing"
            if self.state == "level_up" and (not self.level_up_menu or not self.level_up_menu.active):
                self.state = "playing"
            self.update()
            self.draw()
            pygame.display.flip()
        return self.score
