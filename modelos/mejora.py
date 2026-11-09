"""
Modelo de Mejora (Power-Up).
Representa los coleccionables que aparecen al destruir bloques.
"""

import random
from configuracion import TIPOS_MEJORAS


class Mejora:
    def __init__(self, posicion_x, posicion_y, tipo_mejora=None):
        self.posicion_x = posicion_x
        self.posicion_y = posicion_y
        self.tipo_mejora = tipo_mejora if tipo_mejora else random.choice(TIPOS_MEJORAS)

    def a_diccionario(self):
        """Serializa la mejora a un diccionario para red."""
        return {
            "x": self.posicion_x,
            "y": self.posicion_y,
            "type": self.tipo_mejora
        }
