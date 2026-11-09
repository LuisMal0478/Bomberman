"""
Modelo de Generación y Gestión del Mapa.
Contiene algoritmos para la creación procedimental de niveles y generación de enemigos.
"""

import random
from configuracion import (ANCHO_CASILLA, COLUMNAS, FILAS, ALTO_HUD,
                           CASILLA_VACIA, CASILLA_PARED, CASILLA_BLOQUE,
                           TIPOS_ENEMIGOS)
from modelos.enemigo import Enemigo


class Mapa:
    @staticmethod
    def generar_matriz(nivel, posiciones_jugadores):
        """Genera una matriz de casillas para el nivel indicado."""
        matriz = [[CASILLA_VACIA] * COLUMNAS for _ in range(FILAS)]

        # Bordes exteriores y columnas interiores rígidas
        for r in range(FILAS):
            for c in range(COLUMNAS):
                if r == 0 or r == FILAS - 1 or c == 0 or c == COLUMNAS - 1:
                    matriz[r][c] = CASILLA_PARED
                elif r % 2 == 0 and c % 2 == 0:
                    matriz[r][c] = CASILLA_PARED

        # Definir zona segura de spawn para los jugadores
        zonas_seguras = set()
        for px, py in posiciones_jugadores:
            casilla_px = int(px) // ANCHO_CASILLA
            casilla_py = int(py - ALTO_HUD) // ANCHO_CASILLA
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = casilla_py + dr, casilla_px + dc
                    if 0 <= nr < FILAS and 0 <= nc < COLUMNAS:
                        zonas_seguras.add((nr, nc))

        # Esquinas de spawn clásicas protegidas siempre
        esquinas_spawn = [
            (1, 1), (1, 2), (2, 1),
            (1, COLUMNAS - 2), (1, COLUMNAS - 3), (2, COLUMNAS - 2),
            (FILAS - 2, 1), (FILAS - 3, 1), (FILAS - 2, 2),
            (FILAS - 2, COLUMNAS - 2), (FILAS - 3, COLUMNAS - 2), (FILAS - 2, COLUMNAS - 3)
        ]
        for cr, cc in esquinas_spawn:
            zonas_seguras.add((cr, cc))

        # Rellenar con bloques destructibles según densidad por nivel
        densidad = min(0.68, 0.52 + nivel * 0.02)
        for r in range(1, FILAS - 1):
            for c in range(1, COLUMNAS - 1):
                if matriz[r][c] == CASILLA_VACIA and (r, c) not in zonas_seguras:
                    if random.random() < densidad:
                        matriz[r][c] = CASILLA_BLOQUE

        # Garantizar que las casillas de los jugadores siempre están vacías
        for px, py in posiciones_jugadores:
            cpx = int(px) // ANCHO_CASILLA
            cpy = int(py - ALTO_HUD) // ANCHO_CASILLA
            if 0 <= cpy < FILAS and 0 <= cpx < COLUMNAS:
                matriz[cpy][cpx] = CASILLA_VACIA

        return matriz

    @staticmethod
    def generar_enemigos(nivel, matriz_mapa, posiciones_jugadores):
        """Genera enemigos distribuidos aleatoriamente fuera de la distancia inicial del jugador."""
        enemigos = []
        cantidad = min(3 + nivel * 2, 15)
        casillas_disponibles = []

        # Progresión de enemigos según nivel
        if nivel == 1:
            tipos_desbloqueados = ["balloom"]
        elif nivel == 2:
            tipos_desbloqueados = ["balloom", "oneal", "doll"]
        elif nivel == 3:
            tipos_desbloqueados = ["oneal", "doll", "fantasma", "ovapi"]
        elif nivel == 4:
            tipos_desbloqueados = ["minvo", "fantasma", "ovapi", "pass"]
        else:
            tipos_desbloqueados = ["fantasma", "ovapi", "pass", "pontan"]

        for r in range(1, FILAS - 1):
            for c in range(1, COLUMNAS - 1):
                if matriz_mapa[r][c] == CASILLA_VACIA:
                    demasiado_cerca = False
                    for px, py in posiciones_jugadores:
                        distancia_x = abs(c * ANCHO_CASILLA + ANCHO_CASILLA // 2 - px)
                        distancia_y = abs(r * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD - py)
                        if distancia_x < ANCHO_CASILLA * 3 and distancia_y < ANCHO_CASILLA * 3:
                            demasiado_cerca = True
                            break
                    if not demasiado_cerca:
                        casillas_disponibles.append((r, c))

        random.shuffle(casillas_disponibles)
        for i in range(min(cantidad, len(casillas_disponibles))):
            r, c = casillas_disponibles[i]
            tipo = random.choice(tipos_desbloqueados)
            pos_x = c * ANCHO_CASILLA + ANCHO_CASILLA // 2
            pos_y = r * ANCHO_CASILLA + ANCHO_CASILLA // 2 + ALTO_HUD
            enemigos.append(Enemigo(pos_x, pos_y, tipo))

        return enemigos
