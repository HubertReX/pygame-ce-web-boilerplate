from typing import Any
from maze_generator.hunt_and_kill_maze import HuntAndKillMaze
from rich import print
from maze_generator.maze_utils import analyze_maze, MAZE_COLS, MAZE_ROWS, print_maze


def print_main_stats(stats: dict[str, Any]) -> None:
    main_stats = ["longest_dead_end_path_len", "sum_all_dead_end_paths",
                  "dead_ends_count", "longest_N_wall_path_len", "is_simple", "is_hard"]

    stats_list = []
    for stat in main_stats:
        stats_list.append(f"'{stat}': {stats[stat]}")

    print(", ".join(stats_list))


def main() -> None:
    maze = HuntAndKillMaze(MAZE_COLS, MAZE_ROWS)

    for _ in range(10):
        maze.clear()
        maze.generate()

        stats = analyze_maze(maze)

    print_main_stats(stats)
    print("[cyan]####################[/]")

    print("'longest_dead_end_path':")
    print_maze(maze, stats["longest_dead_end_path"])
    print("[cyan]####################[/]")

    print("'longest_N_wall_path':")
    print_maze(maze, stats["longest_N_wall_path"])
    print("[cyan]####################[/]")


if __name__ == "__main__":
    main()
