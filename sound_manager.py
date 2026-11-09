import pygame
import math
import array

_mixer_initialized = False


def _ensure_mixer():
    global _mixer_initialized
    if not _mixer_initialized:
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        _mixer_initialized = True


def _generate_samples(duration_s, generator_fn, sample_rate=44100):
    n = int(sample_rate * duration_s)
    buf = array.array('h', (0,) * n)
    for i in range(n):
        t = i / sample_rate
        val = generator_fn(t, duration_s)
        val = max(-1.0, min(1.0, val))
        buf[i] = int(val * 32767)
    return buf


def _make_sound(samples, sample_rate=44100):
    return pygame.mixer.Sound(buffer=samples.tobytes())


def _explosion(t, dur):
    env = max(0, 1.0 - t / dur)
    noise = (hash(int(t * 10000)) % 2000 - 1000) / 1000.0
    return noise * env * 0.6


def _powerup(t, dur):
    freq = 400 + 800 * (t / dur)
    env = 1.0 - t / dur
    return math.sin(2 * math.pi * freq * t) * env * 0.4


def _death(t, dur):
    freq = 400 - 300 * (t / dur)
    env = max(0, 1.0 - t / dur)
    return math.sin(2 * math.pi * freq * t) * env * 0.5


def _menu_hover(t, dur):
    env = max(0, 1.0 - t / dur)
    return math.sin(2 * math.pi * 800 * t) * env * 0.2


def _menu_select(t, dur):
    env = max(0, 1.0 - t / dur * 2) if t < dur * 0.5 else 0
    return math.sin(2 * math.pi * 600 * t) * env * 0.3


def _bomb_place(t, dur):
    env = max(0, 1.0 - t / dur)
    freq = 200 - 100 * (t / dur)
    return math.sin(2 * math.pi * freq * t) * env * 0.3


def _step(t, dur):
    env = max(0, 1.0 - t / dur)
    noise = (hash(int(t * 20000)) % 500 - 250) / 1000.0
    return noise * env * 0.15


def _level_up(t, dur):
    freq = 300 + 600 * (t / dur)
    env = max(0, 1.0 - t / dur) if t < dur * 0.8 else max(0, (dur - t) / (dur * 0.2)) * 0.5
    return math.sin(2 * math.pi * freq * t) * env * 0.4


def _victory(t, dur):
    freq = 400 + 200 * math.sin(t * 8)
    env = max(0, 1.0 - t / dur * 0.5)
    return math.sin(2 * math.pi * freq * t) * env * 0.4


def _hurt(t, dur):
    env = max(0, 1.0 - t / dur)
    freq = 600 - 400 * (t / dur)
    noise = (hash(int(t * 15000)) % 400 - 200) / 1000.0
    return (math.sin(2 * math.pi * freq * t) * 0.3 + noise * 0.3) * env


class SoundManager:
    def __init__(self):
        _ensure_mixer()
        self.enabled = True
        self.volume = 0.7
        self._cache = {}
        self._init_sounds()

    def _init_sounds(self):
        defs = {
            'explosion': (0.5, _explosion),
            'powerup': (0.4, _powerup),
            'death': (0.6, _death),
            'menu_hover': (0.1, _menu_hover),
            'menu_select': (0.15, _menu_select),
            'bomb_place': (0.2, _bomb_place),
            'step': (0.08, _step),
            'level_up': (0.5, _level_up),
            'victory': (0.8, _victory),
            'hurt': (0.3, _hurt),
        }
        for name, (dur, fn) in defs.items():
            self._cache[name] = _make_sound(_generate_samples(dur, fn))

    def play(self, name):
        if not self.enabled:
            return
        snd = self._cache.get(name)
        if snd:
            snd.set_volume(self.volume)
            snd.play()

    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, vol))

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
