import random
from typing import Any, Generator

from .cell import CELL_EAST, CELL_NORTH, CELL_SOUTH, CELL_WEST, Cell

#################################################################################################################


class Maze:
    def __init__(self, cols: int, rows: int) -> None:
        self.num_rows = rows
        self.num_cols = cols
        self.clear()

    def clear(self) -> None:
        self.cell_rows: list[list[Cell]] = []

        for y in range(self.num_rows):
            cells = []
            for x in range(self.num_cols):
                cell = Cell(x, y)
                cells.append(cell)
            self.cell_rows.append(cells)

        for y in range(self.num_rows):
            for x in range(self.num_cols):
                cell = self.cell_rows[y][x]
                if x > 0:
                    cell.add_neighbor(CELL_WEST, self.cell_rows[y][x - 1])
                if x < self.num_cols - 1:
                    cell.add_neighbor(CELL_EAST, self.cell_rows[y][x + 1])
                if y > 0:
                    cell.add_neighbor(CELL_NORTH, self.cell_rows[y - 1][x])
                if y < self.num_rows - 1:
                    cell.add_neighbor(CELL_SOUTH, self.cell_rows[y + 1][x])

    #############################################################################################################
    def get_all_cells(self, start_from_top_row: bool = False) -> Generator[Cell, Any, Any]:
        if start_from_top_row:
            rows = self.cell_rows
        else:
            rows = list(reversed(self.cell_rows))

        for row in rows:
            for cell in row:
                yield cell

    #############################################################################################################
    def get_random_cell(self) -> Cell:
        x = random.randint(0, self.num_cols - 1)
        y = random.randint(0, self.num_rows - 1)
        return self.cell_rows[y][x]

    #############################################################################################################
    def get_number_cells(self) -> int:
        return self.num_rows * self.num_cols

    #############################################################################################################
    def generate(self) -> None:
        raise NotImplementedError(
            "[red]error[/] This is abstract class. 'generate' method needs to be implemented in subclass.")
