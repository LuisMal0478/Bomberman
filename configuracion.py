"""
Módulo de Configuración Global del Juego Bomberman.
Contiene todas las constantes de pantalla, colores, celdas, personajes y enemigos en español.
"""

import pygame

# --- DIMENSIONES Y RENDIMIENTO ---
ANCHO_CASILLA = 40
COLUMNAS = 17
FILAS = 13
ALTO_HUD = 60
ANCHO_JUEGO = COLUMNAS * ANCHO_CASILLA
ALTO_JUEGO = FILAS * ANCHO_CASILLA + ALTO_HUD
FPS = 60
NIVEL_MAXIMO = 10

# --- TIPOS DE CASILLAS EN EL MAPA ---
CASILLA_VACIA = 0
CASILLA_PARED = 1
CASILLA_BLOQUE = 2

# --- COLORES ---
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
NEON_AZUL = (0, 212, 255)
DORADO = (255, 215, 0)
ROJO = (255, 71, 87)
VERDE = (46, 213, 115)
GRIS = (100, 100, 120)
GRIS_OSCURO = (40, 40, 60)
GRIS_CLARO = (180, 180, 200)

COLOR_FONDO_OSCURO = (26, 26, 46)
COLOR_FONDO_OSCURO2 = (15, 52, 96)
COLOR_PARED = (80, 80, 100)
COLOR_BLOQUE = (180, 140, 60)
COLOR_BLOQUE2 = (160, 120, 50)
COLOR_SUELO = (40, 50, 30)
COLOR_SUELO2 = (35, 45, 25)
COLOR_BOMBA = (30, 30, 30)
COLOR_EXPLOSION = (255, 120, 0)
COLOR_EXPLOSION2 = (255, 200, 50)
COLOR_FUEGO = (255, 69, 0)
COLOR_NARANJA = (255, 140, 0)

# --- CONFIGURACIÓN DE PERSONAJES ---
PERSONAJES = {
    "bomberman": {
        "nombre": "Bomberman Clásico",
        "color": (255, 255, 255),
        "acento": (50, 100, 220),
        "potencia_fuego": 2,
        "bombas_maximas": 1,
        "velocidad": 3.0,
        "descripcion": "Equilibrado y versátil"
    },
    "fuego": {
        "nombre": "Maestro del Fuego",
        "color": (220, 40, 40),
        "acento": (255, 140, 0),
        "potencia_fuego": 3,
        "bombas_maximas": 1,
        "velocidad": 2.7,
        "descripcion": "Explosiones de gran alcance"
    },
    "velocidad": {
        "nombre": "Corredor Veloz",
        "color": (0, 200, 200),
        "acento": (34, 139, 34),
        "potencia_fuego": 1,
        "bombas_maximas": 1,
        "velocidad": 3.8,
        "descripcion": "Velocidad de movimiento extrema"
    },
    "tanque": {
        "nombre": "Tanque Pesado",
        "color": (80, 80, 80),
        "acento": (139, 90, 43),
        "potencia_fuego": 2,
        "bombas_maximas": 3,
        "velocidad": 2.4,
        "descripcion": "Despliega múltiples bombas"
    }
}

# --- CONFIGURACIÓN DE ENEMIGOS (8 TIPOS CLÁSICOS) ---
TIPOS_ENEMIGOS = {
    "balloom": {
        "nombre": "Globo Balloom",
        "salud": 1,
        "velocidad": 1.2,
        "puntos": 100,
        "color": (230, 80, 80),
        "prob_persecucion": 0.30,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_balloom.png"
    },
    "globito": {
        "nombre": "Globo Balloom",
        "salud": 1,
        "velocidad": 1.2,
        "puntos": 100,
        "color": (230, 80, 80),
        "prob_persecucion": 0.30,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_balloom.png"
    },
    "oneal": {
        "nombre": "Gota Azul O'Neal",
        "salud": 1,
        "velocidad": 1.6,
        "puntos": 200,
        "color": (80, 180, 240),
        "prob_persecucion": 0.55,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_oneal.png"
    },
    "doll": {
        "nombre": "Barril Dahl",
        "salud": 1,
        "velocidad": 1.8,
        "puntos": 300,
        "color": (190, 40, 80),
        "prob_persecucion": 0.65,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_doll.png"
    },
    "muneco": {
        "nombre": "Barril Dahl",
        "salud": 1,
        "velocidad": 1.8,
        "puntos": 300,
        "color": (190, 40, 80),
        "prob_persecucion": 0.65,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_doll.png"
    },
    "minvo": {
        "nombre": "Minvo",
        "salud": 2,
        "velocidad": 2.1,
        "puntos": 400,
        "color": (240, 100, 80),
        "prob_persecucion": 0.80,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_minvo.png"
    },
    "fantasma": {
        "nombre": "Fantasma Pac Doria",
        "salud": 1,
        "velocidad": 1.9,
        "puntos": 500,
        "color": (210, 30, 90),
        "prob_persecucion": 0.85,
        "traspasa_bloques": True,
        "archivo_sprite": "enemigo_fantasma.png"
    },
    "ovapi": {
        "nombre": "Masa Celeste Ovapi",
        "salud": 1,
        "velocidad": 1.7,
        "puntos": 600,
        "color": (70, 200, 255),
        "prob_persecucion": 0.70,
        "traspasa_bloques": True,
        "archivo_sprite": "enemigo_ovapi.png"
    },
    "pass": {
        "nombre": "Fiera Cazadora Pass",
        "salud": 2,
        "velocidad": 2.4,
        "puntos": 700,
        "color": (240, 120, 110),
        "prob_persecucion": 0.90,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_pass.png"
    },
    "veloz": {
        "nombre": "Fiera Cazadora Pass",
        "salud": 2,
        "velocidad": 2.4,
        "puntos": 700,
        "color": (240, 120, 110),
        "prob_persecucion": 0.90,
        "traspasa_bloques": False,
        "archivo_sprite": "enemigo_pass.png"
    },
    "pontan": {
        "nombre": "Pontan Supremo",
        "salud": 2,
        "velocidad": 2.5,
        "puntos": 800,
        "color": (240, 80, 80),
        "prob_persecucion": 0.95,
        "traspasa_bloques": True,
        "archivo_sprite": "enemigo_pontan.png"
    }
}

# --- TIPOS DE MEJORAS (POWER-UPS) ---
TIPOS_MEJORAS = ["mas_bomba", "mas_fuego", "mas_velocidad", "escudo"]
