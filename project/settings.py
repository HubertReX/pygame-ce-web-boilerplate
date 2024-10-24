from collections import namedtuple
from dataclasses import dataclass
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Any, Sequence, Union

import pygame
from pygame.colordict import THECOLORS as COLORS
from pygame.math import Vector2 as vec
from pygame.math import Vector3 as vec3
from pytmx.pytmx import Point as pytmxPoint
from rich import inspect, pretty, print, traceback

help = partial(inspect, help=True, methods=True)
pretty.install()


VERSION = 0.1
GAME_NAME = "Misadventures of Malachi"
LANG = "EN"
ABOUT = [
    f"Version: {VERSION}",
    "Author: Hubert Nafalski",
    "WWW: https://hubertnafalski.itch.io/"
]

# custom type definition
# Point = namedtuple("Point", ["x", "y"])
# from pygame/_common.pyi
# ColorValue = Union[int, str, Sequence[int]]


@dataclass
class Point:
    x: int
    y: int

    @property
    def as_vector(self) -> vec:
        return vec(self.x, self.y)

    def __repr__(self) -> str:
        return f"MyPoint({self.x}, {self.y})"

    # def __add__(self, other: "Point") -> "Point":
    #     return Point(self.x + other.x, self.y + other.y)


def to_point(p: pytmxPoint) -> Point:
    return Point(int(p.x), int(p.y))


def to_vector(p: pytmxPoint) -> vec:
    return vec(int(p.x), int(p.y))


def tuple_to_vector(t: tuple[int | float, int | float]) -> vec:
    return vec(float(t[0]), float(t[1]))


def vector_to_tuple(v: vec) -> tuple[int, int]:
    return (int(v.x), int(v.y))


def lerp_vectors(v1: vec, v2: vec, t: float) -> vec:
    return v1 + (v2 - v1) * t


TILE_SIZE = 16
X_TILES = 80  # 100
Y_TILES = 45  # 64
SCALE = 1
WIDTH, HEIGHT = X_TILES * TILE_SIZE, Y_TILES * TILE_SIZE  # 80x45 => 1280x720 ; 100x64 => 1600x1024
WIDTH_SCALED, HEIGHT_SCALED = WIDTH * SCALE, HEIGHT * SCALE
FILTER_SCALE = 8
CIRCLE_RADIUS = 192 // FILTER_SCALE
# default camera zoom
ZOOM_LEVEL = 3.8
# camera zoom for intro cutscene (zooms out)
ZOOM_WIDE  = 3.10

USE_WEB_SIMULATOR = False
IS_WEB = __import__("sys").platform == "emscripten" or USE_WEB_SIMULATOR
IS_LINUX = __import__("sys").platform == "linux"
IS_FULLSCREEN = False
IS_PAUSED = False
USE_ALPHA_FILTER = True
USE_PARTICLES = False
USE_CUSTOM_MOUSE_CURSOR = True
USE_SOD = False
USE_SHADERS = False
SHOW_DEBUG_INFO = False
SHOW_HELP_INFO = False
SHOW_UI = True

# inventory slots count
MAX_HOTBAR_ITEMS = 6
# scale items by N to display in hotbar
INVENTORY_ITEM_SCALE = 4
# width (with padding) of hotbar slot
INVENTORY_ITEM_WIDTH = 22 * INVENTORY_ITEM_SCALE
# avatar (faceset) size in tiles
AVATAR_SCALE: int = 24

# game render fps cap
FPS_CAP = 0  # 130
# gameplay recording fps (doesn't need to be the same as FPS_CAP)
RECORDING_FPS = 30

# monsters will wake up when closer from player than this value
MONSTER_WAKE_DISTANCE = 100
# player will be able to talk to npc when in range of this distance
FRIENDLY_WAKE_DISTANCE = 25
# player will be able to open chest when in range of this distance
CHEST_OPEN_DISTANCE = 22
# path from monster will be recalculated
# only if player moved by more then N pixels
RECALCULATE_PATH_DISTANCE = 16
# path finding step costs used in map grid (path_finding_grid)
STEP_COST_WALL: int = 100
STEP_COST_GROUND: int = -100
# frames per second
ANIMATION_SPEED = 10
ANIMATION_SPEED_UI: int = 5
# when character speed is grater than this value, it's state changes to Run
RUN_SPEED: float = 39.0
# after how many seconds of Idle state player changes state to Bored
BORED_TIME: float = 4.0
# how long is NPC in stunned state [ms]
STUNNED_TIME: int = 800
# how long is NPC in pushed state [ms]
PUSHED_TIME: int = 1000

# initial game time hour
INITIAL_HOUR: int = 9
# game time speed (N game hours / 1 real time second)
GAME_TIME_SPEED: float = 0.25
# how many seconds a notification will be displayed
NOTIFICATION_DURATION: float = 10.0
# probability that NPC will rest [%]
SHOULD_NPC_REST_PROBABILITY: int = 15
# how long (min) will NPC rest [s]
NPC_MIN_REST_TIME: float = 1.0
# how long (max) will NPC rest [s]
NPC_MAX_REST_TIME: float = 3.0
# how many tiles on x and y axis from current position will NPC set as new target
NPC_RANDOM_WALK_DISTANCE: int = 3
# how many times will NPC try to find random safe position
# if exceeded - NPC will move to unsafe position
MAX_NO_ATTEMPTS_TO_FIND_RANDOM_POS: int = 100

TRANSPARENT_COLOR = (0, 0, 0, 0)
FULL_WHITE_COLOR = (255, 255, 255, 255)
FONT_COLOR = "white"
CHAR_NAME_COLOR = (255, 252, 103)
BLACK_COLOR = (0, 0, 0, 255)
# background fill color
BG_COLOR = (0, 0, 0, 0)
# HUD box border color
UI_BORDER_COLOR = (17, 17, 17, 255)
# HUD box border width
UI_BORDER_WIDTH = 9
# HUD border color when weapon switched
UI_BORDER_COLOR_ACTIVE = "gold"
# HUD box fill color when attacking
UI_COOL_OFF_COLOR = (223, 57, 76)

# render text panel background color
PANEL_BG_COLOR = (30, 30, 30, 200)
# cutscene framing background color
CUTSCENE_BG_COLOR = (10, 10, 10, 255)
# waypoint lines color
WAYPOINTS_LINE_COLOR = (0, 0, 128, 32)
# NPC stunned color
STUNNED_COLOR = (200, 0, 0, 64)
# cold, dark and bluish light at night
NIGHT_FILTER: tuple[int, int, int, int] = (0, 0, 30, 230)
# sunny, warm yellow light during daytime
DAY_FILTER: tuple[int, int, int, int] = (152, 152, 0, 0)
# amount of light sources passed to shader
MAX_LIGHTS_COUNT: int = 32

STYLE_TAGS_DICT: dict[str, str] = {
    "h1":        "{align center}{size 42}{cast_shadow True}",
    "h2":        "{align left}{size 36}{cast_shadow True}",
    "h3":        "{align left}{size 28}{cast_shadow True}",
    "shadow":    "{cast_shadow True}",
    "dark":      "{shadow_color (30,30,30)}",
    "light":     "{shadow_color (230,230,230)}",
    "bold":      "{bold True}",
    "b":         "{bold True}",
    "italic":    "{italic True}",
    "i":         "{italic True}",
    "underline": "{underline True}",
    "u":         "{underline True}",
    "link( +[^\\]]+)?": "{underline True}{link LINK_URL}",
    "big":       "{size 42}",
    "small":     "{size 12}",
    "left":      "{align left}",
    "right":     "{align right}",
    "center":    "{align center}",
    "act":       "{color (255,110,104)}",
    # "char":      "{color (255,252,103,255)}",
    "char":      "{color (255,252,103)}",
    "item":      "{color (104,113,255)}",
    "loc":       "{color (95,250,104)}",
    "num":       "{color (255,119,255)}",
    "quest":     "{color (96,253,255)}",
    "text":      "{color (0,197,199)}",
    "error":     "{color (223,57,76)}",
}


ACTIONS: dict[str, dict[str, Any]] = {
    "quit":   {"show": ["key_Esc", "key_Q"], "msg": "main menu",   "keys": [pygame.K_ESCAPE,    pygame.K_q]},
    "debug":  {"show": ["key_`", "key_Z"],   "msg": "debug",       "keys": [pygame.K_BACKQUOTE, pygame.K_z]},
    "alpha":  {"show": ["key_B"],            "msg": "filter",      "keys": [pygame.K_b]},
    # "shaders_toggle": {"show": ["g"],        "msg": "shader 0/1",  "keys": [pygame.K_g]},
    # "next_shader":    {"show": [".", ">"],   "msg": "next shader", "keys": [pygame.K_PERIOD]},
    "run":       {"show": ["key_Shift"], "msg": "toggle run",  "keys": [pygame.K_LSHIFT, pygame.K_RSHIFT]},
    "jump":      {"show": None,          "msg": "jump",        "keys": [pygame.K_SPACE]},
    "fly":       {"show": None,          "msg": "toggle fly",  "keys": [pygame.K_LALT, pygame.K_RALT]},
    "open":      {"show": ["key_Space"], "msg": "open",        "keys": [pygame.K_SPACE]},
    "attack":    {"show": ["key_Space"], "msg": "attack",      "keys": [pygame.K_SPACE]},
    "talk":      {"show": ["key_Space"], "msg": "talk",        "keys": [pygame.K_SPACE]},
    "pick_up":   {"show": ["key_E"],     "msg": "pick up",     "keys": [pygame.K_e]},
    "drop":      {"show": ["key_X"],     "msg": "drop",        "keys": [pygame.K_x]},
    "inventory": {"show": ["key_I"],     "msg": "inventory",   "keys": [pygame.K_i]},
    "next_item": {"show": None,          "msg": "next item",   "keys": [pygame.K_PERIOD]},
    "prev_item": {"show": None,          "msg": "prev item",   "keys": [pygame.K_COMMA]},
    "item_1":    {"show": None,          "msg": "item 1",      "keys": [pygame.K_1]},
    "item_2":    {"show": None,          "msg": "item 2",      "keys": [pygame.K_2]},
    "item_3":    {"show": None,          "msg": "item 3",      "keys": [pygame.K_3]},
    "item_4":    {"show": None,          "msg": "item 4",      "keys": [pygame.K_4]},
    "item_5":    {"show": None,          "msg": "item 5",      "keys": [pygame.K_5]},
    "item_6":    {"show": None,          "msg": "item 6",      "keys": [pygame.K_6]},
    "use_item":  {"show": ["key_F"],     "msg": "use item",    "keys": [pygame.K_f]},
    "select":    {"show": None,          "msg": "select",      "keys": [pygame.K_SPACE]},
    "accept":    {"show": None,          "msg": "accept",      "keys": [pygame.K_RETURN, pygame.K_KP_ENTER]},
    "help":      {"show": ["key_H"],     "msg": "show help",   "keys": [pygame.K_F1,     pygame.K_h]},
    "menu":      {"show": ["key_F2"],    "msg": "menu",        "keys": [pygame.K_F2]},
    "show_ui":   {"show": ["key_F3"],    "msg": "toggle UI",   "keys": [pygame.K_F3]},
    # "screenshot":     {"show": ["key_F9"],       "msg": "screenshot",  "keys": [pygame.K_F9]},
    "intro":     {"show": ["key_F4"],       "msg": "intro",       "keys": [pygame.K_F4]},
    # "record":         {"show": ([] if IS_WEB else ["key_F3"]), "msg":  "record mp4", "keys": [pygame.K_F3]},
    "reload":    {"show": ([] if IS_WEB else ["key_R"]), "msg":   "reload map", "keys": [pygame.K_r]},
    "zoom_in":   {"show": ["key_+"],     "msg": "zoom in",     "keys": [pygame.K_EQUALS, pygame.K_KP_PLUS]},
    "zoom_out":  {"show": ["key_-"],     "msg": "zoom out",    "keys": [pygame.K_MINUS, pygame.K_KP_MINUS]},
    "left":      {"show": None,          "msg": "",            "keys": [pygame.K_LEFT,  pygame.K_a]},
    "right":     {"show": None,          "msg": "",            "keys": [pygame.K_RIGHT, pygame.K_d]},
    "up":        {"show": None,          "msg": "",            "keys": [pygame.K_UP,    pygame.K_w]},
    "down":      {"show": None,          "msg": "",            "keys": [pygame.K_DOWN,  pygame.K_s]},
    "pause":     {"show": None,          "msg": "pause",       "keys": [pygame.K_F8]},

    "scroll_up":   {"show": None,          "msg": "",         "keys": []},
    "left_click":  {"show": ["mouse_LMB"], "msg": "go to",    "keys": []},
    "right_click": {"show": ["mouse_RMB"], "msg": "stop",     "keys": []},
    "scroll_click": {"show": None,          "msg": "",         "keys": []},
}

INPUTS: dict[str, float | bool] = {key: False for key in ACTIONS}
JOY_DRIFT: float = 0.25
JOY_MOVE_MULTIPLIER: float = 5
GAMEPAD_XBOX_CONTROL_NAMES: dict[str, dict[str, int]] = {
    "buttons": {
        "A":              0,
        "B":              1,
        "X":              2,
        "Y":              3,
        "context":        4,
        "xbox":           5,
        "settings":       6,
        "leftjoy_click":  7,
        "rightjoy_click": 8,
        "LB":             9,
        "RB":             10,
        "dpad_up":        11,
        "dpad_down":      12,
        "dpad_left":      13,
        "dpad_right":     14,

    },
    "axis": {
        "leftjoy_horizontal":  0,
        "leftjoy_vertical":    1,
        "rightjoy_horizontal": 2,
        "rightjoy_vertical":   3,
        "LT":                  4,
        "RT":                  5,
    }
}
GAMEPAD_STEAM_DECK_CONTROL_NAMES: dict[str, dict[str, int]] = {
    "buttons": {
        "A":               3,
        "B":               4,
        "X":               5,
        "Y":               6,
        "context":        11,
        "xbox":           13,
        "dots":            2,
        "settings":       12,
        "leftjoy_click":  14,
        "rightjoy_click": 15,
        "LB":              9,
        "RB":             10,
        "dpad_up":        16,
        "dpad_down":      17,
        "dpad_left":      18,
        "dpad_right":     19,

    },
    "axis": {
        "leftjoy_horizontal":  0,
        "leftjoy_vertical":    1,
        "rightjoy_horizontal": 2,
        "rightjoy_vertical":   3,
        "LT":                  4,
        "RT":                  5,
    }
}

GAMEPAD_WEB_CONTROL_NAMES: dict[str, dict[str, int]] = {
    "buttons": {
        "A":              0,
        "B":              1,
        "X":              2,
        "Y":              3,
        "context":        8,
        "xbox":           16,
        "settings":       9,
        "leftjoy_click":  10,
        "rightjoy_click": 11,
        "LB":             4,
        "RB":             5,
        "LT":             6,
        "RT":             7,
        "dpad_up":        12,
        "dpad_down":      13,
        "dpad_left":      14,
        "dpad_right":     15,

    },
    "axis": {
        "leftjoy_horizontal":  0,
        "leftjoy_vertical":    1,
        "rightjoy_horizontal": 2,
        "rightjoy_vertical":   3,
        "LT":                  4,
        "RT":                  5,
    }
}
# GAMEPAD_XBOX_CONTROL_NAMES_REV: dict[str, dict[int, str]] = {
#     "buttons": {
#         0:  "A",
#         1:  "B",
#         2:  "X",
#         3:  "Y",
#         4:  "context",
#         5:  "xbox",
#         6:  "settings",
#         7:  "leftjoy_click",
#         8:  "rightjoy_click",
#         9:  "LB",
#         10: "RB",
#         11: "dpad_up",
#         12: "dpad_down",
#         13: "dpad_left",
#         14: "dpad_right",

#     },
#     "axis": {
#         0: "leftjoy_horizontal",
#         1: "leftjoy_vertical",
#         2: "rightjoy_horizontal",
#         3: "rightjoy_vertical",
#         4: "LT",
#         5: "RT",
#     }
# }
GAMEPAD_XBOX_BUTTON2ACTIONS: dict[str, str] = {
    "A":          "attack",
    "B":          "use_item",
    "X":          "pick_up",
    "Y":          "drop",
    "context":    "run",
    "settings":   "quit",
    "LB":         "prev_item",
    "RB":         "next_item",
    "dpad_up":    "up",
    "dpad_down":  "down",
    "dpad_left":  "left",
    "dpad_right": "right",
}
GAMEPAD_XBOX_AXIS2ACTIONS: dict[str, tuple[str, str]] = {
    "leftjoy_horizontal": ("left", "right"),
    "leftjoy_vertical":   ("up",   "down"),
}
JOY_COOLDOWN: float = 0.15

# define configuration variables here
CURRENT_DIR = Path(__file__).parent
CONFIG_FILE = CURRENT_DIR / "config_model" / "config.json"
SCREENSHOTS_DIR = CURRENT_DIR if IS_WEB else CURRENT_DIR / ".." / "screenshots"
ASSETS_DIR = CURRENT_DIR / "assets"
# font_name = "font"
font_name = "font_pixel"
FONTS_PATH = ASSETS_DIR / "fonts"
MAIN_FONT = FONTS_PATH / f"{font_name}.ttf"
MENU_FONT = FONTS_PATH / "munro.ttf"

FONT_SIZES_DICT = {
    "font":       [8, 24, 38, 42, 55],
    "font_pixel": [10, 14, 16, 24, 155],
}
FONT_SIZE_TINY   = FONT_SIZES_DICT[font_name][0]
FONT_SIZE_SMALL  = FONT_SIZES_DICT[font_name][1]
FONT_SIZE_MEDIUM = FONT_SIZES_DICT[font_name][2]
FONT_SIZE_LARGE  = FONT_SIZES_DICT[font_name][3]
FONT_SIZE_HUGE   = FONT_SIZES_DICT[font_name][4]
FONT_SIZE_DEFAULT = FONT_SIZE_MEDIUM
TEXT_ROW_SPACING  = 1.4

ASSET_PACK        = "NinjaAdventure"
RESOURCES_DIR     = ASSETS_DIR / ASSET_PACK
DIALOGS_DIR       = ASSETS_DIR / "dialogs" / LANG
MAPS_DIR          = RESOURCES_DIR / "maps"
ITEMS_DIR         = RESOURCES_DIR / "items"
ITEMS_SHEET_FILE  = ITEMS_DIR / "items_trans_weapons.png"
GEMS_SHEET_FILE   = MAPS_DIR / "tilesets" / "images" / "TilesetNature.png"
MAZE_DIR          = ASSETS_DIR / "MazeTileset"
CHARACTERS_DIR    = RESOURCES_DIR / "characters"
PARTICLES_DIR     = RESOURCES_DIR / "particles"
HUD_DIR           = RESOURCES_DIR / "HUD"
HUD_SHEET_FILE    = HUD_DIR / "HUD.png"
EMOJIS_PATH       = RESOURCES_DIR / "Emote"
EMOTE_SHEET_FILE  = EMOJIS_PATH / "emote_all_anim.png"
PROGRAM_ICON      = ASSETS_DIR / "icon.png"
# MOUSE_CURSOR_IMG  = ASSETS_DIR / "aim.png"
MOUSE_CURSOR_IMG  = ASSETS_DIR / "pointer4.png"
# CIRCLE_GRADIENT   = HUD_DIR / "circle_gradient_big.png"
# LOGO_IMG          = HUD_DIR / "logo.png"
SHADERS_DIR = CURRENT_DIR / "shaders"
COMMON_SHADERS_DIR = SHADERS_DIR / "common"
if IS_WEB:
    SHADERS_DIR = SHADERS_DIR / "OpenGL3.0_ES"
else:
    SHADERS_DIR = SHADERS_DIR / "OpenGL3.3"

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

SPRITE_SHEET_DEFINITION_4x7: dict[str, list[tuple[int, int]]] = {
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

    "talk_down":    [(0, 0)],
    "talk_up":      [(1, 0)],
    "talk_left":    [(2, 0)],
    "talk_right":   [(3, 0)],
}

SPRITE_SHEET_DEFINITION_2x1: dict[str, list[tuple[int, int]]] = {
    "idle_down":    [(0, 0)],
    "idle_up":      [(0, 0)],
    # "idle_left":    [(0, 0)],
    "idle_right":   [(0, 0)],

    "run_down":     [(0, 0), (1, 0)],
    "run_up":       [(0, 0), (1, 0)],
    # "run_left":     [(2, 0), (2, 1), (2, 2), (2, 3)],
    "run_right":    [(0, 0), (1, 0)],


    "dead":         [(0, 0)],

    "bored":        [(0, 0)],

    "talk_down":    [(0, 0)],
    "talk_up":      [(0, 0)],
    # "talk_left":    [(2, 0)],
    "talk_right":   [(0, 0)],
}

SPRITE_SHEET_DEFINITION_3x3: dict[str, list[tuple[int, int]]] = {
    "idle_down":    [(1, 0)],
    "idle_up":      [(2, 0)],
    # "idle_left":    [(0, 0)],
    "idle_right":   [(0, 0)],

    "run_down":     [(1, 0), (1, 1), (1, 0), (1, 2)],
    "run_up":       [(2, 0), (2, 1), (2, 0), (2, 2)],
    # "run_left":     [(2, 0), (2, 1), (2, 0), (2, 2)],
    "run_right":    [(0, 0), (0, 1), (0, 0), (0, 2)],


    "dead":         [(0, 0)],

    "bored":        [(0, 0)],

    "talk_down":    [(0, 0)],
    "talk_up":      [(0, 0)],
    # "talk_left":    [(2, 0)],
    "talk_right":   [(0, 0)],
}

SPRITE_SHEET_DEFINITION_2x2: dict[str, list[tuple[int, int]]] = {
    "idle_down":    [(0, 0)],
    "idle_up":      [(0, 0)],
    # "idle_left":    [(0, 0)],
    "idle_right":   [(0, 0)],

    "run_down":     [(0, 0), (1, 0)],
    "run_up":       [(0, 1), (1, 1)],
    # "run_left":     [(2, 0), (2, 1), (2, 2), (2, 3)],
    "run_right":    [(0, 1), (1, 1)],


    "dead":         [(0, 0)],

    "bored":        [(0, 0)],

    "talk_down":    [(0, 0)],
    "talk_up":      [(0, 0)],
    # "talk_left":    [(2, 0)],
    "talk_right":   [(0, 0)],
}

SPRITE_SHEET_DEFINITION_RAIN: dict[str, list[tuple[int, int]]]  = {
    "rain":          [(0, 0), (1, 0), (2, 0)]
}

SPRITE_SHEET_DEFINITION_DESTRUCTIBLE_FOLIAGE: dict[str, list[tuple[int, int]]]  = {
    "foliage":          [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0)],
}
SPRITE_SHEET_DEFINITION_DESTRUCTIBLE_ROCK: dict[str, list[tuple[int, int]]]  = {
    "rock":             [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
                         (8, 0), (9, 0), (10, 0), (11, 0), (12, 0)],
}
SPRITE_SHEET_DEFINITION_LEAF: dict[str, list[tuple[int, int]]]  = {
    "foliage_left":          [(0, 0), (1, 0), (0, 0), (2, 0)],
    "foliage_right":         [(3, 0), (4, 0), (3, 0), (5, 0)],
}

SPRITE_SHEET_DEFINITION_ROCK: dict[str, list[tuple[int, int]]]  = {
    "rock_left":          [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
    "rock_right":         [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
}

SPRITE_SHEET_DEFINITIONS: dict[int, Any]  = {
    32: {
        "type": "2x1",
        "sheet": SPRITE_SHEET_DEFINITION_2x1,
        "tile_width": 16,
    },
    46: {
        "type": "2x2",
        "sheet": SPRITE_SHEET_DEFINITION_2x2,
        "tile_width": 23,
    },
    48: {
        "type": "3x3",
        "sheet": SPRITE_SHEET_DEFINITION_3x3,
        "tile_width": 16,
    },
    64: {
        "type": "4x7",
        "sheet": SPRITE_SHEET_DEFINITION_4x7,
        "tile_width": 16,
    },
    80: {
        "type": "4x7",
        "sheet": SPRITE_SHEET_DEFINITION_4x7,
        "tile_width": 16,
    },
}


HUD_SHEET_DEFINITION: dict[str, list[tuple[int, int]]] = {
    "key":       [(0, 0)],
    "key_Esc":   [(1, 0)],
    "key_Tab":   [(2, 0)],
    "key_Ctl":   [(3, 0)],
    "key_Alt":   [(0, 1)],
    "key_Enter": [(1, 1)],
    "key_Shift": [(2, 1)],
    "key_Space": [(3, 1)],
    "mouse":     [(0, 3)],
    "mouse_LMB": [(1, 3)],
    "mouse_RMB": [(2, 3)],
}

EMOTE_SHEET_DEFINITION = {
    "clear":                [(7, 7)],
    "empty":                [(0, 0)],
    "shocked":              [(2, 0)],
    "shocked_anim":         [(2, 0), (2, 0), (2, 0), (0, 2), (1, 0), ],
    "blessed":              [(6, 0)],
    "blessed_anim":         [(3, 0), (4, 0), (5, 0)],
    "love":                 [(0, 1)],
    "love_anim":            [(0, 1), (0, 1), (0, 1), (7, 0)],
    "angry":                [(1, 1)],
    "indifferent":          [(2, 1)],
    "happy":                [(3, 1)],
    "wondering":            [(4, 1)],
    "blink":                [(5, 1)],
    "blink_anim":           [(5, 1), (5, 1), (0, 2), (0, 2)],
    "doubt":                [(6, 1)],
    "frounce":              [(7, 1)],
    "smile":                [(0, 2)],
    "dreaming":             [(1, 2)],
    "sad":                  [(2, 2)],
    "neutral":              [(3, 2)],
    "dead":                 [(4, 2)],
    "miserable":            [(5, 2)],
    "offended":             [(6, 2)],
    "peaceful":             [(7, 2)],
    "evil":                 [(0, 3)],
    "dots":                 [(1, 3)],
    "dots_anim":            [(1, 3), (1, 3), (1, 3), (2, 3), (3, 3), (4, 3)],
    "exclamation":          [(5, 3)],
    "red_exclamation":      [(6, 3)],
    "red_exclamation_anim": [(6, 3), (7, 3), (6, 3), (0, 4)],
    "question":             [(1, 4)],
    "human":                [(2, 4)],
    "red_question":         [(3, 4)],
    "red_question_anim":    [(3, 4), (4, 4), (3, 4), (5, 4)],
    "broken_heart":         [(6, 4)],
    "broken_heart_anim":    [(7, 4), (0, 5), (1, 5), (1, 5), (1, 5)],
    "heart":                [(2, 5)],
    "heart_anim":           [(2, 5), (3, 5)],
    "zzz":                  [(4, 5)],
    "zzz_anim":             [(4, 5), (5, 5), (6, 5)],
    "star":                 [(7, 5)],
    "star_anim":            [(7, 5), (7, 5), (0, 6), (0, 6)],
    "cross":                [(1, 6)],
    "fight":                [(2, 6)],
    "fight_anim":           [(3, 6), (4, 6), (5, 6), (5, 6), (5, 6)],
    "walk":                 [(6, 6)],
    "A":                    [(7, 6)],
    "B":                    [(0, 7)],
    "X":                    [(1, 7)],
    "Y":                    [(2, 7)],
}

ITEMS_SHEET_DEFINITION = {
    "abacus":               [(1, 0)],
    "abacus2":              [(2, 0)],
    "name":                 [(3, 0)],
    "beef":                 [(1, 1)],
    "calamari":             [(2, 1)],
    "fish":                 [(3, 1)],
    "fortune_cookie":       [(4, 1)],
    "honey":                [(5, 1)],
    "noodle":               [(6, 1)],
    "octopus":              [(7, 1)],
    "onigiri":              [(8, 1)],
    "shrimp":               [(1, 2)],
    "sushi":                [(2, 2)],
    "sushi2":               [(3, 2)],
    "leaf":                 [(4, 2)],
    "shashlik":             [(5, 2)],
    "empty_pot":            [(6, 2)],
    "heart":                [(7, 2)],
    "life_pot":             [(8, 2)],
    "medic_pack":           [(1, 3)],
    "water_pot":            [(2, 3)],
    "milk_pot":             [(3, 3)],
    "scroll_empty":         [(4, 3)],
    "scroll_fire":          [(5, 3)],
    "scroll_ice":           [(6, 3)],
    "scroll_plant":         [(7, 3)],
    "scroll_rock":          [(8, 3)],
    "scroll_thunder":       [(1, 4)],
    "big_chest":            [(2, 4), (3, 4)],
    "golden_coin":          [(4, 4)],
    "golden_coin_anim":     [(4, 4),  (5, 4), (6, 4), (7, 4)],
    "hourglass":            [(8, 4)],
    "hourglass_2":          [(1, 5)],
    "small_chest":          [(2, 5), (3, 5)],
    "silver_coin":          [(4, 5)],
    "silver_cup":           [(5, 5)],
    "silver_key":           [(6, 5)],
    "golden_key":           [(7, 5)],
    "golden_cup":           [(8, 5)],
    "axe":                  [(1, 6)],
    "pitchfork":            [(2, 6)],
    "sai":                  [(3, 6)],
    "sword":                [(4, 6)],
    "lance":                [(5, 6)],
    "hammer":               [(6, 6)],
    "katana":               [(7, 6)],
    "rapier":               [(8, 6)],
    "stick":                [(1, 7)],
    "club":                 [(2, 7)],
    "pan_balance":          [(3, 7)],
    "pan_balance2":         [(4, 7)],
    "pan_balance3":         [(5, 7)],
    "big_heart":            [(6, 7)],
    "sword_short":          [(7, 7)],
    "sword_long":           [(8, 7)],
    "bow":                  [(3, 9)],
    "arrow":                [(4, 9)],
}

GEMS_SHEET_DEFINITION = {
    "gem_crystal_orange":   [(0, 14)],
    "gem_small_orange":     [(0, 15)],
    "gem_big_orange":       [(0, 16)],
    "gem_crystal_blue":     [(1, 14)],
    "gem_small_blue":       [(1, 15)],
    "gem_big_blue":         [(1, 16)],
    "gem_crystal_purple":   [(2, 14)],
    "gem_small_purple":     [(2, 15)],
    "gem_big_purple":       [(2, 16)],
    "gem_crystal_green":    [(3, 14)],
    "gem_small_green":      [(3, 15)],
    "gem_big_green":        [(3, 16)],
}

WEAPON_DIRECTION_OFFSET: dict[str, vec] = {
    "up":    vec(-3,         -10 - TILE_SIZE),
    "down":  vec(-2,          -2 + TILE_SIZE // 2),
    "left":  vec(-TILE_SIZE,   0 - TILE_SIZE // 2),
    "right": vec(TILE_SIZE,    1 - TILE_SIZE // 2)
}

WEAPON_DIRECTION_OFFSET_FROM: dict[str, vec] = {
    "up":    vec(-3, -10),
    "down":  vec(-2,  -2 - TILE_SIZE // 2),
    "left":  vec(0,    0 - TILE_SIZE // 2),
    "right": vec(0,    1 - TILE_SIZE // 2)
}

DIRECTIONS = ["up", "down", "left", "right"]


# make loading images a little easier
def load_image(filename: PathLike) -> Any:
    return pygame.image.load(str(RESOURCES_DIR / filename))


def import_sprite_sheet(
    path: str,
    tile_width: int = TILE_SIZE,
    tile_height: int = TILE_SIZE,
    sprite_sheet_definition: dict[str, list[tuple[int, int]]] = SPRITE_SHEET_DEFINITION_4x7,
    add_missing_directions: bool = True
) -> dict[str, list[pygame.surface.Surface]]:
    """
    Load sprite sheet and cut it into animation names and frames using `sprite_sheet_definition` dict.
    If provided sheet is missing some of the animations from dict, a frame from upper left corner (0, 0)
    will be used.
    If directional variants are missing (e.g.: only idle animation, but no idle left, idle right...)
    the general animation will be copied.
    """

    animations: dict[str, list[pygame.surface.Surface]] = {}
    img = pygame.image.load(path).convert_alpha()
    img_rect = img.get_rect()
    # use first tile (from upper left corner) as default 1 frame animation
    rec_def = pygame.Rect(0, 0, tile_width, tile_height)
    img_def = img.subsurface(rec_def)
    animation_def = [img_def]

    for key, definition in sprite_sheet_definition.items():
        animation = []
        for coord in definition:
            x, y = coord
            rec = pygame.Rect(x * tile_width, y * tile_height, tile_width, tile_height)
            if rec.colliderect(img_rect):
                img_part = img.subsurface(rec)
                animation.append(img_part)
            else:
                continue
                # print(f"ERROR! {self.name}: coordinate {x}x{y} not inside sprite sheet for {key} animation")

        animations[key] = animation or animation_def

        if add_missing_directions and "_" not in key:
            # if there is only one animation for each direction
            # that is when animation name doesn't include direction (e.g. 'idle')
            # than add reference in all directions (e.g. 'idle_up', 'idle_down',...)
            for direction in DIRECTIONS:
                new_key = f"{key}_{direction}"
                animations[new_key] = animations[key]

    new_animations: dict[str, list[pygame.surface.Surface]] = {}
    for key in animations:
        if "_" in key:
            state = key.split("_")[0]
            new_key = f"{state}_left"
            if new_key not in animations and new_key not in new_animations:
                new_animation = []
                for frame in animations[f"{state}_right"]:
                    new_animation.append(pygame.transform.flip(frame.copy(), True, False))
                new_animations[new_key] = new_animation
    animations.update(new_animations)

    return animations
