import json

MSG_JOIN = "join"
MSG_MOVE = "move"
MSG_BOMB = "bomb"
MSG_STATE = "state"
MSG_PLAYER_JOIN = "player_join"
MSG_PLAYER_LEAVE = "player_leave"
MSG_GAME_START = "game_start"
MSG_GAME_OVER = "game_over"
MSG_READY = "ready"
MSG_CHAT = "chat"


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


def make_join(name, char_key):
    return {"type": MSG_JOIN, "name": name, "char": char_key}


def make_move(dx, dy):
    return {"type": MSG_MOVE, "dx": dx, "dy": dy}


def make_bomb(x, y):
    return {"type": MSG_BOMB, "x": x, "y": y}


def make_state(state_dict):
    return {"type": MSG_STATE, **state_dict}


def make_player_join(pid, name, char_key):
    return {"type": MSG_PLAYER_JOIN, "id": pid, "name": name, "char": char_key}


def make_player_leave(pid):
    return {"type": MSG_PLAYER_LEAVE, "id": pid}


def make_game_start(world, players_info):
    return {"type": MSG_GAME_START, "world": world, "players": players_info}


def make_ready(ready=True):
    return {"type": MSG_READY, "ready": ready}


def make_chat(text):
    return {"type": MSG_CHAT, "text": text}
