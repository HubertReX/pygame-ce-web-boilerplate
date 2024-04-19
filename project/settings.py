from typing import Any
import pygame
from pygame.math import Vector2 as vec
from pygame.colordict import THECOLORS as COLORS
from pathlib import Path

# Need a flag to handle differently when game is run in desktop mode or in a web browser
IS_WEB = False
# local storage in web version for high score table
if __import__("sys").platform == "emscripten":
    IS_WEB = True

IS_FULLSCREEN = False
FPS_CAP = 130
ANIMATION_SPEED = 10 # frames per second
WIDTH, HEIGHT = 900, 480
DEBUG = True
# FONT = "assets/homespun.ttf"
FONT = Path("assets") / "font.ttf"
SCREENSHOT_FOLDER = Path("..") / "screenshots"

TILE_SIZE = 32
SCALE = 1
USE_CUSTOM_CURSOR = False
KEYS = [
    "quit",
    "select",
    "accept",
    "help",
    "screenshot",
    "left",
    "right",
    "up",
    "down",
    "scroll_up",
    "scroll_down",
    "left_click",
    "right_click",
    "scroll_click",
    "reload",
    "zoom_in",
    "zoom_out",
]
INPUTS = {}
for key in KEYS:
    INPUTS[key] = False
    

# define configuration variables here
CURRENT_DIR = Path(__file__).parent
RESOURCES_DIR = CURRENT_DIR / "assets" / "map"

# make loading images a little easier
def load_image(filename: str) -> Any:
    return pygame.image.load(str(RESOURCES_DIR / filename))

# MAP_PATH = RESOURCES_DIR / "grasslands.tmx"
# MAP_PATH = RESOURCES_DIR / "small.tmx"
