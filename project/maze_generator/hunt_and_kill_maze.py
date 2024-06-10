import random

# from cell import Cell
from .maze import Maze


class HuntAndKillMaze(Maze):

    def __init__(self, cols, rows) -> None:
        super().__init__(cols, rows)

    # Hunt and kill maze generation algorithm

    def generate_interactive(self, maze_drawer) -> None:
        maze_drawer.draw()
        current_cell = self.get_random_cell()

        while current_cell is not None:
            maze_drawer.draw(current_cell)

            neighbors = current_cell.get_all_neighbors()
            unvisited_neighbors = []
            for neighbor in neighbors:
                if neighbor.get_number_links() == 0:
                    unvisited_neighbors.append(neighbor)

            if len(unvisited_neighbors) > 0:
                neighbor = random.choice(unvisited_neighbors)
                current_cell.link(neighbor)
                current_cell = neighbor
            else:
                current_cell = None
                for cell in self.get_all_cells(start_from_top_row = True):
                    maze_drawer.draw(cell, visit=False)
                    if cell.get_number_links() == 0:
                        neighbors = cell.get_all_neighbors()
                        visited_neighbors = []
                        for neighbor in neighbors:
                            if neighbor.get_number_links() != 0:
                                visited_neighbors.append(neighbor)

                        if len(visited_neighbors) > 0:
                            current_cell = cell
                            neighbor = random.choice(visited_neighbors)
                            current_cell.link(neighbor)
                            break

    # Hunt and kill generation algorithm

    def generate(self) -> None:
        current_cell = self.get_random_cell()

        while current_cell is not None:
            neighbors = current_cell.get_all_neighbors()
            unvisited_neighbors = []
            for neighbor in neighbors:
                if neighbor.get_number_links() == 0:
                    unvisited_neighbors.append(neighbor)

            if len(unvisited_neighbors) > 0:
                neighbor = random.choice(unvisited_neighbors)
                current_cell.link(neighbor)
                current_cell = neighbor
            else:
                current_cell = None
                for cell in self.get_all_cells(start_from_top_row = True):
                    if cell.get_number_links() == 0:
                        neighbors = cell.get_all_neighbors()
                        visited_neighbors = []
                        for neighbor in neighbors:
                            if neighbor.get_number_links() != 0:
                                visited_neighbors.append(neighbor)

                        if len(visited_neighbors) > 0:
                            current_cell = cell
                            neighbor = random.choice(visited_neighbors)
                            current_cell.link(neighbor)
                            break

        for cell in self.get_all_cells():
            cell.allowed_moves = cell.get_allowed_moves()
            index = 0
            for dir in range(4):
                if cell.allowed_moves[dir]:
                    index += 2**dir
                cell.image_index = index
