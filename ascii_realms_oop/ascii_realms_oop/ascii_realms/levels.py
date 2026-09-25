"""Level definitions.

A Level bundles everything BattleState/IntroState need for one stage:
its title, intro dialogue, background music key, and a factory function
that builds a fresh Enemy (so replaying a level never reuses a dead one).
"""

from . import ascii_art as art
from . import config as cfg
from .entities import Enemy


class Level:
    def __init__(self, title, intro, bgm, enemy_factory):
        self.title = title
        self.intro = intro
        self.bgm = bgm
        self._enemy_factory = enemy_factory

    def create_enemy(self):
        return self._enemy_factory()


LEVELS = [
    Level(
        title="LEVEL 1 — Whispering Woods",
        intro=[
            "You step beneath the whispering pines.",
            "Something with sharp teeth blocks the path...",
            "A GOBLIN GRUNT snarls and lunges at you!",
        ],
        bgm="woods",
        enemy_factory=lambda: Enemy(
            "Goblin Grunt", 46, 7, art.GOBLIN_ART, cfg.RED, "Rusty Slash"
        ),
    ),
    Level(
        title="LEVEL 2 — Dragon's Lair",
        intro=[
            "Deep beneath the mountain, heat shimmers in the dark.",
            "Two burning eyes open in the gloom...",
            "The EMBER DRAKE rises to meet you!",
        ],
        bgm="lair",
        enemy_factory=lambda: Enemy(
            "Ember Drake", 95, 11, art.DRAKE_ART, cfg.ORANGE, "Fire Breath"
        ),
    ),
]
