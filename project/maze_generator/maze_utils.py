import heapq
import random
import pytmx
from pygame.math import Vector2 as vec
from functools import wraps
import time
from .maze import Maze
from functools import partial
from rich import inspect, pretty, print
from rich import traceback
help = partial(inspect, help=True, methods=True)
pretty.install()

SUBTILE_COLS = 6
SUBTILE_GRID_COLS = 4
SUBTILE_COLS_SEP = 2
SUBTILE_COLS_OFFSET = SUBTILE_COLS + SUBTILE_COLS_SEP

SUBTILE_ROWS = 6
SUBTILE_GRID_ROWS = 4
SUBTILE_ROWS_SEP = 2
SUBTILE_ROWS_OFFSET = SUBTILE_ROWS + SUBTILE_ROWS_SEP

EMPTY_CELL = 0
BACKGROUND_CELL = 0
STAIRS_CELL = 33  # 332
# background decors (holes, gray stones)
BACKGROUND_DECORS_MAX = 80
# BACKGROUND_DECORS_IDS = [12, 24]

# elements on floor (dead rat, barrel, crate, stool)
ELEMENTS_MAX = 6
ELEMENTS_OFFSETS_MAP = {
    14: vec(1, 3),
    13: vec(4, 3),
    11: vec(2, 2),
    10: vec(2, 2),
    9: vec(4, 2),
    7: vec(3, 4),
    6: vec(1, 4),
    5: vec(4, 4),
}

# wall decors(bars, banner, glyph)
WALL_DECORS_MAX = 8

# floor decors (dirt, gray stones)
# FLOOR_DECORS_IDS = [49, 42]
ITEMS_MAX_COUNT = {
    "golden_coin": 2,
    "flask_health": 2,
    "axe": 1,
    "sword_short": 1,
    "sword_long": 1,
    "staff_violet": 1,
}

MARGIN = 3

TILE_SIZE = 16

# dict of results of a_star function
# key is a tuple of start and goal coordinates
# value is a list of coordinates to go through
_CACHE: dict[tuple[tuple[int, int], tuple[int, int]], list[tuple[int, int]]] = {}
_sum: float = 0.0
_cnt: int = 0

#######################################################################################################################


def timeit(func):

    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        global _sum, _cnt

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # func.add_execute_time(total_time)
        _cnt += 1
        _sum += total_time
        # el = float(kwargs["fps"][-4:])
        # if el <= 10.00:
        #     print(f'{func.__name__} {str(kwargs["start"]):8}
        # {str(kwargs["goal"]):8} duration:\t{total_time:.5f}\tAvg_time:\t{
        #           _sum / _cnt:.4f}\tcnt:\t{_cnt}\tCache_size:\t{len(_CACHE)}\t{kwargs["fps"]}'.replace(".", ","))
        return result
    return timeit_wrapper

#######################################################################################################################
# @timeit


def a_star_cached(grid, start: tuple[int, int], goal: tuple[int, int], fps: str) -> list[tuple[int, int]]:
    global _CACHE  # , _sum, _cnt

    key = (start, goal)  # create_key(start, goal)

    if key not in _CACHE:
        res = a_star(grid, start, goal)
        if res:
            _CACHE[key] = res
            for i, wp in enumerate(res):
                new_key = (wp, goal)
                # if new_key not in _CACHE:
                _CACHE[new_key] = res[i:]
    #     fps += "\t[red]miss[/]"
    # else:
    #     fps += "\t[green]hit[/]"
    return _CACHE[key]


def clear_maze_cache():
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

    # https://panda-man.medium.com/a-pathfinding-algorithm-efficiently-navigating-the-maze-of-possibilities-8bb16f9cecbd
    open_set = []

    # Priority queue with (F-score, node)
    heapq.heappush(open_set, (0, start))
    came_from = {}
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
            tentative_g = g_score[current] + \
                abs(grid[x][y]) if not is_diagonal else g_score[current] + int(abs(-grid[x][y] * 1.41))
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

#######################################################################################################################


def copy_subtile(new_data: list[list[int]], x: int, y: int, subtile_sheet: list[list[int]]):
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


def make_layer(layer, maze: Maze, new_cols_cnt: int, new_rows_cnt: int):

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


def place_tile_randomly(maze, tile_gids, layer, tile_name: str, tiles_count: int):
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


def build_tileset_map_from_maze(clean_tileset_map: pytmx.TiledMap, maze: Maze, to_map: str, entry_point: str) -> None:
    """
    Builds a final maze map from a maze grid.

    Args:
        clean_tileset_map (pytmx.TiledMap): The tileset map with maze template. Will be overwritten with the final map.
        maze (Maze): The input maze grid to convert.
        to_map (str): The exit to map (name of map file, eg. `Village.tmx)`.
        entry_point (str): The starting point in the exit map (name of object on exits layer).

    Description:
        maze template consist of a 4 by 4 grid. Each cell is a patch of tiles
        representing one of maze elements.
        * -> wall
        . -> floor

        #..#  #..#  #..#  #..#
        ....  ...#  #...  #..#
        #..#  #..#  #..#  #..#

        #..#  #..#  #..#  #..#
        ....  ...#  #...  #..#
        ####  ####  ####  ####

        ####  ####  ####  ####
        ....  ...#  #...  #..#
        #..#  #..#  #..#  #..#

        ####  ####  ####
        ....  ...#  #...
        ####  ####  ####

    """

    # if "entry_points" in self.layers:
    #     for obj in tileset_map.get_layer_by_name("entry_points"):
    #         self.entry_points[obj.name] = vec(obj.x, obj.y)
    ENTRY_X_OFFSET = 3
    ENTRY_Y_OFFSET = 3

    RETURN_X_OFFSET = 3
    RETURN_Y_OFFSET = 1

    WALLS_DECORS_OFFSET_RANGE_X = 2
    WALLS_DECORS_OFFSET_RANGE_Y = 1

    entry_obj = clean_tileset_map.get_object_by_name("Entry")
    entry_obj.x = (MARGIN + ENTRY_X_OFFSET) * TILE_SIZE + (TILE_SIZE // 2)
    entry_obj.y = (MARGIN + ENTRY_Y_OFFSET) * TILE_SIZE

    return_obj = clean_tileset_map.get_object_by_name("Return")
    return_obj.x = (MARGIN + RETURN_X_OFFSET) * TILE_SIZE
    return_obj.y = (MARGIN + RETURN_Y_OFFSET) * TILE_SIZE
    return_obj.to_map = to_map  # "Village"
    return_obj.entry_point = entry_point  # "Stairs"

    new_cols_cnt = (maze.num_cols * SUBTILE_COLS) + (2 * MARGIN)
    new_rows_cnt = (maze.num_rows * SUBTILE_ROWS) + (2 * MARGIN)

    layer_names: dict[str, int] = {}
    for i, layer in enumerate(clean_tileset_map.layers):
        layer_names[layer.name] = i
    # print(layer_names)

    # background decors (holes, gray stones)
    background_decors_gids = {}
    background_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["floor_decors"])
    for prop in background_decors_props:
        gid, tile = prop
        # print(tile)
        if "background_decors" in tile.keys():
            background_decors_gids[tile["background_decors"]] = gid

    # floor decors (dirt, gray stones)
    floor_decors_gids = {}
    floor_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["floor_decors"])
    for prop in floor_decors_props:
        gid, tile = prop
        # print(tile)
        if "floor_decors" in tile.keys():
            floor_decors_gids[tile["floor_decors"]] = gid

    # elements on floor (dead rat, barrel, crate, stool)
    elements_gids = {}
    elements_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["elements"])
    for prop in elements_props:
        gid, tile = prop
        # print(tile)
        if "elements" in tile.keys():
            elements_gids[tile["elements"]] = gid

    # wall decors (bars, banner, glyph)
    walls_decors_gids = {}
    walls_decors_props = clean_tileset_map.get_tile_properties_by_layer(layer_names["walls_decors"])
    for prop in walls_decors_props:
        gid, tile = prop
        # print(tile)
        if "walls_decors" in tile.keys():
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
                if image_index in ELEMENTS_OFFSETS_MAP.keys():
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
    bg_id = get_gid_from_tmx_id(BACKGROUND_CELL, clean_tileset_map)
    # bg_data = [[bg_id for _ in range(maze.num_cols + (2 * margin))] for _ in range(maze.num_rows + (2 * margin))]
    bg_data = [[bg_id for _ in range(new_cols_cnt)] for _ in range(new_rows_cnt)]
    # background_decors_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in BACKGROUND_DECORS_IDS]
    bg_layer = clean_tileset_map.get_layer_by_name("background")

    for _ in range(BACKGROUND_DECORS_MAX):
        dir = random.randint(1, 4)
        if dir == 1:
            r_x = random.randint(0, MARGIN - 1)
            r_y = random.randint(0, new_rows_cnt - 1)
        elif dir == 2:
            r_x = random.randint(0, new_cols_cnt - 1)
            r_y = random.randint(0, MARGIN - 1)
        elif dir == 3:
            r_x = random.randint(new_cols_cnt - MARGIN - 1, new_cols_cnt - 1)
            r_y = random.randint(0, new_rows_cnt - 1)
        elif dir == 4:
            r_x = random.randint(0, new_cols_cnt - 1)
            r_y = random.randint(new_rows_cnt - MARGIN - 1, new_rows_cnt - 1)
        bg_data[r_y][r_x] = random.choice(list(background_decors_gids.values()))
    bg_layer.data = bg_data

    # put WALL_DECORS_MAX decors randomly selected from the list of WALLS_DECORS_IDS tiles
    decors_layer = clean_tileset_map.get_layer_by_name("walls_decors")
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

    # place exit doors (must be last since nothing should cover them)
    stairs_id = get_gid_from_tmx_id(STAIRS_CELL, clean_tileset_map)
    decors_layer.data[MARGIN + RETURN_Y_OFFSET][MARGIN + RETURN_X_OFFSET] = stairs_id

    # put random items on the map
    items_layer = clean_tileset_map.get_layer_by_name("items")

    for item_name, count in ITEMS_MAX_COUNT.items():
        place_tile_randomly(maze, items_gids, items_layer, item_name, count)

    clean_tileset_map.width = new_cols_cnt
    clean_tileset_map.height = new_rows_cnt
