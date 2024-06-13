# inspired by:
# https://github.com/CodingQuest2023/Algorithms
from functools import partial
from pathlib import Path

import hunt_and_kill_maze
import pygame
import pyscroll
import pyscroll.data
import pytmx
from cell import *
from maze import Maze
from maze_utils import build_tileset_map_from_maze, get_gid_from_tmx_id
from pyscroll.group import PyscrollGroup
from pytmx.util_pygame import load_pygame
from rich import inspect, pretty, print, traceback

help = partial(inspect, help=True, methods=True)
pretty.install()
traceback.install(show_locals=True, width=150,)

WINDOW_WIDTH    = 1920
WINDOW_HEIGHT   = 1080
CELLSIZE        = 96       # cell width/height in pixels in tilesheet
SCALE_FACTOR    = 1
CELLSIZE_SCALED = CELLSIZE * SCALE_FACTOR
COLS = 10
ROWS = 7


MAPS_DIR = Path("..") / "assets" / "MazeTileset"
ZOOM_LEVEL = 1
IS_WEB = False
SHOW_OLD = False

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
    'scroll_click': {"show": None,        "msg": "",           "keys": []},
}

INPUTS = {}
for key in ACTIONS.keys():
    INPUTS[key] = False


class MazeDrawer:

    def __init__(self):
        self.maze = hunt_and_kill_maze.HuntAndKillMaze(COLS, ROWS)
        pygame.init()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        # open window
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)

        self.maze.generate()
        # load tile sheet, and extract the cell images
        self.tilesheet = pygame.image.load("../assets/MazeTileSet/MazeTileset_clean.png").convert_alpha()
        self.cell_images = []
        for y in range(4):
            for x in range(4):
                rect = (128 * x, 128 * y, CELLSIZE, CELLSIZE)
                image = self.tilesheet.subsurface(rect)
                image = pygame.transform.scale_by(image, (SCALE_FACTOR, SCALE_FACTOR))
                self.cell_images.append(image)

        image = self.tilesheet.subsurface((512, 128, 16, 16))
        self.wizard_image = pygame.transform.scale_by(image, (SCALE_FACTOR, SCALE_FACTOR))

        # center the maze
        self.maze_offset_x = (WINDOW_WIDTH - self.maze.num_cols * CELLSIZE_SCALED) // 2
        self.maze_offset_y = (WINDOW_HEIGHT - self.maze.num_rows * CELLSIZE_SCALED) // 2

        self.visited_cells = []
        self.highlight_surface = pygame.Surface((CELLSIZE_SCALED, CELLSIZE_SCALED))
        self.highlight_surface.set_alpha(50)
        self.highlight_surface.fill("yellow")
        self.darken_surface = pygame.Surface((CELLSIZE_SCALED, CELLSIZE_SCALED))
        self.darken_surface.set_alpha(100)
        self.darken_surface.fill("black")

        self.current_scene = "DummyLevel"
        self.tileset_map = load_pygame(MAPS_DIR / f"{self.current_scene}.tmx")

        self.layers = []
        for layer in self.tileset_map.layers:
            self.layers.append(layer.name)

        # clean_tileset_name = "MazeTileset_clean"
        self.tileset_map = load_pygame(MAPS_DIR / f"MazeTileset_clean.tmx")
        build_tileset_map_from_maze(self.tileset_map, self.maze)
        # self.convert_map()

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            data=pyscroll.data.TiledMapData(self.tileset_map),
            size=self.display_surface.get_size(),
            # camera stops at map borders (no black area around), player needs to be stopped separately
            clamp_camera=True,
        )
        self.map_layer.zoom = ZOOM_LEVEL

        # pyscroll supports layered rendering.  our map has 3 'under'
        # layers.  layers begin with 0.  the layers are 0, 1, and 2.
        # sprites are always drawn over the tiles of the layer they are
        # on.  since we want the sprite to be on top of layer 2, we set
        # the default layer for sprites as 2.
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=3)
        self.group.center(self.map_layer.map_rect.center)

    def generate_map(self):
        self.maze = hunt_and_kill_maze.HuntAndKillMaze(COLS, ROWS)
        self.maze.generate()
        # self.convert_map()
        self.tileset_map = load_pygame(MAPS_DIR / f"MazeTileset_clean.tmx")
        build_tileset_map_from_maze(self.tileset_map, self.maze)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            data=pyscroll.data.TiledMapData(self.tileset_map),
            size=self.display_surface.get_size(),
            # camera stops at map borders (no black area around), player needs to be stopped separately
            clamp_camera=True,
        )
        self.map_layer.zoom = ZOOM_LEVEL

        # pyscroll supports layered rendering.  our map has 3 'under'
        # layers.  layers begin with 0.  the layers are 0, 1, and 2.
        # sprites are always drawn over the tiles of the layer they are
        # on.  since we want the sprite to be on top of layer 2, we set
        # the default layer for sprites as 2.
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=1)
        self.group.center(self.map_layer.map_rect.center)

    def convert_map(self):
        margin = 3

        new_rows = [[0 for _ in range(self.maze.num_cols + (2 * margin))] for _ in range(margin)]

        for row in self.maze.cell_rows:
            new_cols = []
            for _ in range(margin):
                new_cols.append(0)

            for cell in row:
                # find the correct image for the cell
                index = 0
                allowed_moves = cell.get_allowed_moves()
                for dir in range(4):
                    if allowed_moves[dir]:
                        index += 2**dir
                col = index % 4
                row = index // 4
                img_index = (row * 5) + col

                new_cols.append(get_gid_from_tmx_id(img_index, self.tileset_map))

            for _ in range(margin):
                new_cols.append(0)

            new_rows.append(new_cols)

        for _ in range(margin):
            new_rows.append([0 for _ in range(self.maze.num_cols + (2 * margin))])

        self.tileset_map.get_layer_by_name("walls").data = new_rows
        floor_id = get_gid_from_tmx_id(4, self.tileset_map)
        floor_data = [[floor_id for _ in range(self.maze.num_cols + (2 * margin))]
                      for _ in range(self.maze.num_rows + (2 * margin))]
        self.tileset_map.get_layer_by_name("floor").data = floor_data
        self.tileset_map.get_layer_by_name("floor").width = self.maze.num_cols
        self.tileset_map.get_layer_by_name("floor").height = self.maze.num_rows
        self.tileset_map.get_layer_by_name("walls").width = self.maze.num_cols
        self.tileset_map.get_layer_by_name("walls").height = self.maze.num_rows
        self.tileset_map.width = self.maze.num_cols + (2 * margin)
        self.tileset_map.height = self.maze.num_rows + (2 * margin)

    def draw(self, select_cell: Cell | None = None, visit = True):
        if SHOW_OLD:
            self.draw_background()
            self.draw_cells(select_cell, visit)
            self.display_surface.blit(self.wizard_image, (1, 1))
        else:
            self.group.draw(self.display_surface)

    def wait_key(self):
        global SHOW_OLD
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                global WINDOW_WIDTH, WINDOW_HEIGHT
                WINDOW_WIDTH = event.w
                WINDOW_HEIGHT = event.h
                self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_SPACE:
                    SHOW_OLD = not SHOW_OLD
                    # print(f"{SHOW_OLD=}")
                elif event.key == pygame.K_r:
                    self.generate_map()
                else:
                    pygame.quit()
                    exit()

    def update(self, dt: float, events: list[pygame.event.EventType]):
        global INPUTS
        # self.update_sprites.update(dt)
        self.group.update(dt)

    def draw_cells(self, select_cell: Cell | None = None, visit = True):
        for cell in self.maze.get_all_cells():
            # Check which cell walls need to be drawn

            # x,y coords of the cell in pixels
            x = cell.x * CELLSIZE_SCALED
            y = cell.y * CELLSIZE_SCALED

            # find the correct image for the cell
            index = 0

            allowed_moves = cell.get_allowed_moves()
            for dir in range(4):
                if allowed_moves[dir]:
                    index += 2**dir

            self.display_surface.blit(self.cell_images[index], (x + self.maze_offset_x, y + self.maze_offset_y))

            # highlight the selected cell, and draw wizard in this cell
            if cell == select_cell:
                if visit:
                    self.visited_cells.append(cell)
                self.display_surface.blit(self.highlight_surface, (x + self.maze_offset_x, y + self.maze_offset_y))
                self.display_surface.blit(self.wizard_image, (x + self.maze_offset_x +
                                          CELLSIZE_SCALED // 2, y + self.maze_offset_y  + CELLSIZE_SCALED // 2))

            # make unvisited cells darker
            # if cell not in self.visited_cells and self.interactive:
            #     self.display_surface.blit(self.darken_surface, (x + self.maze_offset_x, y + self.maze_offset_y))

    def draw_background(self):
        image = self.tilesheet.subsurface((512, 0, CELLSIZE, CELLSIZE))
        image = pygame.transform.scale_by(image, (SCALE_FACTOR, SCALE_FACTOR))
        for y in range(WINDOW_HEIGHT // CELLSIZE_SCALED + 1):
            for x in range(WINDOW_WIDTH // CELLSIZE_SCALED + 1):
                self.display_surface.blit(image, (x * CELLSIZE_SCALED, y * CELLSIZE_SCALED))

    def loop(self):
        while True:
            dt = self.clock.tick(30) / 1000
            self.update(dt, [])
            self.draw()
            self.wait_key()
            pygame.display.flip()


if __name__ == "__main__":
    maze_drawer = MazeDrawer()
    maze_drawer.loop()
