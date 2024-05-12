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
#  "pydantic_core>=2.18.2",
#  "pydantic>=2.7.1",
# ]
# ///

import asyncio
from game import Game

def main():
    game = Game()    
    asyncio.run(game.loop())

if __name__ == "__main__":
    main()