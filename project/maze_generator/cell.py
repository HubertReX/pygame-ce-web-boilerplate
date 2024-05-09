import random


CELL_NORTH = 3 # 1
CELL_EAST  = 0 # 2
CELL_SOUTH = 2 # 3
CELL_WEST  = 1 # 4


class Cell:

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.links: list[Cell] = []
        self.neighbors: dict[int, Cell] = dict()
        self.allowed_moves: list[bool] = []
        self.image_index: int = 0


    def add_neighbor(self, direction: int, cell: "Cell") -> None:
        self.neighbors[direction] = cell


    def get_neighbor(self, direction: int) -> "Cell":
        if direction in self.neighbors:
            return self.neighbors[direction]
        else:
            return None

    def get_random_neighbor(self) -> "Cell":
        cell_list = list(self.neighbors.values())
        return random.choice(cell_list)


    def get_all_neighbors(self) -> list["Cell"]:
        return list(self.neighbors.values())


    def link(self, cell: "Cell") -> None:
        self.links.append(cell)
        cell.links.append(self)


    def get_number_links(self) -> int:
        return len(self.links)

    def is_direction_linked(self, direction) -> bool:
        res = False
        
        if direction not in self.neighbors:
            res = True
        elif self.neighbors[direction] not in self.links:
            res = True
        
        return res
    
    def get_allowed_moves(self) -> list[bool]:
        res: list[bool] = []

        for dir in range(4):
            res.append(self.is_direction_linked(dir))
        
        return res