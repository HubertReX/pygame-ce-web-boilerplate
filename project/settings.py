from collections import namedtuple
from typing import Any
from xml.etree.ElementTree import VERSION
import pygame
from pygame.math import Vector2 as vec
from pygame.colordict import THECOLORS as COLORS
from pathlib import Path

from functools import partial
from rich import inspect, pretty, print
from rich import traceback
help = partial(inspect, help=True, methods=True)
pretty.install()


VERSION = 0.1
GAME_NAME = "THE GAME"
ABOUT = [
    f'Version: {VERSION}',
    f'Author: Hubert Nafalski',
    f'WWW: https://hubertnafalski.itch.io/'
]

Point = namedtuple("Point", ["x", "y"])

WIDTH, HEIGHT = 1600, 1024
TILE_SIZE = 16
SCALE = 1
ZOOM_LEVEL = 3.25

# Need a flag to handle differently when game is run in desktop mode or in a web browser
IS_WEB = False
# local storage in web version for high score table
if __import__("sys").platform == "emscripten":
    IS_WEB = True

IS_FULLSCREEN = False
IS_PAUSED = False
USE_ALPHA_FILTER = False
USE_CUSTOM_CURSOR = False
USE_SHADERS = False
SHOW_DEBUG_INFO = False
SHOW_HELP_INFO = False

FPS_CAP = 30
ANIMATION_SPEED = 10 # frames per second
# when character speed is grater than this value, it's state changes to Run
RUN_SPEED: float = 39.0
# after how many seconds of Idle state player changes state to Bored
BORED_TIME: float = 4.0


ACTIONS = {
    'quit':       {"show": ["ESC", "q"], "msg": "back",       "keys": [pygame.K_ESCAPE,    pygame.K_q]},
    'debug':      {"show": ["`", "z"],   "msg": "debug",      "keys": [pygame.K_BACKQUOTE, pygame.K_z]},
    'alpha':      {"show": ["f"],        "msg": "filter",     "keys": [pygame.K_f]},
    'run':        {"show": ["CTRL"],     "msg": "toggle run", "keys": [pygame.K_LSHIFT, pygame.K_RSHIFT]},
    'jump':       {"show": ["SPACE"],    "msg": "jump",       "keys": [pygame.K_SPACE]},
    'fly':        {"show": ["SHIFT"],    "msg": "fly",        "keys": [pygame.K_LALT, pygame.K_RALT]},
    'select':     {"show": None,         "msg": "select",     "keys": [pygame.K_SPACE]},
    'accept':     {"show": None,         "msg": "accept",     "keys": [pygame.K_RETURN, pygame.K_KP_ENTER]},
    'help':       {"show": ["F1", 'h'],  "msg": "help",       "keys": [pygame.K_F1,    pygame.K_h]},
    'screenshot': {"show": ["F12"],      "msg": "screenshot", "keys": [pygame.K_F12]},
    'reload':     {"show": ([] if IS_WEB else ["r"]),       "msg": "reload map", "keys": [pygame.K_r]},
    'zoom_in':    {"show": ["+"],       "msg": "zoom in",    "keys": [pygame.K_EQUALS, pygame.K_KP_PLUS]},
    'zoom_out':   {"show": ["-"],       "msg": "zoom out",   "keys": [pygame.K_MINUS, pygame.K_KP_MINUS]},
    # 'quit':       {"show": ["ESC", "q"], "msg": "back",       "keys": [pygame.K_ESCAPE,    pygame.K_q]},
    # 'debug':      {"show": ["`", "z  "],   "msg": "debug",      "keys": [pygame.K_BACKQUOTE, pygame.K_z]},
    # 'run':        {"show": ["CTRL  "],     "msg": "toggle run", "keys": [pygame.K_LCTRL]},
    # 'jump':       {"show": ["SPACE "],    "msg": "jump",       "keys": [pygame.K_SPACE]},
    # 'select':     {"show": None,         "msg": "select",     "keys": [pygame.K_SPACE]},
    # 'accept':     {"show": None,         "msg": "accept",     "keys": [pygame.K_RETURN, pygame.K_KP_ENTER]},
    # 'help':       {"show": ["F1", 'h '],  "msg": "help",       "keys": [pygame.K_F1,    pygame.K_h]},
    # 'screenshot': {"show": ["F12   "],      "msg": "screenshot", "keys": [pygame.K_F12]},
    # 'reload':     {"show": ([] if IS_WEB else ["r     "]),       "msg": "reload map", "keys": [pygame.K_r]},
    # 'zoom_in':    {"show": ["+     "],       "msg": "zoom in",    "keys": [pygame.K_EQUALS, pygame.K_KP_PLUS]},
    # 'zoom_out':   {"show": ["-     "],       "msg": "zoom out",   "keys": [pygame.K_MINUS, pygame.K_KP_MINUS]},
    'left':       {"show": None,         "msg": "",           "keys": [pygame.K_LEFT,  pygame.K_a]},
    'right':      {"show": None,         "msg": "",           "keys": [pygame.K_RIGHT, pygame.K_d]},
    'up':         {"show": None,         "msg": "",           "keys": [pygame.K_UP,    pygame.K_w]},
    'down':       {"show": None,         "msg": "",           "keys": [pygame.K_DOWN,  pygame.K_s]},
    
    # 'pause':      {"show": None,        "msg": "",           "keys": []},
    
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
if IS_WEB:
    SCREENSHOTS_DIR = CURRENT_DIR 
else:
    SCREENSHOTS_DIR = CURRENT_DIR / ".." / "screenshots"
    
ASSETS_DIR = CURRENT_DIR / "assets"
# font_name = "font"
font_name = "font_pixel"
MAIN_FONT = ASSETS_DIR / "fonts" / f"{font_name}.ttf" # homespun

FONT_SIZES_DICT = {
    "font":       [24, 38, 55],
    "font_pixel": [12, 16, 155],
}
FONT_SIZE_SMALL  = FONT_SIZES_DICT[font_name][0]
FONT_SIZE_MEDIUM = FONT_SIZES_DICT[font_name][1]
FONT_SIZE_LARGE  = FONT_SIZES_DICT[font_name][2]
TEXT_ROW_SPACING  = 1.4 

ASSET_PACK = "NinjaAdventure"
RESOURCES_DIR = ASSETS_DIR / ASSET_PACK
MAPS_DIR = RESOURCES_DIR / "maps"
MAZE_DIR = ASSETS_DIR / "MazeTileset"
CHARACTERS_DIR = RESOURCES_DIR / "characters"
PARTICLES_DIR = RESOURCES_DIR / "particles"

PROGRAM_ICON = ASSETS_DIR / "icon.png"

SPRITE_SHEET_DEFINITION = {
    "idle_down":  [(0,0)],
    "idle_up":    [(1,0)],
    "idle_left":  [(2,0)],
    "idle_right": [(3,0)],
    
    "run_down":  [(0,0), (0,1), (0,2), (0,3)],
    "run_up":    [(1,0), (1,1), (1,2), (1,3)],
    "run_left":  [(2,0), (2,1), (2,2), (2,3)],
    "run_right": [(3,0), (3,1), (3,2), (3,3)],
    
    "weapon_down":  [(0,4)],
    "weapon_up":    [(1,4)],
    "weapon_left":  [(2,4)],
    "weapon_right": [(3,4)],
    
    "jump_down":  [(0,5)],
    "jump_up":    [(1,5)],
    "jump_left":  [(2,5)],
    "jump_right": [(3,5)],
    
    "dead":       [(0,6)],
    "item":       [(1,6)],
    "special1":   [(2,6)],
    "special2":   [(3,6)],

    "bored":      [(4,0), (4,1), (4,2), (4,3), (4,4), (4,5)],
        
}

# make loading images a little easier
def load_image(filename: str) -> Any:
    return pygame.image.load(str(RESOURCES_DIR / filename))

