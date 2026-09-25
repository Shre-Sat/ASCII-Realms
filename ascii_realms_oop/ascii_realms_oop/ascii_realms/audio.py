"""Procedural audio.

Everything the game plays — sound effects and background loops — is
synthesized on the fly with numpy, so the game needs zero external
asset files. All of that behaviour is encapsulated in one class,
SoundEngine, so the rest of the codebase just calls play_sfx()/play_bgm()
without knowing (or caring) how a sound is made.
"""

import random

import numpy as np
import pygame

SAMPLE_RATE = 44100


class SoundEngine:
    """Owns the mixer, synthesizes all sounds once at startup, and plays them."""

    def __init__(self):
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
        except pygame.error:
            pass  # mixer already initialized elsewhere; that's fine

        # Some drivers force stereo regardless of what we ask for, so detect
        # the real channel count and shape every array to match it.
        info = pygame.mixer.get_init()
        self.channels = info[2] if info else 1

        self._bgm_channel = pygame.mixer.Channel(7)
        self.sfx = {}
        self.bgm = {}
        self._build_sfx_library()
        self._build_bgm_library()

    # ---------------- low-level waveform synthesis ----------------

    @staticmethod
    def _wave(freq, n, kind):
        t = np.linspace(0, n / SAMPLE_RATE, n, endpoint=False)
        if kind == "sine":
            return np.sin(2 * np.pi * freq * t)
        if kind == "square":
            return np.sign(np.sin(2 * np.pi * freq * t))
        if kind == "saw":
            return 2 * (t * freq - np.floor(0.5 + t * freq))
        if kind == "noise":
            return np.random.uniform(-1, 1, n)
        return np.zeros(n)

    def _to_sound(self, float_array):
        arr = np.clip(float_array * 32767, -32767, 32767).astype(np.int16)
        if self.channels >= 2:
            arr = np.repeat(arr.reshape(-1, 1), self.channels, axis=1)
        arr = np.ascontiguousarray(arr)
        return pygame.sndarray.make_sound(arr)

    def tone(self, freq=440, dur=0.15, vol=0.5, kind="square", decay=2.0):
        n = max(1, int(SAMPLE_RATE * dur))
        w = self._wave(freq, n, kind)
        env = np.linspace(1, 0, n) ** decay
        return self._to_sound(w * env * vol)

    def sequence(self, notes, vol=0.5, kind="square", decay=1.6):
        """notes: list of (freq, duration) tuples; freq <= 0 means a rest."""
        chunks = []
        for freq, dur in notes:
            n = max(1, int(SAMPLE_RATE * dur))
            if freq <= 0:
                chunks.append(np.zeros(n))
                continue
            w = self._wave(freq, n, kind)
            env = np.linspace(1, 0, n) ** decay
            chunks.append(w * env)
        arr = np.concatenate(chunks) * vol
        return self._to_sound(arr)

    def _arpeggio_loop(self, scale, tempo=0.16, bars=8, vol=0.14):
        random.seed(len(scale) * 7 + bars)
        notes = [(random.choice(scale), tempo) for _ in range(bars * 4)]
        return self.sequence(notes, vol, "sine", decay=1.1)

    # ---------------- sound libraries ----------------

    def _build_sfx_library(self):
        self.sfx = {
            "move": self.tone(700, 0.04, 0.25, "square"),
            "select": self.sequence([(660, 0.05), (880, 0.06)], 0.35, "square"),
            "attack": self.sequence([(180, 0.05), (90, 0.08)], 0.6, "square", 3),
            "hit": self.tone(120, 0.14, 0.7, "noise", 4),
            "heal": self.sequence([(440, 0.07), (660, 0.07), (880, 0.14)], 0.4, "sine"),
            "magic": self.sequence(
                [(500, 0.05), (750, 0.05), (1000, 0.05), (1400, 0.12)], 0.4, "sine"
            ),
            "defend": self.tone(300, 0.12, 0.4, "sine"),
            "victory": self.sequence(
                [(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.30)], 0.5, "square"
            ),
            "defeat": self.sequence([(392, 0.22), (311, 0.22), (220, 0.4)], 0.5, "saw", 2.2),
            "levelwin": self.sequence(
                [(523, 0.1), (659, 0.1), (784, 0.1), (1046, 0.1), (1318, 0.35)], 0.45, "square"
            ),
            "gameover_jingle": self.sequence(
                [(220, 0.15), (207, 0.15), (196, 0.15), (0, 0.05), (185, 0.5)],
                0.5,
                "saw",
                2.0,
            ),
        }

    def _build_bgm_library(self):
        self.bgm = {
            "woods": self._arpeggio_loop([196, 220, 247, 262, 294, 330], tempo=0.18, bars=6),
            "lair": self._arpeggio_loop([146, 164, 174, 196, 220, 233], tempo=0.15, bars=6),
            "title": self._arpeggio_loop([262, 330, 392, 440], tempo=0.22, bars=4),
        }

    # ---------------- playback API ----------------

    def play_sfx(self, key):
        channel = pygame.mixer.find_channel(True)
        if channel is not None:
            channel.play(self.sfx[key])

    def play_bgm(self, key):
        self._bgm_channel.play(self.bgm[key], loops=-1)

    def stop_bgm(self):
        self._bgm_channel.stop()
