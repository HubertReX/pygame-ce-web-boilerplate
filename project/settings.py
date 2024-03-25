from pygame.colordict import THECOLORS as COLORS
from pygame.math import Vector2 as vec
import pygame
from pathlib import Path

IS_FULLSCREEN = False
FPS_CAP = 30
ANIMATION_SPEED = 15 # frames per second
WIDTH, HEIGHT = 600, 320
DEBUG = True
# FONT = "assets/homespun.ttf"
FONT = "assets/font.ttf"
TILE_SIZE = 16
SCALE = 2
USE_CUSTOM_CURSOR = False
KEYS = [
    "quit",
    "select",
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
def load_image(filename: str) -> pygame.Surface:
    return pygame.image.load(str(RESOURCES_DIR / filename))

MAP_PATH = RESOURCES_DIR / "grasslands.tmx"
    