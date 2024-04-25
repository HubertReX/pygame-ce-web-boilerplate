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

import asyncio
from game import Game

if __name__ == "__main__":
    game = Game()    
    asyncio.run(game.loop())