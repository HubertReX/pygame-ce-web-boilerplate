from collections import namedtuple
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Any, Sequence, Union

import pygame
from pygame.colordict import THECOLORS as COLORS
from pygame.math import Vector2 as vec
from pygame.math import Vector3 as vec3
from rich import inspect, pretty, print, traceback

help = partial(inspect, help=True, methods=True)
pretty.install()


VERSION = 0.1
GAME_NAME = "THE GAME"
ABOUT = [
    f"Version: {VERSION}",
    "Author: Hubert Nafalski",
    "WWW: https://hubertnafalski.itch.io/"
]

# custom type definition
Point = namedtuple("Point", ["x", "y"])
# from pygame/_common.pyi
ColorValue = Union[int, str, Sequence[int]]

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
USE_CUSTOM_MOUSE_CURSOR = True
USE_SOD = False
USE_SHADERS = True
SHOW_DEBUG_INFO = False
SHOW_HELP_INFO = False

# game render fps cap
FPS_CAP = 30
# gameplay recording fps (doesn't need to be the same as FPS_CAP)
RECORDING_FPS = 30
# path from monster will be recalculated
# only if player moved by more then N pixels
RECALCULATE_PATH_DISTANCE = 16
# frames per second
ANIMATION_SPEED = 10
# when character speed is grater than this value, it's state changes to Run
RUN_SPEED: float = 39.0
# after how many seconds of Idle state player changes state to Bored
BORED_TIME: float = 4.0
# how long is NPC in stunned state [ms]
STUNNED_TIME: int = 1000
# how long is NPC in pushed state [ms]
PUSHED_TIME: int = 1000

# initial game time hour
INITIAL_HOUR = 1
# game time speed (N game hours / 1 real time second)
GAME_TIME_SPEED = 0.25

# background fill color
BG_COLOR = (0, 0, 0, 0)
# render text panel background color
PANEL_BG_COLOR = (10, 10, 10, 150)
# cutscene framing background color
CUTSCENE_BG_COLOR = (10, 10, 10, 255)
# waypoint lines color
WAYPOINTS_LINE_COLOR = (0, 0, 128, 32)
# NPC stunned color
STUNNED_COLOR = (200, 0, 0, 64)
# cold, dark and bluish light at night
NIGHT_FILTER: ColorValue = (0, 0, 30, 220)
# sunny, warm yellow light during daytime
DAY_FILTER: ColorValue = (152, 152, 0, 20)
# amount of light sources passed to shader
MAX_LIGHTS_COUNT: int = 16

ACTIONS = {
    "quit":           {"show": ["ESC", "q"], "msg": "back",        "keys": [pygame.K_ESCAPE,    pygame.K_q]},
    "debug":          {"show": ["`", "z"],   "msg": "debug",       "keys": [pygame.K_BACKQUOTE, pygame.K_z]},
    "alpha":          {"show": ["f"],        "msg": "filter",      "keys": [pygame.K_f]},
    "shaders_toggle": {"show": ["g"],        "msg": "shader 0/1",  "keys": [pygame.K_g]},
    "next_shader":    {"show": [".", ">"],   "msg": "next shader", "keys": [pygame.K_PERIOD]},
    "run":            {"show": ["CTRL"],     "msg": "toggle run",  "keys": [pygame.K_LSHIFT, pygame.K_RSHIFT]},
    "jump":           {"show": ["SPACE"],    "msg": "jump",        "keys": [pygame.K_SPACE]},
    "fly":            {"show": ["SHIFT"],    "msg": "toggle fly",  "keys": [pygame.K_LALT, pygame.K_RALT]},
    "select":         {"show": None,         "msg": "select",      "keys": [pygame.K_SPACE]},
    "accept":         {"show": None,         "msg": "accept",      "keys": [pygame.K_RETURN, pygame.K_KP_ENTER]},
    "help":           {"show": ["F1", "h"],  "msg": "help",        "keys": [pygame.K_F1,    pygame.K_h]},
    "menu":           {"show": ["F2"],       "msg": "menu",        "keys": [pygame.K_F2]},
    "screenshot":     {"show": ["F12"],      "msg": "screenshot",  "keys": [pygame.K_F12]},
    "intro":          {"show": ["F4"],       "msg": "intro",       "keys": [pygame.K_F4]},
    "record":         {"show": ([] if IS_WEB else ["F3"]), "msg":  "record mp4", "keys": [pygame.K_F3]},
    "reload":         {"show": ([] if IS_WEB else ["r"]), "msg":   "reload map", "keys": [pygame.K_r]},
    "zoom_in":        {"show": ["+"],        "msg": "zoom in",     "keys": [pygame.K_EQUALS, pygame.K_KP_PLUS]},
    "zoom_out":       {"show": ["-"],        "msg": "zoom out",    "keys": [pygame.K_MINUS, pygame.K_KP_MINUS]},
    "left":           {"show": None,         "msg": "",            "keys": [pygame.K_LEFT,  pygame.K_a]},
    "right":          {"show": None,         "msg": "",            "keys": [pygame.K_RIGHT, pygame.K_d]},
    "up":             {"show": None,         "msg": "",            "keys": [pygame.K_UP,    pygame.K_w]},
    "down":           {"show": None,         "msg": "",            "keys": [pygame.K_DOWN,  pygame.K_s]},

    "pause":          {"show": ["F8"],       "msg": "pause",       "keys": [pygame.K_F8]},

    "scroll_up":      {"show": None,            "msg": "",         "keys": []},
    "left_click":     {"show": ["Left click"],  "msg": "go to",    "keys": []},
    "right_click":    {"show": ["Right click"], "msg": "stop",     "keys": []},
    "scroll_click":   {"show": None,            "msg": "",         "keys": []},
}

INPUTS = {}
for key in ACTIONS.keys():
    INPUTS[key] = False


# define configuration variables here
CURRENT_DIR = Path(__file__).parent
CONFIG_FILE = CURRENT_DIR / "config_model" / "config.json"
if IS_WEB:
    SCREENSHOTS_DIR = CURRENT_DIR
else:
    SCREENSHOTS_DIR = CURRENT_DIR / ".." / "screenshots"

ASSETS_DIR = CURRENT_DIR / "assets"
# font_name = "font"
font_name = "font_pixel"
MAIN_FONT = ASSETS_DIR / "fonts" / f"{font_name}.ttf"

FONT_SIZES_DICT = {
    "font":       [8, 24, 38, 55],
    "font_pixel": [8, 12, 16, 155],
}
FONT_SIZE_TINY   = FONT_SIZES_DICT[font_name][0]
FONT_SIZE_SMALL  = FONT_SIZES_DICT[font_name][1]
FONT_SIZE_MEDIUM = FONT_SIZES_DICT[font_name][2]
FONT_SIZE_LARGE  = FONT_SIZES_DICT[font_name][3]
FONT_SIZE_DEFAULT = FONT_SIZE_MEDIUM
TEXT_ROW_SPACING  = 1.4

ASSET_PACK        = "NinjaAdventure"
RESOURCES_DIR     = ASSETS_DIR / ASSET_PACK
MAPS_DIR          = RESOURCES_DIR / "maps"
MAZE_DIR          = ASSETS_DIR / "MazeTileset"
CHARACTERS_DIR    = RESOURCES_DIR / "characters"
PARTICLES_DIR     = RESOURCES_DIR / "particles"
HUD_DIR           = RESOURCES_DIR / "HUD"
PROGRAM_ICON      = ASSETS_DIR / "icon.png"
MOUSE_CURSOR_IMG  = ASSETS_DIR / "aim.png"
CIRCLE_GRADIENT   = HUD_DIR / "circle_gradient_big.png"
if IS_WEB:
    SHADERS_DIR = Path("shaders") / "OpenGL3.0_ES"
else:
    SHADERS_DIR = Path("shaders") / "OpenGL3.3"

SHADERS_NAMES = [
    "RETRO_CRT",
    "SATURATED",
    "B_AND_W",
    "LIGHTING",
]
DEFAULT_SHADER = "LIGHTING"

# TODO: do not import particles (circular import) and use class name as string
import particles  # noqa: E402
PARTICLES = {
    "leafs": particles.ParticleLeafs,
    "rain": particles.ParticleRain,
}

SPRITE_SHEET_DEFINITION = {
    "idle_down":    [(0, 0)],
    "idle_up":      [(1, 0)],
    "idle_left":    [(2, 0)],
    "idle_right":   [(3, 0)],

    "run_down":     [(0, 0), (0, 1), (0, 2), (0, 3)],
    "run_up":       [(1, 0), (1, 1), (1, 2), (1, 3)],
    "run_left":     [(2, 0), (2, 1), (2, 2), (2, 3)],
    "run_right":    [(3, 0), (3, 1), (3, 2), (3, 3)],

    "weapon_down":  [(0, 4)],
    "weapon_up":    [(1, 4)],
    "weapon_left":  [(2, 4)],
    "weapon_right": [(3, 4)],

    "jump_down":    [(0, 5)],
    "jump_up":      [(1, 5)],
    "jump_left":    [(2, 5)],
    "jump_right":   [(3, 5)],

    "dead":         [(0, 6)],
    "item":         [(1, 6)],
    "special1":     [(2, 6)],
    "special2":     [(3, 6)],

    "bored":        [(4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)],
}


# make loading images a little easier
def load_image(filename: PathLike) -> Any:
    return pygame.image.load(str(RESOURCES_DIR / filename))
