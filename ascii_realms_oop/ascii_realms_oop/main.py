"""ASCII REALMS — A Battle RPG
Entry point. Run with: python main.py

Requires: pip install pygame-ce numpy
"""

import sys

from ascii_realms.game import Game


def main():
    game = Game()
    game.run()
    sys.exit()


if __name__ == "__main__":
    main()
