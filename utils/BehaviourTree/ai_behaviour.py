from enum import IntEnum, StrEnum, auto
import random
from abc import ABC
from collections.abc import Callable
from rich import print


# from src.npc.bases.ai_behaviour_base import AIBehaviourBase, AIState
from behaviour.ai_behaviour_tree_base import ContextType, NodeWrapper
# from src.settings import SCALED_TILE_SIZE


# TODO: Refactor NPCState into Entity.state (maybe override Entity.get_state())
class AIState(StrEnum):
    IDLE = auto()
    BUSY = auto()


class AIBehaviour(ABC):
    def __init__(self, behaviour_tree_context: ContextType):  # noqa
        """
        !IMPORTANT! AIBehaviour doesn't call Entity.__init__ while still
        relying on it. Be aware that when inheriting from AIBehaviour you
        should first inherit from Entity itself, or inherit from another class
        that has Entity as base.
        """
        # AI-controlled Entities will idle for 1-4s on game start
        self.pf_state = AIState.IDLE
        self.pf_state_duration = 1 + random.random() * 3

        self.pf_path: list[tuple[int, int]]
        """The current path on which the NPC is moving.
        Each tile on which the NPC is moving is represented by its own
        coordinate tuple, while the first one in the list always being the NPCs
        current target position."""

        self.behaviour_tree_context = behaviour_tree_context
        self.conditional_behaviour_tree = None
        self.continuous_behaviour_tree = None

        self.__on_path_abortion_functions = []
        self.__on_path_completion_functions = []

        self.__on_stop_moving_functions = []

    #############################################################################################################
    @property
    def conditional_behaviour_tree(self):
        return self._conditional_behaviour_tree

    #############################################################################################################
    @conditional_behaviour_tree.setter
    def conditional_behaviour_tree(self, value: NodeWrapper | None):
        self._conditional_behaviour_tree = value

    #############################################################################################################
    @property
    def continuous_behaviour_tree(self):
        return self._continuous_behaviour_tree

    #############################################################################################################
    @continuous_behaviour_tree.setter
    def continuous_behaviour_tree(self, value: NodeWrapper | None):
        self._continuous_behaviour_tree = value

    #############################################################################################################
    def on_path_abortion(self, func: Callable[[], None]):
        self.__on_path_abortion_functions.append(func)
        return

    #############################################################################################################
    def abort_path(self):
        self.pf_state = AIState.IDLE
        # self.direction.update((0, 0))
        self.pf_state_duration = 1 + random.random() * 1

        for func in self.__on_path_abortion_functions:
            func()

        self.stop_moving()
        return

    #############################################################################################################
    def on_path_completion(self, func: Callable[[], None]):
        self.__on_path_completion_functions.append(func)
        return

    #############################################################################################################
    def complete_path(self):
        self.pf_state = AIState.IDLE
        # self.direction.update((0, 0))
        self.pf_state_duration = 2 + random.random() * 3

        for func in self.__on_path_completion_functions:
            func()

        self.stop_moving()
        return

    #############################################################################################################
    def exit_idle(self):
        if self.conditional_behaviour_tree is not None:
            self.conditional_behaviour_tree.run(self.behaviour_tree_context)

    #############################################################################################################
    def on_stop_moving(self, func: Callable[[], None]):
        self.__on_stop_moving_functions.append(func)
        return

    #############################################################################################################
    def stop_moving(self):
        for func in self.__on_stop_moving_functions:
            func()

        self.__on_path_abortion_functions.clear()
        self.__on_path_completion_functions.clear()
        self.__on_stop_moving_functions.clear()
        return

    def start_moving(self) -> bool:
        """
        Initiates the AI-controlled Entity to move to the specified tile.

        Note: Path generation has a high performance impact,
        calling it too often at once will cause the game to stutter

        :param coord: Coordinate of the tile the Entity should move to.
        :param pf_grid: (Optional) pathfinding grid to use. Defaults to self.pf_grid
        :return: Whether the path has successfully been created.
        """

    #     if pf_grid is None:
    #         pf_grid = self.pf_grid

    #     if not pf_grid.walkable(coord[0], coord[1]):
    #         return False

    #     # current NPC position on the tilemap
    #     tile_coord = (
    #         pygame.Vector2(self.hitbox_rect.centerx, self.hitbox_rect.centery)
    #         / SCALED_TILE_SIZE
    #     )

        self.pf_state = AIState.BUSY
        self.pf_state_duration = 3.0

    #     pf_grid.cleanup()

    #     try:
    #         start = pf_grid.node(int(tile_coord.x), int(tile_coord.y))
    #     except IndexError as e:
    #         # FIXME: Occurs when NPCs get stuck inside each other at the edge
    #         #  of the map and one of them gets pushed out of the walkable area
    #         warnings.warn(f"NPC is at invalid location {tile_coord}\nFull error: {e}")
    #         return False
    #     end = pf_grid.node(*[int(i) for i in coord])

    #     path_raw = self.pf_finder.find_path(start, end, pf_grid)

    #     # The first position in the path will always be removed as it is the
    #     # same coordinate the NPC is already standing on. Otherwise, if the NPC
    #     # is just standing a little bit off the center of its current
    #     # coordinate, it may turn around quickly once it reaches it, if the
    #     # second coordinate of the path points in the same direction as where
    #     # the NPC was just standing.
    #     self.pf_path = [(i.x + 0.5, i.y + 0.5) for i in path_raw[0][1:]]

    #     if not self.pf_path:
    #         return False

    #     return True

    # def create_step_to_coord(self, coord: tuple[float, float]) -> bool:
    #     self.pf_path.append((coord[0] / SCALED_TILE_SIZE, coord[1] / SCALED_TILE_SIZE))
    #     return True

    #############################################################################################################
    def move(self, dt: float):
        if self.pf_state == AIState.IDLE:
            self.update_idle(dt)

        if self.pf_state == AIState.BUSY:
            self.update_moving(dt)

    #############################################################################################################
    def update_idle(self, dt: float):
        # print("NPC is [magenta]idle")
        self.pf_state_duration -= dt

        if self.pf_state_duration <= 0:
            self.exit_idle()

    #############################################################################################################
    def update_moving(self, dt: float):
        print("NPC is on the [magenta]move")
        self.pf_state_duration -= dt

        if self.pf_state_duration <= 0:
            # runs in case the path has been emptied in the meantime
            #  (e.g. NPCBehaviourMethods.wander_to_interact created a path
            #   to a tile adjacent to the NPC)
            self.complete_path()
            return

        # # Get the next point in the path
        # next_point = self.pf_path[0]

        # # current exact NPC position on the tilemap
        # current_point = (
        #     self.hitbox_rect.centerx / SCALED_TILE_SIZE,
        #     self.hitbox_rect.centery / SCALED_TILE_SIZE,
        # )

        # # remaining distance the NPC moves in the current frame
        # remaining_distance = self.speed * dt / SCALED_TILE_SIZE

        # while remaining_distance:
        #     if current_point == next_point:
        #         # the NPC reached its current target position
        #         self.pf_path.pop(0)

        #     if not self.pf_path:
        #         # the NPC has completed its path
        #         self.complete_path()
        #         break

        #     next_point = self.pf_path[0]

        #     # x- and y-distances from the NPCs current position to its
        #     # target position
        #     dx = next_point[0] - current_point[0]
        #     dy = next_point[1] - current_point[1]

        #     distance = (dx**2 + dy**2) ** 0.5

        #     if remaining_distance >= distance:
        #         # the NPC reaches its current target position in the
        #         # current frame
        #         current_point = next_point
        #         remaining_distance -= distance
        #     else:
        #         # the NPC does not reach its current target position in the
        #         # current frame, so it continues to move towards it
        #         current_point = (
        #             current_point[0] + dx * remaining_distance / distance,
        #             current_point[1] + dy * remaining_distance / distance,
        #         )
        #         remaining_distance = 0

        #         # Rounding the direction leads to smoother animations,
        #         #  e.g. if the distance vector was (-0.99, -0.01), the NPC
        #         #  would face upwards, although it moves much more to the
        #         #  left than upwards, as the get_facing_direction method
        #         #  favors vertical movement
        #         self.direction.update((round(dx / distance), round(dy / distance)))

        # self.hitbox_rect.update(
        #     (
        #         current_point[0] * SCALED_TILE_SIZE - self.hitbox_rect.width / 2,
        #         current_point[1] * SCALED_TILE_SIZE - self.hitbox_rect.height / 2,
        #     ),
        #     self.hitbox_rect.size,
        # )

        # self.check_collision()

        # if self.is_colliding:
        #     self.abort_path()

    #############################################################################################################
    def update(self, dt: float):
        if self.continuous_behaviour_tree is not None:
            self.continuous_behaviour_tree.run(self.behaviour_tree_context)
