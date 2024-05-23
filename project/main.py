#!../.venv/bin/python
# /// script
# [project]
# name = "The Game"
# version = "0.1"
# description = "Boilerplate pygame-ce project for a top-down tiles sheet based RPG game that can run in the browser."
# readme = {file = "../README.md", content-type = "text/markdown"}
# requires-python = ">=3.11"
#
# dependencies = [
#  "numpy",
#  "pytmx",
#  "pyscroll",
#  "functools",
#  "rich",
#  "Pygments",
#  "zengl",
#  "struct",
#  "pathlib",
# ]
# ///
import random
import numpy as np
import asyncio
from game import Game
# 101 0017 # 106 0021 # 107 0030 no left down
seed = 107
random.seed(seed)
np.random.seed(seed)


def main():
    game = Game()
    asyncio.run(game.loop())


if __name__ == "__main__":
    main()
