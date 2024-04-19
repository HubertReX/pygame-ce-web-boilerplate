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
FPS_CAP = 30
ANIMATION_SPEED = 10 # frames per second
WIDTH, HEIGHT = 900, 480
SHOW_DEBUG_INFO = False
SHOW_HELP_INFO = False
# FONT = "assets/homespun.ttf"
FONT = Path("assets") / "font.ttf"
SCREENSHOT_FOLDER = Path("..") / "screenshots"

TILE_SIZE = 32
SCALE = 1
USE_CUSTOM_CURSOR = False
ACTIONS = {
    'quit':       {"show": ["ESC", "q"], "msg": "back",       "keys": [pygame.K_ESCAPE,    pygame.K_q]},
    'debug':      {"show": ["`       "], "msg": "debug",      "keys": [pygame.K_BACKQUOTE]},
    'select':     {"show": None,         "msg": "select",     "keys": [pygame.K_SPACE]},
    'accept':     {"show": None,         "msg": "accept",     "keys": [pygame.K_RETURN]},
    'help':       {"show": ["F1", 'h'],  "msg": "help",       "keys": [pygame.K_F1,    pygame.K_h]},
    'screenshot': {"show": ([] if IS_WEB else ["F12"]),      "msg": "screenshot", "keys": [pygame.K_F12]},
    'reload':     {"show": ([] if IS_WEB else ["r "]),       "msg": "reload map", "keys": [pygame.K_r]},
    'zoom_in':    {"show": ["+ "],       "msg": "zoom in",    "keys": [pygame.K_EQUALS]},
    'zoom_out':   {"show": ["- "],       "msg": "zoom out",   "keys": [pygame.K_MINUS]},
    'left':       {"show": None,         "msg": "",           "keys": [pygame.K_LEFT,  pygame.K_a]},
    'right':      {"show": None,         "msg": "",           "keys": [pygame.K_RIGHT, pygame.K_d]},
    'up':         {"show": None,         "msg": "",           "keys": [pygame.K_UP,    pygame.K_w]},
    'down':       {"show": None,         "msg": "",           "keys": [pygame.K_DOWN,  pygame.K_s]},
    
    'scroll_up':   {"show": None,        "msg": "",           "keys": []},
    'left_click':  {"show": None,        "msg": "",           "keys": []},
    'right_click': {"show": None,        "msg": "",           "keys": []},
    'scroll_click':{"show": None,        "msg": "",           "keys": []},
}

INPUTS = {}
for key in ACTIONS.keys():
    INPUTS[key] = False
    

# define configuration variables here
CURRENT_DIR = Path(__file__).parent
RESOURCES_DIR = CURRENT_DIR / "assets" / "map"

# make loading images a little easier
def load_image(filename: str) -> Any:
    return pygame.image.load(str(RESOURCES_DIR / filename))

# MAP_PATH = RESOURCES_DIR / "grasslands.tmx"
# MAP_PATH = RESOURCES_DIR / "small.tmx"
