"""Game screens, implemented as the classic State pattern.

GameState is an abstract base class defining the interface every screen
must provide: handle_event(), update(), draw(), and an optional enter()
hook run on transition. Game.change_state() swaps the active state, and
the main loop only ever talks to `self.state` polymorphically — it never
needs to know whether it's currently showing the title screen or a battle.
"""

import math
from abc import ABC, abstractmethod

import pygame

from . import config as cfg
from . import ascii_art as art
from .levels import LEVELS


class GameState(ABC):
    def __init__(self, game):
        self.game = game

    def enter(self):
        """Called once when this state becomes active. Override as needed."""

    @abstractmethod
    def handle_event(self, event):
        ...

    @abstractmethod
    def update(self, dt):
        ...

    @abstractmethod
    def draw(self):
        ...


class TitleState(GameState):
    def enter(self):
        self.game.sound.stop_bgm()
        self.game.sound.play_bgm("title")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.sound.play_sfx("select")
            self.game.sound.stop_bgm()
            self.game.new_run()

    def update(self, dt):
        pass

    def draw(self):
        r = self.game.renderer
        r.fill()
        t = pygame.time.get_ticks() / 1000
        for i, line in enumerate(art.TITLE_ART.split("\n")):
            color = tuple(
                max(0, min(255, c))
                for c in (
                    int(120 + 80 * math.sin(t * 2 + i)),
                    int(200 + 40 * math.sin(t * 2 + i + 1)),
                    int(140 + 60 * math.sin(t * 2 + i + 2)),
                )
            )
            r.draw_text(line, r.font_sm, color, cfg.WIDTH // 2, 60 + i * 16, align="center")
        r.draw_text(
            "A Battle RPG rendered entirely in text",
            r.font_md,
            cfg.GRAY,
            cfg.WIDTH // 2,
            190,
            align="center",
        )
        r.draw_ascii_block(art.PLAYER_ART, r.font_md, cfg.CYAN, 0, 260, center_x=cfg.WIDTH // 2 - 220)
        r.draw_ascii_block(art.GOBLIN_ART, r.font_md, cfg.RED, 0, 260, center_x=cfg.WIDTH // 2 + 220)
        if int(t * 2) % 2 == 0:
            r.draw_text("PRESS ENTER TO BEGIN", r.font_lg, cfg.YELLOW, cfg.WIDTH // 2, 470, align="center")
        r.draw_text("ESC to quit", r.font_sm, cfg.GRAY, cfg.WIDTH // 2, 590, align="center")


class IntroState(GameState):
    def enter(self):
        self.shown = 0
        self.timer = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            level = LEVELS[self.game.level_idx]
            if self.shown < len(level.intro):
                self.shown = len(level.intro)
                self.game.sound.play_sfx("select")
            else:
                self.game.sound.play_sfx("select")
                self.game.begin_battle()

    def update(self, dt):
        level = LEVELS[self.game.level_idx]
        self.timer += dt
        if self.timer > 0.9 and self.shown < len(level.intro):
            self.shown += 1
            self.timer = 0
            self.game.sound.play_sfx("move")

    def draw(self):
        r = self.game.renderer
        level = LEVELS[self.game.level_idx]
        r.fill()
        r.draw_text(level.title, r.font_lg, cfg.YELLOW, cfg.WIDTH // 2, 60, align="center")
        box = pygame.Rect(80, 160, cfg.WIDTH - 160, 300)
        r.draw_box(box, color=cfg.GRAY, fill=(14, 15, 22))
        y = box.y + 30
        for i in range(self.shown):
            for wl in r.wrap_text(level.intro[i], r.font_md, box.w - 60):
                r.draw_text(wl, r.font_md, cfg.WHITE, box.x + 30, y)
                y += 28
            y += 10
        if self.shown >= len(level.intro) and int(pygame.time.get_ticks() / 400) % 2 == 0:
            r.draw_text("Press ENTER to fight!", r.font_md, cfg.GREEN, cfg.WIDTH // 2, box.bottom - 40, align="center")
        r.draw_ascii_block(self.game.enemy.art, r.font_sm, self.game.enemy.color, 0, 480, center_x=cfg.WIDTH // 2)


class BattleState(GameState):
    MENU = [
        ("1. Attack", "attack"),
        ("2. Defend", "defend"),
        ("3. Magic (6MP)", "magic"),
        ("4. Item (Potion)", "item"),
    ]

    def enter(self):
        self.game.turn = "player"
        self.game.action_lock = False
        self.game.menu_index = 0
        self.game.log = []
        self.game.add_log(f"A wild {self.game.enemy.name} appears!")

    def handle_event(self, event):
        game = self.game
        if event.type != pygame.KEYDOWN:
            return
        if game.turn != "player" or game.action_lock:
            return

        if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
            game.menu_index = (game.menu_index - 1) % len(self.MENU)
            game.sound.play_sfx("move")
        elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
            game.menu_index = (game.menu_index + 1) % len(self.MENU)
            game.sound.play_sfx("move")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            game.player_action(self.MENU[game.menu_index][1])
        elif event.key == pygame.K_1:
            game.player_action("attack")
        elif event.key == pygame.K_2:
            game.player_action("defend")
        elif event.key == pygame.K_3:
            game.player_action("magic")
        elif event.key == pygame.K_4:
            game.player_action("item")

    def update(self, dt):
        game = self.game
        game.player.tick_effects()
        game.enemy.tick_effects()
        if game.turn == "enemy":
            game.turn_timer -= dt
            if game.turn_timer <= 0:
                if not game.check_battle_end():
                    game.enemy_turn()
                    game.check_battle_end()

    def draw(self):
        game = self.game
        r = game.renderer
        e, p = game.enemy, game.player
        r.fill()

        r.draw_text(LEVELS[game.level_idx].title, r.font_sm, cfg.GRAY, 20, 12)

        e_color = cfg.WHITE if e.flash > 0 else e.color
        p_color = cfg.WHITE if p.flash > 0 else p.color

        r.draw_hp_bar(cfg.WIDTH - 320, 60, 280, 20, e.hp, e.max_hp, cfg.RED, e.name)
        r.draw_ascii_block(e.art, r.font_md, e_color, 0, 100, center_x=cfg.WIDTH - 200, shake=e.shake)

        r.draw_hp_bar(40, 320, 260, 20, p.hp, p.max_hp, cfg.GREEN, p.name)
        r.draw_hp_bar(40, 366, 260, 14, p.mp, p.max_mp, cfg.BLUE, "MP")
        r.draw_ascii_block(p.art, r.font_md, p_color, 0, 400, center_x=180, shake=p.shake)
        if p.guarding:
            r.draw_text("[GUARDING]", r.font_sm, cfg.BLUE, 40, 300)

        log_box = pygame.Rect(40, 430, cfg.WIDTH - 80, 90)
        r.draw_box(log_box, color=cfg.GRAY, fill=(14, 15, 22))
        y = log_box.y + 8
        for line in game.log[-4:]:
            r.draw_text("> " + line, r.font_sm, cfg.WHITE, log_box.x + 12, y)
            y += 20

        menu_box = pygame.Rect(40, 530, cfg.WIDTH - 80, 90)
        r.draw_box(menu_box, color=cfg.GRAY, fill=(14, 15, 22))
        active = game.turn == "player" and not game.action_lock
        for i, (label, _) in enumerate(self.MENU):
            col_x = menu_box.x + 30 + (i % 2) * (menu_box.w // 2)
            row_y = menu_box.y + 12 + (i // 2) * 34
            color = cfg.YELLOW if (active and i == game.menu_index) else (cfg.WHITE if active else cfg.GRAY)
            prefix = "> " if (active and i == game.menu_index) else "  "
            r.draw_text(prefix + label, r.font_md, color, col_x, row_y)
        if not active:
            r.draw_text("Enemy turn...", r.font_sm, cfg.GRAY, menu_box.right - 140, menu_box.y - 20)


class LevelWinState(GameState):
    def enter(self):
        self.game.sound.play_sfx("levelwin")
        self.game.sound.stop_bgm()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.sound.play_sfx("select")
            self.game.next_level_or_win()

    def update(self, dt):
        pass

    def draw(self):
        r = self.game.renderer
        r.fill()
        r.draw_text("VICTORY!", r.font_xl, cfg.GREEN, cfg.WIDTH // 2, 180, align="center")
        r.draw_text(
            f"You defeated the {self.game.enemy.name}!",
            r.font_md,
            cfg.WHITE,
            cfg.WIDTH // 2,
            250,
            align="center",
        )
        r.draw_ascii_block(art.SLIME_HIT, r.font_lg, cfg.YELLOW, 0, 300, center_x=cfg.WIDTH // 2)
        if int(pygame.time.get_ticks() / 400) % 2 == 0:
            is_last = self.game.level_idx + 1 >= len(LEVELS)
            msg = "Press ENTER to finish your journey..." if is_last else "Press ENTER to continue..."
            r.draw_text(msg, r.font_md, cfg.YELLOW, cfg.WIDTH // 2, 420, align="center")


class GameOverState(GameState):
    def enter(self):
        self.game.sound.play_sfx("gameover_jingle")
        self.game.sound.stop_bgm()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.sound.play_sfx("select")
            self.game.change_state(TitleState)

    def update(self, dt):
        pass

    def draw(self):
        r = self.game.renderer
        r.fill()
        r.draw_text("GAME OVER", r.font_xl, cfg.RED, cfg.WIDTH // 2, 200, align="center")
        r.draw_text(self.game.game_over_reason, r.font_md, cfg.WHITE, cfg.WIDTH // 2, 270, align="center")
        if int(pygame.time.get_ticks() / 400) % 2 == 0:
            r.draw_text("Press ENTER to try again", r.font_md, cfg.YELLOW, cfg.WIDTH // 2, 360, align="center")
        r.draw_text("Press ESC to quit", r.font_sm, cfg.GRAY, cfg.WIDTH // 2, 400, align="center")


class WinGameState(GameState):
    def enter(self):
        self.game.sound.stop_bgm()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.game.sound.play_sfx("select")
            self.game.change_state(TitleState)

    def update(self, dt):
        pass

    def draw(self):
        r = self.game.renderer
        r.fill()
        r.draw_text("*** YOU ARE VICTORIOUS ***", r.font_lg, cfg.YELLOW, cfg.WIDTH // 2, 160, align="center")
        r.draw_text(
            "The realm is safe. Your legend is written in ASCII forevermore.",
            r.font_md,
            cfg.WHITE,
            cfg.WIDTH // 2,
            230,
            align="center",
        )
        r.draw_ascii_block(art.PLAYER_ART, r.font_lg, cfg.CYAN, 0, 300, center_x=cfg.WIDTH // 2)
        if int(pygame.time.get_ticks() / 400) % 2 == 0:
            r.draw_text("Press ENTER to play again", r.font_md, cfg.GREEN, cfg.WIDTH // 2, 500, align="center")
        r.draw_text("Press ESC to quit", r.font_sm, cfg.GRAY, cfg.WIDTH // 2, 540, align="center")
