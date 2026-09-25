"""Battle entities: a Fighter base class plus Player and Enemy subclasses.

This is the core OOP demonstration in the project:
- Fighter defines shared state and behaviour (HP, guarding, damage,
  hit-flash/shake animation timers).
- Player and Enemy each extend Fighter with their own abilities
  (attack/defend/magic/item vs. a special-attack pattern), so a
  BattleState can treat both polymorphically as "a Fighter with hp/art"
  while still calling their distinct action methods.
"""

from abc import ABC
import random


class Fighter(ABC):
    """Common battle-entity state: HP, guarding, and hit animation timers."""

    def __init__(self, name, hp, atk, art, color, guard_mult=0.4):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.art = art
        self.color = color
        self.guarding = False
        self.guard_mult = guard_mult
        self.shake = 0
        self.flash = 0

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        """Apply damage (reduced if guarding), trigger hit animation, return the amount dealt."""
        if self.guarding:
            amount = max(1, int(amount * self.guard_mult))
        amount = max(1, int(amount))
        self.hp = max(0, self.hp - amount)
        self.shake = 10
        self.flash = 8
        return amount

    def tick_effects(self):
        """Advance the shake/flash hit-animation timers by one frame."""
        if self.shake > 0:
            self.shake -= 1
        if self.flash > 0:
            self.flash -= 1


class Player(Fighter):
    """The hero. Adds magic, an MP pool, and a potion inventory."""

    def __init__(self, name="Chhavi", hp=60, atk=10, mag=12, mp=20, art=None, color=None):
        super().__init__(name, hp, atk, art, color, guard_mult=0.35)
        self.mag = mag
        self.max_mp = mp
        self.mp = mp
        self.potions = 3

    def attack(self, target, sound):
        sound.play_sfx("attack")
        dmg = random.randint(self.atk - 2, self.atk + 4)
        dealt = target.take_damage(dmg)
        sound.play_sfx("hit")
        return f"You strike for {dealt} damage!"

    def defend(self, sound):
        sound.play_sfx("defend")
        self.guarding = True
        return "You brace yourself, guard up!"

    def cast_magic(self, target, sound):
        if self.mp < 6:
            return None
        self.mp -= 6
        sound.play_sfx("magic")
        dmg = random.randint(self.mag + 4, self.mag + 12)
        dealt = target.take_damage(dmg)
        return f"Arcane bolt hits for {dealt} damage!"

    def use_item(self, sound):
        if self.potions <= 0:
            return None
        self.potions -= 1
        heal = random.randint(14, 20)
        self.hp = min(self.max_hp, self.hp + heal)
        sound.play_sfx("heal")
        return f"You drink a potion, +{heal} HP!"

    def regen_mp(self, amount=2):
        self.mp = min(self.max_mp, self.mp + amount)

    def reset_guard(self):
        self.guarding = False

    def restore_for_next_level(self, hp_bonus=15):
        self.hp = min(self.max_hp, self.hp + hp_bonus)
        self.mp = self.max_mp


class Enemy(Fighter):
    """A foe with a normal attack and a named special move."""

    def __init__(self, name, hp, atk, art, color, special_name, special_chance=0.28):
        super().__init__(name, hp, atk, art, color)
        self.special_name = special_name
        self.special_chance = special_chance

    def act(self, target, sound):
        """Take a turn against target, returning a battle-log message."""
        if random.random() < self.special_chance:
            sound.play_sfx("magic")
            dmg = random.randint(self.atk + 3, self.atk + 9)
            dealt = target.take_damage(dmg)
            sound.play_sfx("hit")
            return f"{self.name} uses {self.special_name} for {dealt} damage!"

        sound.play_sfx("attack")
        dmg = random.randint(self.atk - 2, self.atk + 3)
        dealt = target.take_damage(dmg)
        sound.play_sfx("hit")
        return f"{self.name} attacks for {dealt} damage!"
