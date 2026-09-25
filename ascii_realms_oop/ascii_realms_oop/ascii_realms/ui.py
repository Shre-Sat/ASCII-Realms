"""Rendering layer.

Renderer owns the screen surface and every font, and exposes small,
reusable drawing primitives (text, ASCII-art blocks, boxes, HP bars).
States call these instead of touching pygame drawing calls directly,
so all visual styling lives in one place.
"""

import random

import pygame

from . import config as cfg


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        font_path = pygame.font.match_font(
            "consolas,couriernew,dejavusansmono,monospace"
        )
        self.font_sm = pygame.font.Font(font_path, 14)
        self.font_md = pygame.font.Font(font_path, 18)
        self.font_lg = pygame.font.Font(font_path, 26)
        self.font_xl = pygame.font.Font(font_path, 40)

    def fill(self, color=cfg.BLACK):
        self.screen.fill(color)

    def draw_text(self, text, font, color, x, y, shadow=True, align="left"):
        img = font.render(text, True, color)
        rect = img.get_rect()
        if align == "left":
            rect.topleft = (x, y)
        elif align == "center":
            rect.midtop = (x, y)
        elif align == "right":
            rect.topright = (x, y)
        if shadow:
            sh = font.render(text, True, cfg.BLACK)
            self.screen.blit(sh, (rect.x + 2, rect.y + 2))
        self.screen.blit(img, rect)
        return rect

    def draw_ascii_block(self, lines, font, color, x, y, center_x=None, shake=0):
        for i, line in enumerate(lines):
            ox = random.randint(-shake, shake) if shake else 0
            oy = random.randint(-shake, shake) if shake else 0
            row_y = y + i * (font.get_height() + 2)
            if center_x is not None:
                img = font.render(line, True, color)
                rect = img.get_rect(midtop=(center_x + ox, row_y + oy))
                self.screen.blit(img, rect)
            else:
                self.draw_text(line, font, color, x + ox, row_y + oy, shadow=False)

    def draw_box(self, rect, color=cfg.GRAY, fill=cfg.PANEL, width=2):
        pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, color, rect, width)

    def draw_hp_bar(self, x, y, w, h, cur, mx, color, label):
        pct = 0 if mx <= 0 else max(0, cur / mx)
        self.draw_box((x, y, w, h), color=cfg.GRAY, fill=(25, 26, 34), width=1)
        inner_w = int((w - 4) * pct)
        bar_color = cfg.GREEN if pct > 0.5 else (cfg.YELLOW if pct > 0.2 else cfg.RED)
        if inner_w > 0:
            pygame.draw.rect(self.screen, bar_color, (x + 2, y + 2, inner_w, h - 4))
        self.draw_text(f"{label} {cur}/{mx}", self.font_sm, cfg.WHITE, x, y - 18)

    def wrap_text(self, text, font, max_w):
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] > max_w and cur:
                lines.append(cur)
                cur = w
            else:
                cur = test
        if cur:
            lines.append(cur)
        return lines
