"""
Administrador de Sonidos del Juego.
Genera ondas sonoras y efectos de sonido en tiempo real usando Pygame Mixer.
"""

import pygame
import math
import array

_mezclador_inicializado = False


def _asegurar_mezclador():
    global _mezclador_inicializado
    if not _mezclador_inicializado:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            _mezclador_inicializado = True
        except Exception:
            pass


def _generar_muestras(duracion_segundos, funcion_generadora, tasa_muestreo=44100):
    n = int(tasa_muestreo * duracion_segundos)
    búfer = array.array('h', (0,) * n)
    for i in range(n):
        t = i / tasa_muestreo
        val = funcion_generadora(t, duracion_segundos)
        val = max(-1.0, min(1.0, val))
        búfer[i] = int(val * 32767)
    return búfer


def _crear_sonido(muestras):
    return pygame.mixer.Sound(buffer=muestras.tobytes())


def _gen_explosion(t, dur):
    envolvente = max(0, 1.0 - t / dur)
    ruido = (hash(int(t * 10000)) % 2000 - 1000) / 1000.0
    return ruido * envolvente * 0.6


def _gen_mejora(t, dur):
    frec = 400 + 800 * (t / dur)
    envolvente = 1.0 - t / dur
    return math.sin(2 * math.pi * frec * t) * envolvente * 0.4


def _gen_muerte(t, dur):
    frec = 400 - 300 * (t / dur)
    envolvente = max(0, 1.0 - t / dur)
    return math.sin(2 * math.pi * frec * t) * envolvente * 0.5


def _gen_menu_hover(t, dur):
    envolvente = max(0, 1.0 - t / dur)
    return math.sin(2 * math.pi * 800 * t) * envolvente * 0.2


def _gen_menu_seleccion(t, dur):
    envolvente = max(0, 1.0 - t / dur * 2) if t < dur * 0.5 else 0
    return math.sin(2 * math.pi * 600 * t) * envolvente * 0.3


def _gen_bomba_colocada(t, dur):
    envolvente = max(0, 1.0 - t / dur)
    frec = 200 - 100 * (t / dur)
    return math.sin(2 * math.pi * frec * t) * envolvente * 0.3


def _gen_paso(t, dur):
    envolvente = max(0, 1.0 - t / dur)
    ruido = (hash(int(t * 20000)) % 500 - 250) / 1000.0
    return ruido * envolvente * 0.15


def _gen_nivel_completado(t, dur):
    frec = 300 + 600 * (t / dur)
    envolvente = max(0, 1.0 - t / dur) if t < dur * 0.8 else max(0, (dur - t) / (dur * 0.2)) * 0.5
    return math.sin(2 * math.pi * frec * t) * envolvente * 0.4


def _gen_victoria(t, dur):
    frec = 400 + 200 * math.sin(t * 8)
    envolvente = max(0, 1.0 - t / dur * 0.5)
    return math.sin(2 * math.pi * frec * t) * envolvente * 0.4


def _gen_dano(t, dur):
    envolvente = max(0, 1.0 - t / dur)
    frec = 600 - 400 * (t / dur)
    ruido = (hash(int(t * 15000)) % 400 - 200) / 1000.0
    return (math.sin(2 * math.pi * frec * t) * 0.3 + ruido * 0.3) * envolvente


class AdministradorSonidos:
    def __init__(self):
        _asegurar_mezclador()
        self.activo = True
        self.volumen = 0.7
        self._memoria_sonidos = {}
        self._inicializar_sonidos()

    def _inicializar_sonidos(self):
        definiciones = {
            'explosion': (0.5, _gen_explosion),
            'mejora': (0.4, _gen_mejora),
            'muerte': (0.6, _gen_muerte),
            'menu_hover': (0.1, _gen_menu_hover),
            'menu_seleccion': (0.15, _gen_menu_seleccion),
            'bomba_colocada': (0.2, _gen_bomba_colocada),
            'paso': (0.08, _gen_paso),
            'nivel_completado': (0.5, _gen_nivel_completado),
            'victoria': (0.8, _gen_victoria),
            'dano': (0.3, _gen_dano),
        }
        for nombre, (dur, fn) in definiciones.items():
            try:
                self._memoria_sonidos[nombre] = _crear_sonido(_generar_muestras(dur, fn))
            except Exception:
                pass

    def reproducir(self, nombre):
        """Reproduce un efecto de sonido por su nombre en español."""
        if not self.activo:
            return
        sonido = self._memoria_sonidos.get(nombre)
        if sonido:
            try:
                sonido.set_volume(self.volumen)
                sonido.play()
            except Exception:
                pass

    def cambiar_volumen(self, volumen):
        """Ajusta el volumen global entre 0.0 y 1.0."""
        self.volumen = max(0.0, min(1.0, volumen))

    def alternar_sonido(self):
        """Activa o desactiva el audio global."""
        self.activo = not self.activo
        return self.activo
