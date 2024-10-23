import copy
import heapq
import random
import time
import itertools
from functools import partial, wraps
from typing import Any, Callable

import pytmx
from pygame.math import Vector2 as vec
from rich import inspect, pretty, print, traceback

from .maze import Maze
from .mappings import TILE_INDEX_TO_SYMBOL, TILE_INDEX_TO_GRID

help = partial(inspect, help=True, methods=True)
pretty.install()

SUBTILE_COLS      = 6
SUBTILE_GRID_COLS = 4
SUBTILE_COLS_SEP  = 2
SUBTILE_COLS_OFFSET = SUBTILE_COLS + SUBTILE_COLS_SEP

SUBTILE_ROWS      = 6
SUBTILE_GRID_ROWS = 4
SUBTILE_ROWS_SEP  = 2
SUBTILE_ROWS_OFFSET = SUBTILE_ROWS + SUBTILE_ROWS_SEP

ENTRY_X_OFFSET = 3
ENTRY_Y_OFFSET = 3

X_CENTER = 3
Y_CENTER = 4

# RE_ENTRY_X_OFFSET = 3
# RE_ENTRY_Y_OFFSET = 5

RETURN_X_OFFSET = 3
RETURN_Y_OFFSET = 1

# STAIRS_DOWN_X_OFFSET = 4
# STAIRS_DOWN_Y_OFFSET = 4

# STAIRS_UP_X_OFFSET = 1
# STAIRS_UP_Y_OFFSET = 4

WALLS_DECORS_OFFSET_RANGE_X = 2
WALLS_DECORS_OFFSET_RANGE_Y = 1

EMPTY_CELL       = 0
BACKGROUND_CELL  = 231
RETURN_CELL      = 33  # 332
# STAIRS_DOWN_CELL = 50  # 184 # 200
# STAIRS_UP_CELL   = 16  # 184  # 200

# background decors (holes, gray stones)
BACKGROUND_DECORS_MAX = 80
# BACKGROUND_DECORS_IDS = [12, 24]

# elements on floor (dead rat, barrel, crate, stool)
ELEMENTS_MAX = 12

# map image_index to offset of elements
ELEMENTS_OFFSETS_MAP = {
    14: vec(1, 2),
    13: vec(4, 2),
    11: vec(2, 2),
    10: vec(2, 2),
    9:  vec(4, 2),
    7:  vec(4, 4),
    6:  vec(1, 4),
    5:  vec(4, 4),
}

# wall decors(bars, banner, glyph)
WALL_DECORS_MAX = 8

# floor decors (dirt, gray stones)
# FLOOR_DECORS_IDS = [49, 42]
ITEMS_MAX_COUNT = {
    "golden_coin": 2,
    "life_pot": 2,
    "axe": 1,
    "sword_short": 1,
    "sword_long": 1
}

MARGIN = 3

TILE_SIZE = 16

#######################################
#         analyze maze const          #
#######################################
STEP_COST_WALL: int   = 100
STEP_COST_GROUND: int = 0

DIVIDER = 4

FROM_NORTH =  7
FROM_SOUTH = 11
FROM_WEST  = 13
FROM_EAST  = 14

DEAD_ENDS = [FROM_NORTH, FROM_SOUTH, FROM_EAST, FROM_WEST]

IMAGE_DIRECTION_TO_POS_OFFSET = {
    FROM_NORTH: (3, 4),
    FROM_SOUTH: (3, 4),
    FROM_WEST:  (3, 4),
    FROM_EAST:  (2, 4),
}

IMAGE_DIRECTION_TO_OFFSET = {
    FROM_NORTH: (3, 4),
    FROM_SOUTH: (3, 2),
    FROM_WEST:  (4, 3),
    FROM_EAST:  (1, 3),
}

IMAGE_DIRECTION_TO_CHEST = {
    FROM_NORTH: (4, 4),
    FROM_SOUTH: (4, 2),
    FROM_WEST:  (4, 4),
    FROM_EAST:  (1, 4),
}


# IMAGE_DIRECTION_TO_IDX = {
#     "stairs_up": {
#         FROM_NORTH: 50,
#         FROM_SOUTH: 52,
#         FROM_WEST:  56,
#         FROM_EAST:  16,
#     },
#     "stairs_down": {
#         FROM_NORTH: 51,
#         FROM_SOUTH: 53,
#         FROM_WEST:  57,
#         FROM_EAST:  54,
#     },
# }

IMAGE_DIRECTION_TO_IDX = {
    "stairs_up": {
        FROM_NORTH: 20,
        FROM_SOUTH: 21,
        FROM_WEST:  22,
        FROM_EAST:  23,
    },
    "stairs_down": {
        FROM_NORTH: 16,
        FROM_SOUTH: 17,
        FROM_WEST:  18,
        FROM_EAST:  19,
    },
}

STAIRS_TILES_POS = {
    "stairs_up": {
        FROM_NORTH: (32, 9),
        FROM_SOUTH: (33, 9),
        FROM_WEST:  (34, 9),
        FROM_EAST:  (35, 9),
    },
    "stairs_down": {
        FROM_NORTH: (32, 8),
        FROM_SOUTH: (33, 8),
        FROM_WEST:  (34, 8),
        FROM_EAST:  (35, 8),
    },
}

# STAIRS_TYPES_IDX = {
#     "stairs_up": {
#         "north": 50,
#         "south": 52,
#         "west":  16,
#         "east":  56,
#     },
#     "stairs_down": {
#         "north": 53,
#         "south": 51,
#         "east":  54,
#         "west":  57,
#     },
# }

GRID_FACTOR = 3

# dict of results of a_star function
# key is a tuple of start and goal coordinates
# value is a list of coordinates to go through
_CACHE: dict[tuple[tuple[int, int], tuple[int, int]], list[tuple[int, int]]] = {}
_sum: float = 0.0
_cnt: int = 0
_TIMEIT_CACHE = {}
#######################################################################################################################


def timeit(func: Callable) -> Callable:

    @wraps(func)
    def timeit_wrapper(*args: Any, **kwargs: Any) -> Any:
        global _sum, _cnt

        start_time = time.time_ns()  # perf_counter()
        result = func(*args, **kwargs)
        end_time = time.time_ns()  # perf_counter()
        total_time = end_time - start_time
        # func.add_execute_time(total_time)
        fun_name = repr(func).split(" ")[1]
        _cnt, _sum = _TIMEIT_CACHE.get(fun_name, (0, 0.0))
        _cnt += 1
        _sum += total_time
        _TIMEIT_CACHE[fun_name] = (_cnt, _sum)
        # if _cnt % 50 == 0:
        #     print(f"{fun_name};{_sum / _cnt:.10f}")  # {_sum=} {_cnt=}

        # el = float(kwargs["fps"][-4:])
        # if el <= 10.00:
        #     print(f'{func.__name__} {str(kwargs["start"]):8}
        # {str(kwargs["goal"]):8} duration:\t{total_time:.5f}\tAvg_time:\t{
        #           _sum / _cnt:.4f}\tcnt:\t{_cnt}\tCache_size:\t{len(_CACHE)}\t{kwargs["fps"]}'.replace(".", ","))
        return result
    return timeit_wrapper

#######################################################################################################################


# @timeit
def a_star_cached(
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    fps: str = ""
) -> list[tuple[int, int]]:
    global _CACHE  # , _sum, _cnt

    key = (start, goal)  # create_key(start, goal)

    if key not in _CACHE:
        if res := a_star(grid, start, goal):
            _CACHE[key] = res
            for i, wp in enumerate(res):
                new_key = (wp, goal)
                if new_key not in _CACHE:
                    _CACHE[new_key] = res[i:]
        else:
            # print(f"[red]ERROR[/] a* miss {key} - no route to destination?")
            return []
    #     fps += "\t[red]miss[/]"
    # else:
    #     fps += "\t[green]hit[/]"
    return _CACHE[key]


def clear_maze_cache() -> None:
    # del _CACHE
    global _CACHE, _sum, _cnt
    # print(f"Cache size was: {len(_CACHE)} {_sum=:.4f} {_cnt=}")
    _CACHE = {}
    _sum = 0.0
    _cnt = 0

# def is_diagonal(p)

#######################################################################################################################


def a_star(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]] | None:
    # MARK: A*
    def heuristic(point: tuple[int, int], goal: tuple[int, int]) -> int:
        # Manhattan distance heuristic
        return abs(point[0] - goal[0]) + abs(point[1] - goal[1])

    def safe_get_grid(x: int, y: int) -> int:
        if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
            return grid[x][y]
        else:
            return 1

    # https://panda-man.medium.com/a-pathfinding-algorithm-efficiently-navigating-the-maze-of-possibilities-8bb16f9cecbd
    # (score, (x, y))
    open_set: list[tuple[int, tuple[int, int]]] = []

    # Priority queue with (F-score, node)
    heapq.heappush(open_set, (0, start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], int] = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct the path and return
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        # 8 dir
        for d in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1),):

            # 4 dir
            # for d in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            dx, dy = d
            is_diagonal = (abs(dx) + abs(dy)) > 1
            x, y = current[0] + dx, current[1] + dy
            neighbor = (x, y)

            # Assuming uniform cost for each step
            # tentative_g = g_score[current] + 1
            # orthogonal move cost == 100 diagonal move cost == sqrt(2)
            # node with negative value indicates custom step cost (e.g. water = -200)
            if not is_diagonal:
                cost = abs(safe_get_grid(x, y))
            else:
                cost = g_score[current] + int(abs(safe_get_grid(x, y) * 1.41))
            tentative_g = g_score[current] + cost

            # move permitted if new node is not blocked
            # move_permitted = grid[x][y] == 0

            # all orthogonal moves are permitted, orthogonal move permitted only if not passing blocked corner
            # e.g. move from S to G (X == blocked)
            #    |   |
            # ---+---+---
            #    | S |       Permitted
            # ---+---+---
            #  G |   |

            #    |   |
            # ---+---+---
            #    | S |       Not permitted
            # ---+---+---
            #  G | X |

            #    |   |
            # ---+---+---
            #  X | S |       Not permitted
            # ---+---+---
            #  G |   |

            if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
                move_permitted = grid[x][y] <= 0 if not is_diagonal else (
                    grid[x][y] <= 0 and grid[x][current[1]] <= 0 and grid[current[0]][y] <= 0)
                if move_permitted:
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + heuristic(neighbor, goal) * 100
                        heapq.heappush(open_set, (f_score, neighbor))
                        came_from[neighbor] = current

    return None  # No path found

# # Example usage:
# grid = [
#     [0, 0, 0, 0],
#     [0, 1, 1, 0],
#     [0, 1, 0, 0],
#     [0, 0, 0, 0]
# ]

# start = (0, 0)
# goal = (3, 3)

# path = a_star(grid, start, goal)
# print("Shortest path:", path)

#######################################
#      analyze maze functions         #
#######################################


def print_maze(maze: Maze, path: list[tuple[int, int]] | None = None) -> None:
    if not path:
        path = []

    for cell in maze.get_all_cells(start_from_top_row=True):
        if cell.x == 0:
            print("")
        # cell.x > maze_cols // DIVIDER and cell.y > maze_rows // DIVIDER and
        if (cell.x, cell.y) == path[0]:
            color = "bright_red"
        elif (cell.x, cell.y) == path[-1]:
            color = "red"
        elif cell.image_index in DEAD_ENDS:
            color = "bright_yellow"
        elif (cell.x, cell.y) in path:
            color = "bright_cyan"
        else:
            color = "white"

        # print(f"[{color}]{cell.image_index:3}[/]", sep=" ", end="")
        print(f"[{color}]{TILE_INDEX_TO_SYMBOL[cell.image_index]}[/]", sep=" ", end="")

    print("")

#######################################################################################################################


def find_dead_ends(maze: Maze) -> list[tuple[int, int]]:
    candidates = []
    for cell in maze.get_all_cells():
        # cell.x > maze_cols // DIVIDER and cell.y > maze_rows // DIVIDER and
        if cell.image_index in DEAD_ENDS:
            candidates.append((cell.x, cell.y))

    return candidates


#######################################################################################################################

def find_tiles_with_N_wall(maze: Maze) -> list[tuple[int, int]]:
    candidates = []
    for cell in maze.get_all_cells():
        # all tiles that have solid wall to the north
        # happen to have image_index lower than 7
        if cell.image_index > 7:
            candidates.append((cell.x, cell.y))

    return candidates


#######################################################################################################################

def find_tiles_with_cross_way(maze: Maze) -> list[tuple[int, int]]:
    candidates = []
    for cell in maze.get_all_cells():
        # all T-shaped and a 4-way crossing
        if cell.image_index in (0, 1, 2, 4, 8):
            candidates.append((cell.x, cell.y))

    return candidates


#######################################################################################################################

def generate_grid(maze: Maze) -> list[list[int]]:
    path_finding_grid: list[list[int]] = [[STEP_COST_GROUND for _ in range(len(maze.cell_rows[0]) * GRID_FACTOR)]
                                          for _ in range(len(maze.cell_rows) * GRID_FACTOR)]
    for y, row in enumerate(maze.cell_rows):
        for x, cell in enumerate(row):
            tile_index = TILE_INDEX_TO_GRID[cell.image_index]
            copy_subtile(path_finding_grid, x * GRID_FACTOR, y * GRID_FACTOR, tile_index)

    return path_finding_grid

#######################################################################################################################


def scale_step(step: tuple[int, int]) -> tuple[int, int]:
    return (1 + step[1] * GRID_FACTOR, 1 + step[0] * GRID_FACTOR)

#######################################################################################################################


def fix_path(path: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not path:
        print("[red]ERROR[/] No path!")
        return []
    fixed_path: list[tuple[int, int]] = []
    fixed_path.append((path[0][1] // GRID_FACTOR, path[0][0] // GRID_FACTOR))
    for step in path:
        new_step = (step[1] // GRID_FACTOR, step[0] // GRID_FACTOR)
        if not fixed_path[-1] == new_step:
            fixed_path.append(new_step)
    return fixed_path

#######################################################################################################################


def analyze_maze(maze: Maze) -> dict[str, Any]:
    stats: dict[str, Any] = {}

    path_finding_grid = generate_grid(maze)
    dead_ends = find_dead_ends(maze)

    if len(dead_ends) == 0:
        print("[red]ERROR[/] no 'dead end' tiles!")
        exit()

    dead_ends_pairs = itertools.combinations(dead_ends, 2)
    dead_end_paths = []
    dead_end_paths_len = []
    for dead_ends_pair in dead_ends_pairs:
        start = scale_step(dead_ends_pair[0])
        goal = scale_step(dead_ends_pair[1])
        path = fix_path(a_star(start=start, goal=goal, grid=path_finding_grid))
        dead_end_paths.append(path)
        dead_end_paths_len.append(len(path))

    tiles_with_N_wall = find_tiles_with_N_wall(maze)

    if len(tiles_with_N_wall) == 0:
        print("[red]ERROR[/] no tiles with Northern wall")
        exit()

    n_wall_with_dead_end_paris = []
    for tile_with_N_wall in tiles_with_N_wall:
        for dead_end in dead_ends:
            if not tile_with_N_wall == dead_end:
                n_wall_with_dead_end_paris.append((tile_with_N_wall, dead_end))

    from_N_wall_paths = []
    from_N_wall_paths_len = []
    for n_wall_with_dead_end_pair in n_wall_with_dead_end_paris:
        start = scale_step(n_wall_with_dead_end_pair[0])
        goal = scale_step(n_wall_with_dead_end_pair[1])
        path = fix_path(a_star(start=start, goal=goal, grid=path_finding_grid))
        from_N_wall_paths.append(path)
        from_N_wall_paths_len.append(len(path))

    # print(
    #     f"count end points {len(candidates):2d}",
    #     # f"count paths {len(paths):2d}",
    #     # f"min {min(paths_len):2d}",
    #     # f"avg {(sum(paths_len) / len(paths_len)):2.1f}",
    #     f"max {max(paths_len):2d}",
    #     f"sum {sum(paths_len):4d}",
    # )

    # simple maze
    if len(dead_ends) < 8 and sum(dead_end_paths_len) < 600:  # and max(paths_len) < 40:
        stats["is_simple"] = True
    else:
        stats["is_simple"] = False

    # hard maze
    if len(dead_ends) > 9 and sum(dead_end_paths_len)  > 900:  # or max(paths_len) > 45:
        stats["is_hard"] = True
    else:
        stats["is_hard"] = False

    stats["dead_ends"] = dead_ends
    stats["dead_ends_count"] = len(dead_ends)
    stats["dead_end_paths"] = dead_end_paths
    stats["dead_end_paths_lengths"] = dead_end_paths_len
    longest_dead_end_path          = dead_end_paths[dead_end_paths_len.index(min(dead_end_paths_len))]
    stats["longest_dead_end_path"] = longest_dead_end_path
    stats["longest_dead_end_path_start"] = longest_dead_end_path[0]
    stats["longest_dead_end_path_end"] = longest_dead_end_path[-1]
    stats["longest_dead_end_path_len"] = len(longest_dead_end_path)
    stats["sum_all_dead_end_paths"] = sum(dead_end_paths_len)

    # TODO: revert after finished
    longest_N_wall_path          = from_N_wall_paths[from_N_wall_paths_len.index(min(from_N_wall_paths_len))]
    stats["longest_N_wall_path"] = longest_N_wall_path
    stats["longest_N_wall_path_start"] = longest_N_wall_path[0]
    stats["longest_N_wall_path_end"] = longest_N_wall_path[-1]
    stats["longest_N_wall_path_len"] = len(longest_N_wall_path)

    # from_N_wall_paths
    return stats


#######################################
#      build map functions            #
#######################################

def copy_subtile(new_data: list[list[int]], x: int, y: int, subtile_sheet: list[list[int]]) -> None:
    rows = len(subtile_sheet)
    cols = len(subtile_sheet[0])
    for row in range(rows):
        for col in range(cols):
            new_data[y + row][x + col] = subtile_sheet[row][col]

#######################################################################################################################


def get_gid_from_tmx_id(tmx_id: int, tileset_map: pytmx.TiledMap) -> int:
    gid_tuple = tileset_map.gidmap[tmx_id + 1]

    if len(gid_tuple):
        return gid_tuple[0][0]
    else:
        print(f"[red]ERROR[/] GID for {tmx_id} not found!")
        # print(tileset_map.gidmap)
        return 0

#######################################################################################################################


def make_layer(layer: pytmx.TiledTileLayer, maze: Maze, new_cols_cnt: int, new_rows_cnt: int) -> None:

    subtile_sheet_dict = {}
    for y in range(SUBTILE_GRID_ROWS):
        for x in range(SUBTILE_GRID_COLS):
            subtile = []
            for subtile_y in range(SUBTILE_ROWS):
                subtile_row = []
                for subtile_x in range(SUBTILE_COLS):
                    subtile_row.append(layer.data[subtile_y + (y * SUBTILE_ROWS_OFFSET)]
                                       [subtile_x + (x * SUBTILE_COLS_OFFSET)])
                subtile.append(subtile_row)

            subtile_sheet_dict[x + (y * SUBTILE_GRID_ROWS)] = subtile

    new_data = [[EMPTY_CELL for _ in range(new_cols_cnt)] for _ in range(new_rows_cnt)]

    for y, row in enumerate(maze.cell_rows):

        for x, cell in enumerate(row):
            # find the correct image for the cell
            # index = 0
            # allowed_moves = cell.get_allowed_moves()
            # for dir in range(4):
            #     if allowed_moves[dir]:
            #         index += 2**dir

            tile_index = subtile_sheet_dict[cell.image_index]
            copy_subtile(new_data, (x * SUBTILE_COLS) + MARGIN, (y * SUBTILE_ROWS) + MARGIN, tile_index)

    layer.data = new_data
    # layer.width = new_cols_cnt
    # layer.height = new_rows_cnt

#######################################################################################################################


def place_tile_randomly(
    maze: Maze,
    tile_gids: dict[str, int],
    layer: pytmx.TiledTileLayer,
    tile_name: str,
    tiles_count: int
) -> None:
    count: int = 0
    while count < tiles_count:
        r_x = random.randint(0, maze.num_cols - 1)
        r_y = random.randint(0, maze.num_rows - 1)
        # tile_gid = random.choice(walls_decors_gids)
        x = (r_x * SUBTILE_ROWS) + MARGIN + 3
        y = (r_y * SUBTILE_COLS) + MARGIN + 3
        # check if empty
        if layer.data[y][x] != EMPTY_CELL:
            continue
        layer.data[y][x] = tile_gids[tile_name]
        count += 1

#######################################################################################################################


def translate_grid_to_sub_grid(cell: tuple[int, int]) -> tuple[int, int]:
    left = MARGIN * TILE_SIZE + cell[0] * SUBTILE_COLS * TILE_SIZE
    top  = MARGIN * TILE_SIZE + cell[1] * SUBTILE_ROWS * TILE_SIZE

    return (left, top)

#######################################################################################################################


def build_tileset_map_from_maze(
    clean_tileset_map: pytmx.TiledMap,
    maze: Maze,
    maze_stats: dict[str, Any],
    current_map: str,
    to_map: str,
    entry_point: str,
) -> None:
    """
    Builds a final maze map from a maze grid.

    Args:
        clean_tileset_map (pytmx.TiledMap): The tileset map with maze template. Will be overwritten with the final map.
        maze (Maze): The input maze grid to convert.
        current_map (str): the name of current maze (contains maze level)
        to_map (str): The exit to map (name of map file, eg. `Village.tmx)`.
        entry_point (str): The starting point in the exit map (name of object on exits layer).

    Description:
        maze template consist of a 4 by 4 grid. Each cell is a patch of tiles
        representing one of maze elements.
        * -> wall
        . -> floor
        9 -> image_index

        #..#  #..#  #..#  #..#
        ..0.  ..1#  #.2.  #.3#
        #..#  #..#  #..#  #..#

        #..#  #..#  #..#  #..#
        ..4.  ..5#  #.6.  #.7#
        ####  ####  ####  ####

        ####  ####  ####  ####
        ..8.  ..9#  #10.  #11#
        #..#  #..#  #..#  #..#

        ####  ####  ####
        .12.  .13#  #14.
        ####  ####  ####

    """

    # if "entry_points" in self.layers:
    #     for obj in tileset_map.get_layer_by_name("entry_points"):
    #         self.entry_points[obj.name] = vec(obj.x, obj.y)
    global BACKGROUND_CELL, STAIRS_TILES_POS, IMAGE_DIRECTION_TO_IDX, RETURN_CELL
    BACKGROUND_CELL = clean_tileset_map.get_layer_by_name("background").data[0][0]
    # print(f"{BACKGROUND_CELL=}")

    RETURN_CELL = clean_tileset_map.get_layer_by_name("floor_decors").data[9][36]
    floor_decors = clean_tileset_map.get_layer_by_name("floor_decors")
    for stair_type in STAIRS_TILES_POS:
        for direction in STAIRS_TILES_POS[stair_type]:
            pos = STAIRS_TILES_POS[stair_type][direction]
            IMAGE_DIRECTION_TO_IDX[stair_type][direction] = floor_decors.data[pos[1]][pos[0]]
            # print(IMAGE_DIRECTION_TO_IDX[stair_type][direction], pos, floor_decors.data[pos[1]][pos[0]])
    # elements_layer = clean_tileset_map.get_layer_by_name("floor_decors")
    # print("stairs_down")
    # for x in range(32, 36):
    #     print(elements_layer.data[8][x])
    # print("stairs_up")
    # for x in range(32, 36):
    #     print(elements_layer.data[9][x])

    stats = maze_stats  # analyze_maze(maze)
    current_map_name: str = current_map.split("_")[0]
    current_map_level: int = stats["current_map_level"]
    max_level: int = stats["max_level"]
    if current_map_level == 1:
        start = stats["longest_N_wall_path_start"]
        end   = stats["longest_N_wall_path_end"]
    else:
        start = stats["longest_dead_end_path_start"]
        end   = stats["longest_dead_end_path_end"]
    stats["start"] = start
    stats["end"]   = end
    start_cell = maze.cell_rows[start[1]][start[0]]
    end_cell   = maze.cell_rows[end[1]][end[0]]
    # print(f"{current_map=}, {to_map=}")
    # print(f"{current_map_level=}")
    # print(f"{start=}")
    # print(f"{end=}")

    # position (point) where the player will show up after entering the map from Village or lower maze level
    entry_obj = clean_tileset_map.get_object_by_name("Entry")
    if current_map_level == 1:
        # in front (below) of the door

        entry_obj.x = (MARGIN + start[0] * SUBTILE_COLS + ENTRY_X_OFFSET) * TILE_SIZE + (TILE_SIZE // 2)
        entry_obj.y = (MARGIN + start[1] * SUBTILE_ROWS + ENTRY_Y_OFFSET) * TILE_SIZE
    else:
        # next to stairs up sprite
        # start = stats["longest_dead_end_path_start"]
        entry_obj.x = (MARGIN + start[0] * SUBTILE_COLS +  # noqa: W504
                       IMAGE_DIRECTION_TO_POS_OFFSET[start_cell.image_index][0]) * TILE_SIZE + (TILE_SIZE // 2)
        entry_obj.y = (MARGIN + start[1] * SUBTILE_ROWS +  # noqa: W504
                       IMAGE_DIRECTION_TO_POS_OFFSET[start_cell.image_index][1]) * TILE_SIZE

    # return to previous map (Village or maze level - 1) collider
    return_obj = clean_tileset_map.get_object_by_name("Return")
    if current_map_level == 1:
        # same location as the location of doors sprite on the north wall
        return_obj.x = (MARGIN + start[0] * SUBTILE_COLS + RETURN_X_OFFSET) * TILE_SIZE
        return_obj.y = (MARGIN + start[1] * SUBTILE_ROWS + RETURN_Y_OFFSET) * TILE_SIZE
        return_obj.to_map = to_map  # "Village"
        return_obj.entry_point = entry_point  # "Stairs"
    else:
        # same location as the location of the stairs up sprite
        return_obj.x = (MARGIN + start[0] * SUBTILE_COLS +  # noqa: W504
                        IMAGE_DIRECTION_TO_OFFSET[start_cell.image_index][0]) * TILE_SIZE
        return_obj.y = (MARGIN + start[1] * SUBTILE_ROWS +  # noqa: W504
                        IMAGE_DIRECTION_TO_OFFSET[start_cell.image_index][1]) * TILE_SIZE
        return_obj.to_map = f"{current_map_name}_{(current_map_level - 1):02d}"
        return_obj.entry_point = "Re-Entry"  # "Stairs"

    big_chest_obj = clean_tileset_map.get_object_by_name("BigChest_Maze")
    big_chest_obj.x = (MARGIN + end[0] * SUBTILE_COLS +  # noqa: W504
                       IMAGE_DIRECTION_TO_CHEST[end_cell.image_index][0]) * TILE_SIZE
    big_chest_obj.y = (MARGIN + end[1] * SUBTILE_ROWS +  # noqa: W504
                       IMAGE_DIRECTION_TO_CHEST[end_cell.image_index][1]) * TILE_SIZE

    # go deeper (maze level + 1) collider (on stairs down sprite)
    stairs_obj = clean_tileset_map.get_object_by_name("Stairs")
    if current_map_level < max_level:
        stairs_obj.x = (MARGIN + end[0] * SUBTILE_COLS + IMAGE_DIRECTION_TO_OFFSET[end_cell.image_index][0]) * TILE_SIZE
        stairs_obj.y = (MARGIN + end[1] * SUBTILE_ROWS + IMAGE_DIRECTION_TO_OFFSET[end_cell.image_index][1]) * TILE_SIZE
        stairs_obj.to_map = f"{current_map_name}_{(current_map_level + 1):02d}"
        stairs_obj.entry_point = "Entry"
    else:
        # not accessible
        stairs_obj.x = 0
        stairs_obj.y = 0

    # position (point) where the player will show up after returning from deeper maze level (next to stairs down)
    re_entry_obj = clean_tileset_map.get_object_by_name("Re-Entry")
    if current_map_level < max_level:
        re_entry_obj.x = (MARGIN + end[0] * SUBTILE_COLS +  # noqa: W504
                          IMAGE_DIRECTION_TO_POS_OFFSET[end_cell.image_index][0]) * TILE_SIZE + (TILE_SIZE // 2)
        re_entry_obj.y = (MARGIN + end[1] * SUBTILE_ROWS +  # noqa: W504
                          IMAGE_DIRECTION_TO_POS_OFFSET[end_cell.image_index][1]) * TILE_SIZE
    else:
        re_entry_obj.x = 0
        re_entry_obj.y = 0

    new_cols_cnt = (maze.num_cols * SUBTILE_COLS) + (2 * MARGIN)
    new_rows_cnt = (maze.num_rows * SUBTILE_ROWS) + (2 * MARGIN)

    layer_names: dict[str, int] = {}
    for i, layer in enumerate(clean_tileset_map.layers):
        layer_names[layer.name] = i
    # print(layer_names)

    # background decors (holes, gray stones)
    floor_decors_gids = {}
    floor_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["floor_decors"])
    for prop in floor_decors_props:
        gid, tile = prop
        # print(tile)
        if "floor_decors" in tile:  # .keys():
            floor_decors_gids[tile["floor_decors"]] = gid

    # floor decors (dirt, gray stones)
    # floor_decors_gids = {}
    # floor_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["floor_decors"])
    # for prop in floor_decors_props:
    #     gid, tile = prop
    #     # print(tile)
    #     if "floor_decors" in tile:  # .keys():
    #         floor_decors_gids[tile["floor_decors"]] = gid

    # elements on floor (dead rat, barrel, crate, stool)
    elements_gids = {}
    elements_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["elements"])
    for prop in elements_props:
        gid, tile = prop
        # print(tile)
        if "elements" in tile:  # .keys():
            elements_gids[tile["elements"]] = gid

    # wall decors (bars, banner, glyph)
    walls_decors_gids = {}
    walls_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["walls_decors"])
    for prop in walls_decors_props:
        gid, tile = prop
        # print(tile)
        if "walls_decors" in tile:  # .keys():
            walls_decors_gids[tile["walls_decors"]] = gid

    # collectable items (flask health, golden key, coin)
    items_gids: dict[str, int] = {}
    items_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["items"])
    for prop in items_props:
        gid, tile = prop
        items_gids[tile["item_name"]] = gid

    for layer_name in ["walls", "floor"]:
        layer = clean_tileset_map.get_layer_by_name(layer_name)
        make_layer(layer, maze, new_cols_cnt, new_rows_cnt)

        if layer_name == "walls":
            elements_cnt = 0
            # print(f"{clean_tileset_map.gidmap}=")
            # for cell_id in SPECIAL_WALLS_IDS:
            #     print(clean_tileset_map.gidmap[cell_id])
            while elements_cnt < ELEMENTS_MAX:
                r_x = random.randint(0, maze.num_cols - 1)
                r_y = random.randint(0, maze.num_rows - 1)
                # tiles with visible wall at the top (so there is a place to put decors)
                image_index = maze.cell_rows[r_y][r_x].image_index
                if image_index in ELEMENTS_OFFSETS_MAP:  # .keys():
                    tile_gid = random.choice(list(elements_gids.values()))
                    x = (r_x * SUBTILE_ROWS) + MARGIN + int(ELEMENTS_OFFSETS_MAP[image_index].x)
                    y = (r_y * SUBTILE_COLS) + MARGIN + int(ELEMENTS_OFFSETS_MAP[image_index].y)
                    layer.data[y][x] = tile_gid
                    elements_cnt += 1

    for layer in clean_tileset_map.layers:
        # print(layer.name)
        # clear and init layer size for all other layers
        if layer.name not in ["background", "walls", "floor"]:
            new_data = [[EMPTY_CELL for _ in range(new_cols_cnt)] for _ in range(new_rows_cnt)]
            layer.data = new_data
        layer.width = new_cols_cnt
        layer.height = new_rows_cnt

    # background
    # bg_id = get_gid_from_tmx_id(BACKGROUND_CELL, clean_tileset_map)
    bg_id = BACKGROUND_CELL
    # bg_data = [[bg_id for _ in range(maze.num_cols + (2 * margin))] for _ in range(maze.num_rows + (2 * margin))]
    bg_data = [[bg_id for _ in range(new_cols_cnt)] for _ in range(new_rows_cnt)]
    # background_decors_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in BACKGROUND_DECORS_IDS]
    bg_layer = clean_tileset_map.get_layer_by_name("background")

    # for _ in range(BACKGROUND_DECORS_MAX):
    #     dir = random.randint(1, 4)
    #     if dir == 1:
    #         r_x = random.randint(0, MARGIN - 1)
    #         r_y = random.randint(0, new_rows_cnt - 1)
    #     elif dir == 2:
    #         r_x = random.randint(0, new_cols_cnt - 1)
    #         r_y = random.randint(0, MARGIN - 1)
    #     elif dir == 3:
    #         r_x = random.randint(new_cols_cnt - MARGIN - 1, new_cols_cnt - 1)
    #         r_y = random.randint(0, new_rows_cnt - 1)
    #     elif dir == 4:
    #         r_x = random.randint(0, new_cols_cnt - 1)
    #         r_y = random.randint(new_rows_cnt - MARGIN - 1, new_rows_cnt - 1)
    #     bg_data[r_y][r_x] = random.choice(list(floor_decors_gids.values()))
    bg_layer.data = bg_data

    # put WALL_DECORS_MAX decors randomly selected from the list of WALLS_DECORS_IDS tiles
    decors_layer = clean_tileset_map.get_layer_by_name("walls_decors")
    floor_decors_layer = clean_tileset_map.get_layer_by_name("floor_decors")
    items_layer = clean_tileset_map.get_layer_by_name("items")
    # walls_decors_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in WALLS_DECORS_IDS]
    wall_decors_cnt = 0
    while wall_decors_cnt < WALL_DECORS_MAX:
        r_x = random.randint(0, maze.num_cols - 1)
        r_y = random.randint(0, maze.num_rows - 1)
        # tiles with visible wall at the top (so there is a place to put decors)
        if maze.cell_rows[r_y][r_x].image_index >= 8:
            tile_gid = random.choice(list(walls_decors_gids.values()))
            x = (r_x * SUBTILE_ROWS) + MARGIN + WALLS_DECORS_OFFSET_RANGE_X
            y = (r_y * SUBTILE_COLS) + MARGIN + WALLS_DECORS_OFFSET_RANGE_Y
            # print(tile_gid)
            decors_layer.data[y][x] = tile_gid
            wall_decors_cnt += 1

    # place exit (return) doors (must be last since nothing should cover them)
    if current_map_level == 1:
        return_id = RETURN_CELL  # get_gid_from_tmx_id(RETURN_CELL, clean_tileset_map)
        x = MARGIN + start[0] * SUBTILE_COLS + RETURN_X_OFFSET
        y = MARGIN + start[1] * SUBTILE_COLS + RETURN_Y_OFFSET
        decors_layer.data[y][x] = return_id
    else:
        # return_id = get_gid_from_tmx_id(RETURN_CELL, clean_tileset_map)
        cell = maze.cell_rows[start[1]][start[0]]
        idx = IMAGE_DIRECTION_TO_IDX["stairs_up"][cell.image_index]
        x = MARGIN + start[0] * SUBTILE_COLS + IMAGE_DIRECTION_TO_OFFSET[cell.image_index][0]  # STAIRS_UP_X_OFFSET
        y = MARGIN + start[1] * SUBTILE_COLS + IMAGE_DIRECTION_TO_OFFSET[cell.image_index][1]  # STAIRS_UP_Y_OFFSET

        decors_layer.data[y][x] = idx  # STAIRS_TYPES_IDX["stairs_up"]["east"]  # STAIRS_UP_CELL

    # decors_layer = clean_tileset_map.get_layer_by_name("walls_decors")

    # put random items on the map

    for item_name, count in ITEMS_MAX_COUNT.items():
        place_tile_randomly(maze, items_gids, items_layer, item_name, count)
    # print(clean_tileset_map.gidmap)
    # stairs_id = get_gid_from_tmx_id(STAIRS_CELL, clean_tileset_map)

    # place stairs down sprite
    if current_map_level < max_level:
        cell = maze.cell_rows[end[1]][end[0]]
        idx = IMAGE_DIRECTION_TO_IDX["stairs_down"][cell.image_index]

        x = MARGIN + end[0] * SUBTILE_COLS + IMAGE_DIRECTION_TO_OFFSET[cell.image_index][0]
        y = MARGIN + end[1] * SUBTILE_COLS + IMAGE_DIRECTION_TO_OFFSET[cell.image_index][1]

        floor_decors_layer.data[y][x] = idx  # STAIRS_TYPES_IDX["stairs_down"]["west"]

    clean_tileset_map.width = new_cols_cnt
    clean_tileset_map.height = new_rows_cnt
