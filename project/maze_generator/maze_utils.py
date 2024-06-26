import random
import pytmx
from pygame.math import Vector2 as vec
# from project.settings import TILE_SIZE
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
BACKGROUND_DECORS_IDS = [12, 24]
STAIRS_CELL = 33 #332

WALLS_DECORS_IDS = [28, 29, 19,]
SPECIAL_WALLS_IDS = [65, 74, 82, 63, 73, 124,]

# FLOOR_DECORS_IDS = [49, 42]
MARGIN = 3

TILE_SIZE = 16

import heapq

def heuristic(point, goal):
    # Manhattan distance heuristic
    return abs(point[0] - goal[0]) + abs(point[1] - goal[1])

# def is_diagonal(p)
def a_star(grid, start, goal):
    # https://panda-man.medium.com/a-pathfinding-algorithm-efficiently-navigating-the-maze-of-possibilities-8bb16f9cecbd
    open_set = []

    # Priority queue with (F-score, node)
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    
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
        for d in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1),]:
        
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
            tentative_g = g_score[current] + abs(grid[x][y]) if not is_diagonal else g_score[current] + int(abs(-grid[x][y] * 1.41))
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
                move_permitted = grid[x][y] <= 0 if not is_diagonal else (grid[x][y] <= 0 and grid[x][current[1]] <= 0 and grid[current[0]][y] <= 0)
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

def copy_subtile(new_data: list[list[int]], x: int, y: int, subtile_sheet: list[list[int]]):
    rows = len(subtile_sheet)
    cols = len(subtile_sheet[0])
    for row in range(rows):
        for col in range(cols):
            new_data[y + row][x + col] = subtile_sheet[row][col]


def get_gid_from_tmx_id(tmx_id: int, tileset_map: pytmx.TiledMap) -> int:
    gid_tuple = tileset_map.gidmap[tmx_id+1]
    if len(gid_tuple):
        return gid_tuple[0][0]
    else:
        print(f"[red]ERROR[/] GID for {tmx_id} not found!")
        # print(tileset_map.gidmap)
        return 0


def make_layer(layer, maze: Maze, new_cols_cnt: int, new_rows_cnt: int):
    
    subtile_sheet_dict = {}
    for y in range(SUBTILE_GRID_ROWS):
        for x in range(SUBTILE_GRID_COLS):
            subtile = []
            for subtile_y in range(SUBTILE_ROWS):
                subtile_row = []
                for subtile_x in range(SUBTILE_COLS):
                    subtile_row.append(layer.data[subtile_y + (y * SUBTILE_ROWS_OFFSET)][subtile_x + (x * SUBTILE_COLS_OFFSET)])
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
    
    
def get_pyscroll_from_maze(clean_tileset_map: pytmx.TiledMap, maze: Maze, to_map: str, entry_point: str) -> dict[int, list[list[int]]]:
    
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
    return_obj.to_map = to_map # "Village"
    return_obj.entry_point = entry_point # "Stairs"
    
    new_cols_cnt = (maze.num_cols * SUBTILE_COLS) + (2 * MARGIN)
    new_rows_cnt = (maze.num_rows * SUBTILE_ROWS) + (2 * MARGIN)
    
    for layer_name in ["walls", "floor"]:
        layer = clean_tileset_map.get_layer_by_name(layer_name)
        make_layer(layer, maze, new_cols_cnt, new_rows_cnt)
        if layer_name == "walls":
            # SPECIAL_WALLS_IDS
            
            special_walls_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in SPECIAL_WALLS_IDS]
            # print(f"{special_walls_gids=}")
            special_walls_max = 6
            special_walls_cnt = 0
            special_walls_offsets_map = {
                14: vec(1, 3),
                13: vec(4, 3),
                11: vec(2, 2),
                10: vec(2, 2),
                9 : vec(4, 2),
                7 : vec(3, 4),
                6 : vec(1, 4),
                5 : vec(4, 4),
            }
            # print(f"{clean_tileset_map.gidmap}=")
            # for cell_id in SPECIAL_WALLS_IDS:
            #     print(clean_tileset_map.gidmap[cell_id])
            while special_walls_cnt < special_walls_max:
                r_x = random.randint(0, maze.num_cols - 1)
                r_y = random.randint(0, maze.num_rows - 1)
                # tiles with visible wall at the top (so there is a place to put decors)
                image_index = maze.cell_rows[r_y][r_x].image_index
                if image_index in special_walls_offsets_map.keys():
                    tile_gid = random.choice(special_walls_gids)
                    x = (r_x * SUBTILE_ROWS) + MARGIN + int(special_walls_offsets_map[image_index].x)
                    y = (r_y * SUBTILE_COLS) + MARGIN + int(special_walls_offsets_map[image_index].y)
                    layer.data[y][x] = tile_gid
                    special_walls_cnt += 1
            
        
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
    background_decors_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in BACKGROUND_DECORS_IDS]
    bg_layer = clean_tileset_map.get_layer_by_name("background")
    BACKGROUND_DECORS_MAX = 80
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
        bg_data[r_y][r_x] = random.choice(background_decors_gids)
    bg_layer.data = bg_data    
    
    # put wall_decors_max decors randomly selected from the list of WALLS_DECORS_IDS tiles
    decors_layer = clean_tileset_map.get_layer_by_name("walls_decors")
    # print(f"{len(decors_layer.data)=}")
    # print(f"{len(decors_layer.data[0])=}")
    walls_decors_gids = [get_gid_from_tmx_id(cell_id, clean_tileset_map) for cell_id in WALLS_DECORS_IDS]
    WALL_DECORS_MAX = 8
    wall_decors_cnt = 0
    while wall_decors_cnt < WALL_DECORS_MAX:
        r_x = random.randint(0, maze.num_cols - 1)
        r_y = random.randint(0, maze.num_rows - 1)
        # tiles with visible wall at the top (so there is a place to put decors)
        if maze.cell_rows[r_y][r_x].image_index >= 8:
            tile_gid = random.choice(walls_decors_gids)
            x = (r_x * SUBTILE_ROWS) + MARGIN + WALLS_DECORS_OFFSET_RANGE_X
            y = (r_y * SUBTILE_COLS) + MARGIN + WALLS_DECORS_OFFSET_RANGE_Y
            decors_layer.data[y][x] = tile_gid
            wall_decors_cnt += 1
            
    # place exit doors (must be last since nothing should cover them)        
    stairs_id = get_gid_from_tmx_id(STAIRS_CELL, clean_tileset_map)
    decors_layer.data[MARGIN + RETURN_Y_OFFSET][MARGIN + RETURN_X_OFFSET] = stairs_id
    
    clean_tileset_map.width = new_cols_cnt
    clean_tileset_map.height = new_rows_cnt
