"""The Game class: application entry point and state-machine orchestrator.

Game owns the shared session data (player, current enemy, level index,
battle log) and the pieces that don't belong to any one screen (the
window, clock, SoundEngine, Renderer). It exposes battle operations
(player_action, enemy_turn, check_battle_end, ...) that BattleState calls
into, keeping combat rules out of the drawing/input code.
"""

import random

import pygame

from . import ascii_art as art
from . import config as cfg
from .audio import SoundEngine
from .entities import Player
from .levels import LEVELS
from .ui import Renderer
from .states import (
    TitleState,
    IntroState,
    BattleState,
    LevelWinState,
    GameOverState,
    WinGameState,
)


class Game:
    def __init__(self):
        # SoundEngine calls pygame.init()/pygame.mixer.init() internally,
        # so it must be constructed before any other pygame calls.
        self.sound = SoundEngine()

        pygame.display.set_caption("ASCII REALMS — A Battle RPG")
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)

        # Session state shared across screens.
        self.level_idx = 0
        self.player = None
        self.enemy = None
        self.log = []
        self.menu_index = 0
        self.turn = "player"
        self.turn_timer = 0.0
        self.action_lock = False
        self.game_over_reason = ""

        self.running = True
        self.state = None
        self.change_state(TitleState)

    # ---------------- state machine ----------------

    def change_state(self, state_cls):
        self.state = state_cls(self)
        self.state.enter()

    # ---------------- session / level flow ----------------

    def new_run(self):
        self.player = Player(
            name="Hero", hp=60, atk=10, mag=12, mp=20, art=art.PLAYER_ART, color=cfg.CYAN
        )
        self.level_idx = 0
        self.start_level()

    def start_level(self):
        level = LEVELS[self.level_idx]
        self.enemy = level.create_enemy()
        self.player.reset_guard()
        self.log = []
        self.sound.stop_bgm()
        self.sound.play_bgm(level.bgm)
        self.change_state(IntroState)

    def begin_battle(self):
        self.change_state(BattleState)

    def next_level_or_win(self):
        self.level_idx += 1
        if self.level_idx >= len(LEVELS):
            self.change_state(WinGameState)
        else:
            self.player.restore_for_next_level()
            self.start_level()

    # ---------------- battle operations ----------------

    def add_log(self, message):
        self.log.append(message)
        self.log = self.log[-4:]

    def player_action(self, action):
        if self.action_lock or not self.player.alive or not self.enemy.alive:
            return

        self.player.reset_guard()
        message = None

        if action == "attack":
            message = self.player.attack(self.enemy, self.sound)
        elif action == "defend":
            message = self.player.defend(self.sound)
        elif action == "magic":
            message = self.player.cast_magic(self.enemy, self.sound)
            if message is None:
                self.add_log("Not enough MP!")
                return
        elif action == "item":
            message = self.player.use_item(self.sound)
            if message is None:
                self.add_log("No potions left!")
                return

        self.action_lock = True
        self.add_log(message)
        self.turn = "enemy"
        self.turn_timer = 0.7

    def enemy_turn(self):
        if not self.enemy.alive:
            return
        message = self.enemy.act(self.player, self.sound)
        self.add_log(message)
        self.player.regen_mp(2)
        self.turn = "player"
        self.action_lock = False

    def check_battle_end(self):
        if not self.enemy.alive:
            self.change_state(LevelWinState)
            return True
        if not self.player.alive:
            self.game_over_reason = f"You were defeated by the {self.enemy.name}."
            self.change_state(GameOverState)
            return True
        return False

    # ---------------- main loop ----------------

    def run(self):
        while self.running:
            dt = self.clock.tick(cfg.FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self.state.handle_event(event)

            self.state.update(dt)
            self.state.draw()
            pygame.display.flip()

        pygame.quit()
