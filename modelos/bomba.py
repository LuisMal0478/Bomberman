"""
Modelos de Bomba y Explosión.
Representan las bombas colocadas por jugadores y las explosiones resultantes.
"""

from configuracion import ANCHO_CASILLA, ALTO_HUD


class Bomba:
    def __init__(self, posicion_x, posicion_y, potencia, propietario=None, temporizador=180):
        self.posicion_x = posicion_x
        self.posicion_y = posicion_y
        self.potencia = potencia
        self.propietario = propietario
        self.temporizador = temporizador
        self.esta_explotada = False

    def actualizar(self):
        """Disminuye el temporizador de la bomba. Retorna True cuando debe explotar."""
        self.temporizador -= 1
        if self.temporizador <= 0:
            self.esta_explotada = True
            return True
        return False

    def a_diccionario(self):
        """Serializa la bomba a un diccionario para red."""
        return {
            "x": self.posicion_x,
            "y": self.posicion_y,
            "power": self.potencia,
            "timer": self.temporizador
        }


class Explosion:
    def __init__(self, posicion_x, posicion_y, temporizador=20):
        self.posicion_x = posicion_x
        self.posicion_y = posicion_y
        self.temporizador = temporizador

    def actualizar(self):
        """Disminuye la duración de la onda expansiva."""
        self.temporizador -= 1
        return self.temporizador > 0

    def a_diccionario(self):
        """Serializa la explosión a un diccionario para red."""
        return {
            "x": self.posicion_x,
            "y": self.posicion_y,
            "timer": self.temporizador
        }
