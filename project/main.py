#!../.venv/bin/python
# /// script
# [project]
# name = "The Game"
# version = "0.1"
# description = "Boilerplate pygame-ce project for a top-down tiles sheet based RPG game that can run in the browser."
# readme = {file = "../README.md", content-type = "text/markdown"}
# requires-python = ">=3.12"
#
# dependencies = [
#  "numpy",
#  "pillow",
#  "pytmx",
#  "pyscroll",
#  "functools",
#  "rich",
#  "Pygments",
#  "pathlib",
#  "pillow",
#  "thorpy",
# ]
# ///
import asyncio
import random
from rich import print, rule
from game import Game

# 101 0017 # 106 0021 # 107 0030 no left down
seed = 107
random.seed(seed)
# np.random.seed(seed)


def main() -> None:
    print(rule.Rule(title="[bright_yellow]START[/]", characters="#"))
    game = Game()
    asyncio.run(game.loop())
    print(rule.Rule(title="[bright_yellow]END[/]", characters="#"))


if __name__ == "__main__":
    main()
