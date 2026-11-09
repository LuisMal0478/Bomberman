import os
import sys
import json
import socket
import threading
import random
import time
import math

# Ejecución segura en servidores en la nube sin interfaz gráfica (Headless Linux)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game import (COLS, ROWS, CELL, HUD_H, CELL_EMPTY, CELL_WALL, CELL_BLOCK,
                  CHARACTERS, ENEMY_TYPES, POWERUP_TYPES, MAX_LEVEL,
                  generate_world, spawn_enemies, spawn_powerup)


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


class GameServer:
    def __init__(self, host="0.0.0.0", port=5555, alt_port=None):
        self.host = host
        self.port = port
        self.alt_port = alt_port
        self.server_socket = None
        self.alt_server_socket = None
        self.clients = {}
        self.lock = threading.Lock()
        self.running = False
        self.game_state = "waiting"
        self.level = 1
        self.score = 0
        self.grid = []
        self.players = {}
        self.enemies = []
        self.bombs = []
        self.explosions = []
        self.powerups = []
        self.player_id_counter = 0
        self.frame = 0
        self.door_cell = (0, 0)
        self.door_revealed = False
        self.door_open = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Servidor escuchando en {self.host}:{self.port}")
        accept_thread = threading.Thread(target=self._accept_connections, args=(self.server_socket,), daemon=True)
        accept_thread.start()

        if self.alt_port and self.alt_port != self.port:
            try:
                self.alt_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.alt_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.alt_server_socket.bind((self.host, self.alt_port))
                self.alt_server_socket.listen(5)
                print(f"Servidor escuchando tambien en puerto secundario {self.host}:{self.alt_port}")
                alt_thread = threading.Thread(target=self._accept_connections, args=(self.alt_server_socket,), daemon=True)
                alt_thread.start()
            except Exception as e:
                print(f"Aviso puerto secundario {self.alt_port}: {e}")

        game_thread = threading.Thread(target=self._game_loop, daemon=True)
        game_thread.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            self.server_socket.close()
            if self.alt_server_socket:
                self.alt_server_socket.close()

    def _accept_connections(self, sock):
        while self.running:
            try:
                sock.settimeout(1.0)
                client_socket, addr = sock.accept()
                print(f"Conexion desde {addr}")
                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, addr), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client_socket, addr):
        player_id = None
        buffer = b""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    msg = decode_line(line.decode('utf-8', errors='replace'))
                    if msg is None:
                        continue
                    msg_type = msg.get("type")
                    if msg_type == "join":
                        with self.lock:
                            player_id = self.player_id_counter
                            self.player_id_counter += 1
                            name = msg.get("name", f"J{player_id + 1}")
                            char_key = msg.get("char", "bomberman")
                            if char_key not in CHARACTERS:
                                char_key = "bomberman"
                            ch = CHARACTERS[char_key]
                            spawn_positions = [
                                (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
                                ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
                                (CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
                                ((COLS - 2) * CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
                            ]
                            idx = len(self.players) % len(spawn_positions)
                            sx, sy = spawn_positions[idx]
                            self.players[player_id] = {
                                "id": player_id,
                                "name": name,
                                "char_key": char_key,
                                "x": sx, "y": sy,
                                "speed": ch["speed"],
                                "fire_power": ch["bomb_power"],
                                "bombs_max": ch["max_bombs"],
                                "bombs_active": 0,
                                "lives": 3,
                                "color": list(ch["color"]),
                                "accent": list(ch["accent"]),
                                "alive": True,
                                "invuln_timer": 0,
                                "shield_timer": 0,
                                "score": 0,
                                "dx": 0, "dy": 1,
                            }
                        self.clients[player_id] = (client_socket, addr)
                        client_socket.send(encode({"type": "join_ok", "id": player_id}))
                        self._broadcast_player_join(player_id)
                        print(f"Jugador {name} (ID:{player_id}) se unio")
                        if self.game_state == "playing" and len(self.players) >= 1:
                            self._send_full_state(client_socket, player_id)
                    elif msg_type == "move":
                        if player_id is not None:
                            with self.lock:
                                p = self.players.get(player_id)
                                if p and p["alive"]:
                                    dx = msg.get("dx", 0)
                                    dy = msg.get("dy", 0)
                                    self._move_player(p, dx, dy)
                    elif msg_type == "bomb":
                        if player_id is not None:
                            with self.lock:
                                p = self.players.get(player_id)
                                if p and p["alive"]:
                                    self._place_bomb(p)
                    elif msg_type == "ready":
                        with self.lock:
                            if self.game_state == "waiting" and len(self.players) >= 1:
                                self._start_round()
        except (ConnectionResetError, OSError, BrokenPipeError):
            pass
        finally:
            with self.lock:
                if player_id is not None and player_id in self.players:
                    del self.players[player_id]
                if player_id is not None and player_id in self.clients:
                    del self.clients[player_id]
            self._broadcast_player_leave(player_id)
            try:
                client_socket.close()
            except Exception:
                pass
            print(f"Cliente {addr} desconectado (ID:{player_id})")

    def _start_round(self):
        spawn_positions = [
            (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            (CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
            ((COLS - 2) * CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
        ]
        for i, (pid, p) in enumerate(self.players.items()):
            sx, sy = spawn_positions[i % len(spawn_positions)]
            p["x"] = float(sx)
            p["y"] = float(sy)
            p["dx"] = 0
            p["dy"] = 1
            p["bombs_active"] = 0
            p["invuln_timer"] = 60

        positions = [(p["x"], p["y"]) for p in self.players.values()]
        self.grid = generate_world(self.level, positions)
        self.enemies = spawn_enemies(self.level, self.grid, positions)
        self.bombs.clear()
        self.explosions.clear()
        self.powerups.clear()
        blocks = [(r, c) for r in range(ROWS) for c in range(COLS) if self.grid[r][c] == CELL_BLOCK]
        if blocks:
            self.door_cell = random.choice(blocks)
        else:
            self.door_cell = (ROWS // 2, COLS // 2)
        self.door_revealed = False
        self.door_open = False
        self.game_state = "playing"
        msg = encode({"type": "game_start"})
        for client_socket, _ in self.clients.values():
            try:
                client_socket.send(msg)
            except Exception:
                pass
        self._broadcast_state()

    def _broadcast_state(self):
        state = self._get_state()
        msg = encode({"type": "state", **state})
        for client_socket, _ in self.clients.values():
            try:
                client_socket.send(msg)
            except Exception:
                pass

    def _broadcast_message(self, msg):
        data = encode(msg)
        for client_socket, _ in self.clients.values():
            try:
                client_socket.send(data)
            except Exception:
                pass

    def _broadcast_player_join(self, player_id):
        p = self.players.get(player_id)
        if p:
            self._broadcast_message({
                "type": "player_join",
                "id": player_id,
                "name": p["name"],
                "char": p["char_key"],
            })

    def _broadcast_player_leave(self, player_id):
        self._broadcast_message({"type": "player_leave", "id": player_id})

    def _send_full_state(self, client_socket, player_id):
        state = self._get_state()
        msg = encode({"type": "state", **state})
        try:
            client_socket.send(msg)
        except Exception:
            pass

    def _get_state(self):
        return {
            "game_state": self.game_state,
            "level": self.level,
            "score": self.score,
            "grid": self.grid,
            "players": {str(k): {
                "id": v["id"], "name": v["name"], "char": v["char_key"],
                "x": v["x"], "y": v["y"], "lives": v["lives"],
                "alive": v["alive"], "color": v["color"], "accent": v["accent"],
                "bombs_max": v["bombs_max"], "fire_power": v["fire_power"],
                "speed": v["speed"], "score": v["score"],
                "invuln_timer": v["invuln_timer"], "shield_timer": v["shield_timer"],
            } for k, v in self.players.items()},
            "enemies": [{"x": e["x"], "y": e["y"], "type": e["type"],
                          "hp": e["hp"], "color": e["color"],
                          "dir": e["dir"]} for e in self.enemies],
            "bombs": [{"x": b["x"], "y": b["y"], "timer": b["timer"],
                        "power": b["power"]} for b in self.bombs],
            "explosions": [{"x": e["x"], "y": e["y"], "timer": e["timer"]}
                            for e in self.explosions],
            "powerups": [{"x": p["x"], "y": p["y"], "type": p["type"]}
                          for p in self.powerups],
            "door": {
                "r": self.door_cell[0],
                "c": self.door_cell[1],
                "revealed": self.door_revealed,
                "open": self.door_open
            },
        }

    def _move_player(self, player, dx, dy):
        if not player["alive"]:
            return
        speed = player["speed"]
        r = 10

        def is_free(tx, ty):
            if (tx - r < CELL or tx + r > (COLS - 1) * CELL or
                    ty - r < HUD_H + CELL or ty + r > HUD_H + (ROWS - 1) * CELL):
                return False
            for ox, oy in [(-r, -r), (r, -r), (-r, r), (r, r)]:
                cx = int(tx + ox) // CELL
                cy = int(ty + oy - HUD_H) // CELL
                if cx < 0 or cx >= COLS or cy < 0 or cy >= ROWS:
                    return False
                if self.grid[cy][cx] != CELL_EMPTY:
                    return False
            # Las bombas no bloquean al jugador para permitirle pasar libremente y no quedar atrapado
            return True

        if dx != 0 and dy == 0:
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
                player["y"] += math.copysign(min(abs(diff_y), speed), diff_y)
                if is_free(player["x"] + dx * (speed * 0.5), player["y"]):
                    player["x"] += dx * (speed * 0.5)

        elif dy != 0 and dx == 0:
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
                player["x"] += math.copysign(min(abs(diff_x), speed), diff_x)
                if is_free(player["x"], player["y"] + dy * (speed * 0.5)):
                    player["y"] += dy * (speed * 0.5)

    def _place_bomb(self, player):
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
            "owner_id": player["id"],
        })
        player["bombs_active"] += 1

    def _explode_bomb(self, bomb):
        owner_id = bomb.get("owner_id")
        if owner_id is not None and owner_id in self.players:
            self.players[owner_id]["bombs_active"] = max(0, self.players[owner_id]["bombs_active"] - 1)
        power = bomb["power"]
        bx = int(bomb["x"]) // CELL
        by = int(bomb["y"] - HUD_H) // CELL
        cells = [(bx, by)]

        if 0 <= bx < COLS and 0 <= by < ROWS and self.grid[by][bx] == CELL_BLOCK:
            self.grid[by][bx] = CELL_EMPTY
            if (by, bx) == self.door_cell:
                self.door_revealed = True

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            for i in range(1, power + 1):
                nx, ny = bx + dx * i, by + dy * i
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if self.grid[ny][nx] == CELL_WALL:
                        break
                    cells.append((nx, ny))
                    if self.grid[ny][nx] == CELL_BLOCK:
                        self.grid[ny][nx] = CELL_EMPTY
                        if (ny, nx) == self.door_cell:
                            self.door_revealed = True
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

    def _game_loop(self):
        while self.running:
            time.sleep(1.0 / 30.0)
            with self.lock:
                if self.game_state == "playing":
                    self.frame += 1
                    self._update_bombs()
                    self._update_explosions()
                    self._update_enemies()
                    self._check_collisions()
                    self._check_powerups()

                    all_dead = all(not p["alive"] for p in self.players.values())
                    if all_dead and self.players:
                        self.game_state = "game_over"
                    else:
                        # Abrir la puerta si todos los enemigos fueron derrotados
                        if len(self.enemies) == 0:
                            self.door_open = True

                        # Comprobar si algún jugador vivo pisa la puerta abierta
                        if self.door_revealed and self.door_open and self.grid[self.door_cell[0]][self.door_cell[1]] != CELL_BLOCK:
                            dr, dc = self.door_cell
                            door_x = dc * CELL + CELL // 2
                            door_y = dr * CELL + CELL // 2 + HUD_H
                            jugador_entro = any(
                                p["alive"] and math.hypot(p["x"] - door_x, p["y"] - door_y) < CELL * 0.55
                                for p in self.players.values()
                            )
                            if jugador_entro:
                                self.level += 1
                                if self.level > MAX_LEVEL:
                                    self.game_state = "victory"
                                else:
                                    self.score += self.level * 1000
                                    for pl in self.players.values():
                                        pl["score"] += self.level * 1000
                                    self._start_round()
                    self._broadcast_state()

    def _update_bombs(self):
        new_bombs = []
        for b in self.bombs:
            b["timer"] -= 1
            if b["timer"] <= 0:
                self._explode_bomb(b)
            else:
                new_bombs.append(b)
        self.bombs = new_bombs

    def _update_explosions(self):
        self.explosions = [e for e in self.explosions if e["timer"] > 1]
        for e in self.explosions:
            e["timer"] -= 1

    def _update_enemies(self):
        for e in self.enemies:
            speed_frames = max(1, int(30 / e["speed"]))
            if self.frame % speed_frames == 0:
                dx, dy = e["dir"]
                nx = e["x"] + dx * CELL
                ny = e["y"] + dy * CELL
                nx_c = int(nx) // CELL
                ny_c = int((ny - HUD_H)) // CELL
                can_move = (0 <= nx_c < COLS and 0 <= ny_c < ROWS and
                            self.grid[ny_c][nx_c] == CELL_EMPTY)
                for oe in self.enemies:
                    if oe is not e and abs(oe["x"] - nx) < CELL * 0.8 and abs(oe["y"] - ny) < CELL * 0.8:
                        can_move = False
                        break
                if can_move:
                    e["x"] = nx
                    e["y"] = ny
                else:
                    e["dir"] = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

    def _check_collisions(self):
        for p in self.players.values():
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
                        if p["lives"] <= 0:
                            p["alive"] = False
                        else:
                            p["invuln_timer"] = 120
                            spawn_positions = [
                                (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
                                ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
                            ]
                            idx = p["id"] % len(spawn_positions)
                            p["x"], p["y"] = spawn_positions[idx]
            for exp in self.explosions:
                if abs(p["x"] - exp["x"]) < CELL * 0.6 and abs(p["y"] - exp["y"]) < CELL * 0.6:
                    if p["shield_timer"] <= 0 and p["invuln_timer"] <= 0:
                        p["lives"] -= 1
                        if p["lives"] <= 0:
                            p["alive"] = False
                        else:
                            p["invuln_timer"] = 120
                            spawn_positions = [
                                (CELL + CELL // 2, CELL + CELL // 2 + HUD_H),
                                ((COLS - 2) * CELL + CELL // 2, (ROWS - 2) * CELL + CELL // 2 + HUD_H),
                            ]
                            idx = p["id"] % len(spawn_positions)
                            p["x"], p["y"] = spawn_positions[idx]
        for e in self.enemies[:]:
            for exp in self.explosions:
                if abs(e["x"] - exp["x"]) < CELL * 0.6 and abs(e["y"] - exp["y"]) < CELL * 0.6:
                    e["hp"] -= 1
                    if e["hp"] <= 0:
                        self.enemies.remove(e)
                        self.score += e["score"]
                        for p in self.players.values():
                            if p["alive"]:
                                p["score"] += e["score"]
                    break

    def _check_powerups(self):
        for p in self.players.values():
            if not p["alive"]:
                continue
            for pu in self.powerups[:]:
                if abs(p["x"] - pu["x"]) < CELL * 0.6 and abs(p["y"] - pu["y"]) < CELL * 0.6:
                    if pu["type"] == "bomb_up":
                        p["bombs_max"] = min(8, p["bombs_max"] + 1)
                    elif pu["type"] == "fire_up":
                        p["fire_power"] = min(8, p["fire_power"] + 1)
                    elif pu["type"] == "speed_up":
                        p["speed"] = min(6.0, p["speed"] + 0.5)
                    elif pu["type"] == "shield":
                        p["shield_timer"] = 300
                    self.powerups.remove(pu)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Servidor de Bomberman Multijugador (Nube o Local)")
    env_port = int(os.environ.get("PORT", "5555"))
    default_alt = 5555 if env_port != 5555 else 8080
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Host IP para escuchar (por defecto 0.0.0.0)")
    parser.add_argument("--port", type=int, default=env_port, help="Puerto principal para escuchar")
    parser.add_argument("--alt_port", type=int, default=default_alt, help="Puerto secundario para escuchar")
    args = parser.parse_args()

    server = GameServer(host=args.host, port=args.port, alt_port=args.alt_port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.running = False
        print("\nServidor detenido.")
