"""
Protocolo de Red para Bomberman Multijugador.
Define los comandos y funciones de codificación / decodificación JSON.
"""

import json

TIPO_UNIRSE = "unirse"
TIPO_MOVER = "mover"
TIPO_BOMBA = "bomba"
TIPO_ESTADO = "estado"
TIPO_JUGADOR_UNIDO = "jugador_unido"
TIPO_JUGADOR_SALIDO = "jugador_salido"
TIPO_INICIO = "inicio_juego"
TIPO_LISTO = "listo"
TIPO_CONEXION_OK = "conexion_ok"


def codificar_mensaje(diccionario_mensaje):
    """Codifica un diccionario a formato JSON con salto de línea final."""
    return json.dumps(diccionario_mensaje).encode('utf-8') + b"\n"


def decodificar_linea(linea_bytes_o_texto):
    """Decodifica una cadena o bytes recibidos por socket a un diccionario Python."""
    if isinstance(linea_bytes_o_texto, bytes):
        linea_bytes_o_texto = linea_bytes_o_texto.decode('utf-8', errors='replace')
    linea = linea_bytes_o_texto.strip()
    if not linea:
        return None
    try:
        return json.loads(linea)
    except json.JSONDecodeError:
        return None


def crear_mensaje_unirse(nombre, clave_personaje):
    return {"type": TIPO_UNIRSE, "name": nombre, "char": clave_personaje}


def crear_mensaje_mover(dx, dy):
    return {"type": TIPO_MOVER, "dx": dx, "dy": dy}


def crear_mensaje_bomba():
    return {"type": TIPO_BOMBA}


def crear_mensaje_listo(listo=True):
    return {"type": TIPO_LISTO, "ready": listo}
