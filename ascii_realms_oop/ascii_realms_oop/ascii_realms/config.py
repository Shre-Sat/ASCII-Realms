"""Static configuration: window size and color palette.

Kept free of any pygame calls that require pygame.init(), so this module
can be safely imported first by anything else in the package.
"""

WIDTH, HEIGHT = 960, 640
FPS = 60

BLACK = (8, 9, 14)
PANEL = (16, 18, 26)
GREEN = (70, 230, 130)
DGREEN = (30, 110, 60)
RED = (235, 80, 80)
DRED = (110, 30, 30)
YELLOW = (245, 220, 90)
WHITE = (225, 228, 235)
GRAY = (95, 100, 115)
BLUE = (90, 170, 245)
PURPLE = (190, 120, 240)
ORANGE = (240, 150, 70)
CYAN = (90, 230, 220)
