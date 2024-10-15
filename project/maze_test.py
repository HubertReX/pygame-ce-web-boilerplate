import itertools
from typing import Any
from maze_generator import hunt_and_kill_maze
from rich import print
from maze_generator.maze_utils import GRID_FACTOR, a_star, mapping, mapping_grid

from maze_generator.maze import Maze
from maze_generator.cell import Cell

STEP_COST_WALL: int   = 100
STEP_COST_GROUND: int = 0

maze_cols = 10
maze_rows = 7

DIVIDER = 4

North = 7
South = 11
West = 13
East = 14


# for y, row in enumerate(maze.cell_rows):

#     for x, cell in enumerate(row):
#         # find the correct image for the cell
#         # index = 0
#         # allowed_moves = cell.get_allowed_moves()
#         # for dir in range(4):
#         #     if allowed_moves[dir]:
#         #         index += 2**dir

#         # tile_index = subtile_sheet_dict[cell.image_index]

#         print(f"{cell.image_index:3}", sep=" ", end="")
#     print("")

# print("##########")


def print_maze(maze: Maze, path: list[tuple[int, int]] | None = None) -> None:
    if not path:
        path = []
    for cell in maze.get_all_cells(start_from_top_row=True):
        if cell.x == 0:
            print("")
        # cell.x > maze_cols // DIVIDER and cell.y > maze_rows // DIVIDER and
        if cell.image_index in [7, 11, 13, 14]:
            color = "yellow"
        elif (cell.x, cell.y) in path:
            color = "red"
        else:
            color = "white"

        # print(f"[{color}]{cell.image_index:3}[/]", sep=" ", end="")
        print(f"[{color}]{mapping[cell.image_index]}[/]", sep=" ", end="")

    print("")
    print("[cyan]####################[/]")

# cell = maze.cell_rows[0][0]
# print(cell.allowed_moves)


# maze.generate()

def find_candidate(maze: Maze) -> None:
    found_candidate = False
    for cell in maze.get_all_cells():
        if cell.x > maze_cols // DIVIDER and cell.y > maze_rows // DIVIDER and cell.image_index in [7, 11, 13, 14]:
            found_candidate = True
            break
    if not found_candidate:
        print(found_candidate)


def find_candidates(maze: Maze) -> list[tuple[int, int]]:
    candidates = []
    for cell in maze.get_all_cells():
        # cell.x > maze_cols // DIVIDER and cell.y > maze_rows // DIVIDER and
        if cell.image_index in [7, 11, 13, 14]:
            candidates.append((cell.x, cell.y))

    return candidates


def copy_subtile(new_data: list[list[int]], x: int, y: int, subtile_sheet: list[list[int]]) -> None:
    rows = len(subtile_sheet)
    cols = len(subtile_sheet[0])
    for row in range(rows):
        for col in range(cols):
            new_data[y + row][x + col] = subtile_sheet[row][col] // 100


def generate_grid(maze: Maze) -> list[list[int]]:
    path_finding_grid: list[list[int]] = [[STEP_COST_GROUND for _ in range(maze_cols * GRID_FACTOR)]
                                          for _ in range(maze_rows * GRID_FACTOR)]
    for y, row in enumerate(maze.cell_rows):
        for x, cell in enumerate(row):
            tile_index = mapping_grid[cell.image_index]
            copy_subtile(path_finding_grid, x * GRID_FACTOR, y * GRID_FACTOR, tile_index)

    return path_finding_grid


def analyze_maze(maze: Maze) -> dict[str, Any]:
    pass
    stats: dict[str, Any] = {}
    # stats["end_points"] = []
    # stats["paths"] = []
    # stats["paths_len"] = []
    stats["longest_path"] = []

    path_finding_grid = generate_grid(maze)
    candidates = find_candidates(maze)

    if len(candidates) == 0:
        print("[red]ERROR[/] no candidates")
        exit()

    combinations = itertools.combinations(candidates, 2)
    paths = []
    paths_len = []
    for comb in combinations:
        start = scale_step(comb[0])
        goal = scale_step(comb[1])
        path = fix_path(a_star(start=start, goal=goal, grid=path_finding_grid))
        paths.append(path)
        paths_len.append(len(path))

    # print(
    #     f"count end points {len(candidates):2d}",
    #     # f"count paths {len(paths):2d}",
    #     # f"min {min(paths_len):2d}",
    #     # f"avg {(sum(paths_len) / len(paths_len)):2.1f}",
    #     f"max {max(paths_len):2d}",
    #     f"sum {sum(paths_len):4d}",
    # )

    # simple maze
    # if len(candidates) < 8 and sum(paths_len) < 600:  # and max(paths_len) < 40:
    # hard maze
    # if len(candidates) > 9 and sum(paths_len)  > 900:  # or max(paths_len) > 45:
    #     print_maze(maze, paths[paths_len.index(max(paths_len))])

    # stats["end_points"] = candidates
    # stats["paths"] = paths
    # stats["paths_len"] = paths_len
    longest_path = paths[paths_len.index(max(paths_len))]
    # stats["longest_path"] = paths[paths_len.index(max(paths_len))]
    stats["longest_path_start"] = longest_path[0]
    stats["longest_path_end"] = longest_path[-1]
    stats["longest_path_len"] = max(paths_len)
    stats["sum_all_paths_len"] = sum(paths_len)

    return stats


def main() -> None:
    maze = hunt_and_kill_maze.HuntAndKillMaze(maze_cols, maze_rows)

    for _ in range(10):
        maze.clear()
        maze.generate()

        stats = analyze_maze(maze)
        print(stats)


def scale_step(step: tuple[int, int]) -> tuple[int, int]:
    return (1 + step[1] * GRID_FACTOR, 1 + step[0] * GRID_FACTOR)


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


if __name__ == "__main__":
    main()
