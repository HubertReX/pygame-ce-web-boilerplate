# from dataclasses import dataclass
import math
import os
import random
from enum import Enum, auto
from typing import Any
from rich import print

import pygame
from maze_generator.maze_utils import a_star_cached
from pygame.math import Vector2 as vec
from settings import (
    INVENTORY_ITEM_SCALE,
    MAX_NO_ATTEMPTS_TO_FIND_RANDOM_POS,
    NPC_MAX_REST_TIME,
    NPC_MIN_REST_TIME,
    NPC_RANDOM_WALK_DISTANCE,
    SHOULD_NPC_REST_PROBABILITY,
    SPRITE_SHEET_DEFINITIONS,
    ANIMATION_SPEED,
    AVATAR_SCALE,
    CHARACTERS_DIR,
    DIALOGS_DIR,
    HEIGHT,
    INPUTS,
    IS_WEB,
    JOY_MOVE_MULTIPLIER,
    MAX_HOTBAR_ITEMS,
    MONSTER_WAKE_DISTANCE,
    PUSHED_TIME,
    RECALCULATE_PATH_DISTANCE,
    SCALE,
    STEP_COST_WALL,
    SPRITE_SHEET_DEFINITION_4x7,
    STUNNED_COLOR,
    STUNNED_TIME,
    TILE_SIZE,
    WEAPON_DIRECTION_OFFSET,
    WEAPON_DIRECTION_OFFSET_FROM,
    Point,
    import_sprite_sheet,
    lerp_vectors,
    tuple_to_vector,
    vector_to_tuple,
)
from enums import AttitudeEnum, ItemTypeEnum, RaceEnum, NPCEventActionEnum
if IS_WEB:
    from config_model.config import Character
else:
    from config_model.config_pydantic import Character  # type: ignore[assignment]

import game
import npc_state
import scene
import splash_screen
from objects import ChestSprite, EmoteSprite, HealthBar, HealthBarUI, ItemSprite, NotificationTypeEnum, Shadow
from animation.transitions import AnimationTransition


#################################################################################################################
# MARK: NPC
# @dataclass(slots=True)
class NPC(pygame.sprite.Sprite):
    def __init__(
            self,
            game: game.Game,
            scene: scene.Scene,
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: tuple[int, int],
            name: str,
            emotes: dict[str, list[pygame.Surface]],
            waypoints: tuple[Point, ...] = (),
            model_name: str = "",
    ):

        self.name = name
        if not model_name:
            model_name = self.name
        super(NPC, self).__init__()
        self.game = game
        self.scene = scene
        self.model: Character = game.conf.characters[model_name]
        self.current_map = self.scene.current_map
        self.dialogs: str | None = None
        self.has_dialog: bool = False

        self.load_dialogs()

        self.shadow_group = shadow_group
        self.label_group = label_group
        self.pos: vec = vec(pos[0], pos[1])
        self.prev_pos: vec = self.pos.copy()

        self.shadow = self.create_shadow()
        self.health_bar = self.create_health_bar()
        # hide health bar at start (negative value makes it transparent)
        self.health_bar.hide()
        self.items: list[ItemSprite] = []
        self.selected_weapon: ItemSprite | None = None
        self.selected_item_idx: int = -1
        self.total_items_weight: float = 0.0
        self.animations: dict[str, list[pygame.surface.Surface]] = {}

        tile_width = 16
        tile_height = 16
        self.sprite_sheet_type: str = ""

        sprite_file_name = str(CHARACTERS_DIR / self.model.sprite / "SpriteSheet.png")
        tile_width, sheet = self.set_sprite_sheet_type(sprite_file_name)

        self.animations = import_sprite_sheet(
            sprite_file_name,
            tile_width,
            tile_height,
            sprite_sheet_definition=sheet,
        )
        self.masks: dict[str, list[pygame.mask.Mask]] = {}
        self.animation_speed = ANIMATION_SPEED
        self.avatar = pygame.image.load(str(CHARACTERS_DIR / self.model.sprite / "Faceset.png")).convert_alpha()
        # Player avatar will be shown on the right side of the screen
        # and need to be flipped to face left
        if self.model.name != "Player":
            self.avatar = pygame.transform.flip(self.avatar, True, False)

        self.avatar = pygame.transform.scale(self.avatar, (TILE_SIZE * AVATAR_SCALE, TILE_SIZE * AVATAR_SCALE))
        self.emote: EmoteSprite = EmoteSprite(label_group, pos, emotes)

        self.generate_masks()
        self.frame_index: float = 0.0
        self.image = self.animations["idle_down"][int(self.frame_index)]
        self.mask = self.masks["idle_down"][int(self.frame_index)]

        self.tileset_coord: Point = self.get_tileset_coord()
        self.rect: pygame.FRect = self.image.get_frect(midbottom = self.pos)
        # hit box size is half the TILE_SIZE, bottom, centered
        self.feet = pygame.Rect(0, 0, self.rect.width // 2, TILE_SIZE // 2)
        self.feet.midbottom = (int(self.pos.x), int(self.pos.y))
        # individual steps to follow (mainly a center of a given tile, but pixel accurate)
        # provided by A* path finding
        self.waypoints: tuple[Point, ...] = waypoints
        self.waypoints_cnt: int = len(waypoints)
        self.current_waypoint_no: int = 0
        # list of targets to follow
        self.target: vec = vec(0, 0)
        self.targets: list[vec] = []

        # NPC met in the game
        self.npc_met: NPC | None = None
        # Chest object near player
        self.chest_in_range: ChestSprite | None = None

        # is in attacking state
        self.is_attacking: bool = False
        # game time (time_elapsed) when last attack was made
        self.attack_time: float  = 0.0
        # how long to wait before next attack (in mili seconds)
        self.attack_cooldown: int = 200
        # double check cooldown since events fail
        self.weapon_cooldown: float = 0.0

        self.can_switch_weapon: bool = True
        # how long to wait before next weapon switch (in mili seconds)
        self.switch_duration_cooldown: int = 400
        # double check cooldown since events fail
        self.switch_cooldown: float = 0.0
        # rest duration
        self.end_rest_time: float = -1.0

        # basic planar (N,E, S, W) physics
        # speed in pixels per second
        self.speed_walk: int = self.model.speed_walk
        self.speed_run: int = self.model.speed_run
        self.speed: int = random.choice([self.speed_walk, self.speed_run])
        if self.model.attitude == AttitudeEnum.enemy or self.model.race == RaceEnum.animal:
            self.speed = self.speed_walk

        # movement inertia
        self.force: int = 2000
        self.friction: int = -12
        self.acc: vec = vec(0, 0)
        self.vel: vec = vec(0, 0)

        # jump/fly physics
        self.up_force: int = 3200
        self.up_friction: int = -1
        self.up_acc: float = 0.0
        self.up_vel: float = 0.0

        self.jumping_offset: int = 0
        # flags set by key strokes - not real NPC states
        self.is_dead = False
        self.is_flying = False
        self.is_jumping = False
        self.is_stunned = False
        self.is_talking = False

        # general purpose custom event, action is defined by the payload passed to event
        self.custom_event_id: int  = pygame.event.custom_type()
        self.register_custom_event()

        # actual NPC state, mainly to determine type of animation and speed
        self.state: npc_state.NPC_State = npc_state.Idle()
        self.state.enter_time = self.scene.game.time_elapsed

        self.load_items()

    #############################################################################################################
    def select_next_item(self) -> None:
        if len(self.items) > 0:
            self.selected_item_idx += 1
            if self.selected_item_idx >= len(self.items):
                self.selected_item_idx = 0

    #############################################################################################################
    def select_prev_item(self) -> None:
        if len(self.items) > 0:
            self.selected_item_idx -= 1
            if self.selected_item_idx < 0:
                self.selected_item_idx = len(self.items) - 1
    #############################################################################################################

    def register_custom_event(self) -> None:
        self.game.register_custom_event(self.custom_event_id, self.process_custom_event)

    #############################################################################################################

    def set_sprite_sheet_type(self, sprite_file_name: str) -> tuple[int, dict[str, list[tuple[int, int]]]]:
        width = pygame.image.load(sprite_file_name).get_width()
        if width in SPRITE_SHEET_DEFINITIONS:
            sheet = SPRITE_SHEET_DEFINITIONS[width]["sheet"]
            tile_width = SPRITE_SHEET_DEFINITIONS[width]["tile_width"]
            self.sprite_sheet_type = SPRITE_SHEET_DEFINITIONS[width]["type"]
        else:
            print(f"[red]ERROR![/] Unknown sprite sheet definitions width {width} for NPC {self.name}")
            sheet = SPRITE_SHEET_DEFINITION_4x7
            self.sprite_sheet_type = "4x7"
        return tile_width, sheet

    #############################################################################################################

    def __hash__(self) -> int:
        return hash(self.name)

    #############################################################################################################
    def load_items(self) -> None:
        for item_name in self.model.items:
            item = self.scene.create_item(item_name, 0, 0, show=False)
            self.pick_up(item)

    #############################################################################################################

    def load_dialogs(self) -> None:
        if self.model.attitude == AttitudeEnum.friendly:
            modal_panel_file = DIALOGS_DIR / f"{self.model.name}.md"
            if modal_panel_file.exists():
                self.dialogs = modal_panel_file.read_text()
                self.has_dialog = True

    #############################################################################################################
    def generate_masks(self) -> None:
        # _mask = pygame.mask.from_surface(self.image)
        for key, animation in self.animations.items():
            masks = [pygame.mask.from_surface(frame) for frame in animation]
            self.masks[key] = masks

    #############################################################################################################

    def create_health_bar(self) -> HealthBar:
        return HealthBar(self.name,
                         self.model,
                         self.game.render_text,
                         self.label_group,
                         vector_to_tuple(self.pos)
                         )

    #############################################################################################################
    def create_shadow(self) -> Shadow:
        empty: bool = False
        # TODO: add proper handling of shadows hiding when NPC is in water
        if "Fish" in self.model.name:
            empty = True
        return Shadow(self.shadow_group, (0, 0), (TILE_SIZE - 2, 6), empty)

    #############################################################################################################
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    #############################################################################################################
    def get_tileset_coord(self, pos: vec | None = None, offset_y: int = -4) -> Point:
        """
        map position in world coordinates to tileset grid
        """
        if not pos:
            pos = self.pos

        # shift up by 4 pixels since perceived location is different than actual Sprite position on screen
        return Point(int(pos.x // TILE_SIZE), int((pos.y + offset_y) // TILE_SIZE))

    #############################################################################################################

    # def import_image(self, path: str) -> None:
    #     """
    #     old implementation used with separate img per frame (e.g. monochrome_ninja)
    #     """
    #     # self.animations = self.game.get_animations(path)
    #     animations_keys: list[str] = []  # list(self.animations.keys())
    #     for animation in animations_keys:
    #         full_path = os.path.join(path, animation)
    #         self.animations[animation] = self.game.get_images(full_path)
    #         if animation in ["idle", "run"]:
    #             self.animations[f"{animation}_right"] = []
    #             self.animations[f"{animation}_left"] = []
    #             for frame in self.animations[animation]:
    #                 converted = frame
    #                 # converted = frame.convert_alpha()
    #                 # converted.set_colorkey(COLORS["yellow"])
    #                 self.animations[f"{animation}_right"].append(converted)
    #                 self.animations[f"{animation}_left"].append(pygame.transform.flip(converted, True, False))

    #############################################################################################################
    # MARK: animate
    def animate(self, state: str, dt: float, loop: bool = True) -> None:
        self.frame_index += dt

        if self.frame_index >= len(self.animations[state]):
            self.frame_index = 0.0 if loop else len(self.animations[state]) - 1.0

        self.image = self.animations[state][int(self.frame_index)].copy()
        self.mask = self.masks[state][int(self.frame_index)].copy()

        self.emote.animate(dt)
        if self.is_stunned:
            # self.emote.set_emote("shocked_anim")
            red_filter = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            red_filter.fill(STUNNED_COLOR)
            # self.image.blit(red_filter, (0, 0))
            # red_filter.blit(self.image, (0, 0))
            # self.image = red_filter

            value = math.sin(self.game.time_elapsed * 200.0)
            value = 255 if value >= 0 else 0
            self.image.set_alpha(value)
            if self.selected_weapon and self.selected_weapon.image:
                self.selected_weapon.image.set_alpha(value)
        else:
            self.image.set_alpha(255)
            if self.selected_weapon and self.selected_weapon.image:
                self.selected_weapon.image.set_alpha(255)

    #############################################################################################################
    def get_direction_360(self) -> str:
        if self.npc_met and self.is_talking:
            direction = self.npc_met.pos - self.pos
            angle = vec(0, -1).angle_to(direction)
        else:
            angle = vec(0, -1).angle_to(self.vel)
        angle = (angle + 360) % 360

        dir: str
        match self.sprite_sheet_type:
            case "2x1":
                dir = self.get_direction_RL(angle)
            case "2x2":
                dir = self.get_direction_RDL(angle)
            case "3x3":
                dir = self.get_direction_RDLU(angle)
            case "4x7":
                dir = self.get_direction_RDLU(angle)
            case _:
                dir = "down"

        return dir

    #############################################################################################################

    def get_direction_RL(self, angle: float) -> str:
        return "right" if angle < 180.0 else "left"

    #############################################################################################################

    def get_direction_RDL(self, angle: float) -> str:
        if 0.0 <= angle < 135.0:
            return "right"
        elif 135.0 <= angle < 225.0:
            return "down"
        else:
            return "left"

    #############################################################################################################

    def get_direction_RDLU(self, angle: float) -> str:
        if 45.0 <= angle < 135.0:
            return "right"
        elif 135.0 <= angle < 225.0:
            return "down"
        elif 225.0 <= angle < 315.0:
            return "left"
        else:
            return "up"

    #############################################################################################################
    # MARK: movement
    def movement(self) -> None:
        if self.is_stunned or self.is_talking:
            return

        if self.model.race == RaceEnum.monster:
            self.movement_monster()
        # elif self.model.attitude == AttitudeEnum.afraid:
        elif self.model.race == RaceEnum.animal:
            self.movement_animal()

        self.follow_waypoints()

    #############################################################################################################
    def movement_animal(self) -> None:
        # distance_from_player = (self.pos - self.scene.player.pos).magnitude_squared()
        distance_from_target = (self.pos - self.target).magnitude_squared()

        if self.waypoints_cnt == 0 or distance_from_target < 4**2:
            should_rest: bool = random.randint(0, 100) < SHOULD_NPC_REST_PROBABILITY
            if self.end_rest_time < 0.0 and should_rest:
                self.target = vec(0, 0)
                self.waypoints = ()
                self.waypoints_cnt = 0
                self.speed = 0

                delta = NPC_MAX_REST_TIME - NPC_MIN_REST_TIME
                self.end_rest_time = self.game.time_elapsed + NPC_MIN_REST_TIME + random.random() * delta
                # print(f"({self.game.time_elapsed:4.1f}) [yellow]{self.name}[/] "
                #       f"will rest for {(self.end_rest_time - self.game.time_elapsed):4.1f} sec ")
            else:
                if self.game.time_elapsed > self.end_rest_time:
                    # print(f"({self.game.time_elapsed:4.1f}) [yellow]{self.name}[/] will no longer rest")
                    self.end_rest_time = -1.0
                    self.speed = self.speed_walk
                    # current_way_point_vec.distance_squared_to(npc_pos) <= 2.0

                    target_vec = self.get_random_safe_pos(self.pos, range=NPC_RANDOM_WALK_DISTANCE)

                    self.target = target_vec
                    self.find_path()
                    self.check_waypoints_in_exit()

    #############################################################################################################

    def get_random_safe_pos(
        self,
        start_pos: vec,
        range: float = 1.0,
        check_exits: bool = True,
        check_allowed_zones: bool = True,
        allow_start_pos: bool = True,
    ) -> vec:

        repeat = True
        repeat_cnt: int = 0
        new_rect = pygame.FRect(0.0, 0.0, TILE_SIZE, TILE_SIZE)  # self.rect.copy()

        while repeat:
            repeat_cnt += 1
            target_vec = start_pos + self.get_random_pos(range, range)
            new_rect.center = target_vec  # type: ignore[assignment]

            if repeat_cnt > MAX_NO_ATTEMPTS_TO_FIND_RANDOM_POS:
                print(
                    f"[red]ERROR![/] in [magenta]get_random_safe_pos[/] can't find safe pos for [blue]{self.name}[/]"
                    f" from {start_pos}!")
                return target_vec

            # check if new position is within rect around start position
            if not allow_start_pos:
                start_rect = pygame.FRect(0, 0, TILE_SIZE, TILE_SIZE)
                start_rect.center = start_pos  # type: ignore[assignment]
                if start_rect.collidepoint(target_vec):
                    print("[yellow]Warning[/] same position not allowed")
                    continue

            # check if new pos is not on exit
            if check_exits:
                if self.check_pos_is_exit(target_vec):
                    continue

            # check if new pos is inside one of allowed zones
            if check_allowed_zones:
                if len(self.model.allowed_zones) > 0:
                    matched_any_zone: bool = False
                    for zone_name in self.model.allowed_zones:
                        allowed_zones = self.scene.zones[zone_name]
                        for zone in allowed_zones:
                            if zone.contains(new_rect):
                                matched_any_zone = True
                                # print(f"[magenta]Zone: {zone_name}[/] matched for [blue]{self.name}[/]!")
                                break
                        if matched_any_zone:
                            break
                    if not matched_any_zone:
                        # zone_names = ", ".join(self.model.allowed_zones)
                        # print(f"[red]ERROR![/] [blue]{self.name}[/] outside of zones ({zone_names})!")
                        continue

            # check if new position is in map bounds
            target_grid = self.get_tileset_coord(target_vec, offset_y=0)
            # target_grid.x -= 1
            # target_grid.y -= 1
            grid = self.scene.path_finding_grid
            if target_grid.y < 0 or target_grid.y >= len(grid) or \
                    target_grid.x < 0 or target_grid.x >= len(grid[0]):
                continue

            # check if new position is not on a wall
            value = grid[target_grid.y][target_grid.x]
            if value < 0:
                repeat = False

        return target_vec

    #############################################################################################################
    def check_waypoints_in_exit(self) -> None:
        # check if waypoints are inside one of the exits
        new_waypoints: list[Point] = []
        for waypoint in self.waypoints:
            if self.check_pos_is_exit(waypoint.as_vector):
                break
            new_waypoints.append(waypoint)

        # accept only waypoints that are before the on in exit
        self.waypoints = tuple(new_waypoints)
        self.waypoints_cnt = len(new_waypoints)
        if self.current_waypoint_no > self.waypoints_cnt - 1:
            self.current_waypoint_no = 0

    #############################################################################################################

    def check_pos_is_exit(self, target_vec: vec) -> bool:
        for exit in self.scene.exit_sprites:
            if exit.rect.collidepoint(target_vec):
                return True

        return False

    #############################################################################################################

    def movement_monster(self) -> None:
        distance_from_player = (self.pos - self.scene.player.pos).magnitude_squared()
        # activate monsters in maze when player is near
        # no designated waypoints, distance from player in range, is enemy
        if self.waypoints_cnt == 0 and distance_from_player < MONSTER_WAKE_DISTANCE**2:
            self.target = self.scene.player.pos.copy()
            self.speed = self.speed_run
            self.emote.set_temporary_emote("red_exclamation_anim", 4.0)
            self.find_path()
            # if character has a set target (and needs to follow it) or there are no waypoints to follow any more
        elif self.target != vec(0, 0):  # or self.waypoints_cnt == 0:
            # if (no more waypoints or the player has moved) and (character is a monster chasing player)
            # not self.target == self.scene.player.pos)
            distance_player_moved = (self.target - self.scene.player.pos).magnitude_squared()

            # if (self.waypoints_cnt == 0 or not self.target == self.scene.player.pos) and \
            #     self.model.attitude == AttitudeEnum.enemy.value:
            if (distance_player_moved > RECALCULATE_PATH_DISTANCE ** 2) \
                    and self.model.attitude == AttitudeEnum.enemy:
                self.target = self.scene.player.pos.copy()
                self.find_path()

    #############################################################################################################
    def follow_waypoints(self) -> None:
        if self.waypoints_cnt <= 0:
            return

        npc_pos = self.pos
        current_way_point_vec = self.waypoints[self.current_waypoint_no].as_vector
        current_way_point_vec.y += 4
        # skip to next waypoint when within around 1 pixel
        if current_way_point_vec.distance_squared_to(npc_pos) <= 2.0:
            self.current_waypoint_no += 1
            # if following target and reached goal do not start over again
            if self.current_waypoint_no >= self.waypoints_cnt:
                if self.target != vec(0, 0):
                    return self.clear_waypoints()
                else:
                    self.current_waypoint_no = 0
                current_way_point_vec = self.waypoints[self.current_waypoint_no].as_vector
                current_way_point_vec.y += 4
        direction = current_way_point_vec - npc_pos
        direction = direction.normalize() * self.force
        self.acc.x = direction.x
        self.acc.y = direction.y

    #############################################################################################################
    def clear_waypoints(self) -> None:
        self.target = vec(0, 0)
        self.waypoints = ()
        self.waypoints_cnt = 0
        self.current_waypoint_no = 0
        self.acc = vec(0, 0)
        # self.vel = vec(0, 0)
        if self.model.attitude == AttitudeEnum.enemy:
            self.speed = self.speed_walk

        return

    #############################################################################################################
    def find_path(self) -> None:
        start = (self.tileset_coord.y, self.tileset_coord.x)
        target = self.get_tileset_coord(self.target)
        goal = (target.y, target.x)
        # fps = f"FPS:\t{self.game.fps: 6.1f}\t3s:\t{self.game.avg_fps_3s: 6.1f}
        # \t10s:\t{self.game.avg_fps_10s: 6.1f}\ttime:\t{self.game.time_elapsed:4.1f}"
        if path := a_star_cached(start=start, goal=goal, grid=self.scene.path_finding_grid):
            self.generate_waypoints_from_path(path, start)
        else:
            print(f"[red]ERROR![/] Path not found for npc '{self.name}'!")
            # self.scene.add_notification(
            #     f"Path not found for npc '[char]{self.name}[/char]'", NotificationTypeEnum.debug)
            self.waypoints = ()
            self.waypoints_cnt = 0
            self.acc = vec(0, 0)
            self.vel = vec(0, 0)

        self.current_waypoint_no = 0

    def generate_waypoints_from_path(self, path: list[tuple[int, int]], start: tuple[int, int]) -> None:
        waypoints = []
        path_list = list(path)
        # if first waypoint is the same map grid, than skip it
        # hack to prevent NPC jitter (coming back to center of current grid, than to next,
        # but then path is recalculated and goes back to current grid center)
        start_index = 1 if len(path_list) >= 2 and path_list[0] == start else 0
        # when following Player, stop 1 step before
        # for waypoint in path_list[start_index:-1]:
        for waypoint in path_list[start_index:]:
            y, x = waypoint
            p = Point(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
            waypoints.append(p)
        self.waypoints_cnt = len(waypoints)
        self.waypoints = tuple(waypoints)

    #############################################################################################################
    def jump(self) -> None:
        self.is_jumping = True
        self.up_acc = self.up_force
        # self.up_vel = 50
        self.jumping_offset = 1

    #############################################################################################################
    # MARK: physics
    def physics(self, dt: float) -> None:
        if self.is_stunned or self.is_attacking:
            self.adjust_rect()
            return

        self.prev_pos = self.pos.copy()

        self.acc.x += self.vel.x * self.friction
        self.vel.x += self.acc.x * dt

        self.acc.y += self.vel.y * self.friction
        self.vel.y += self.acc.y * dt

        if self.tileset_coord.y < len(self.scene.path_finding_grid) and \
                self.tileset_coord.x < len(self.scene.path_finding_grid[0]):
            step_cost = abs(self.scene.path_finding_grid[self.tileset_coord.y][self.tileset_coord.x]) or 1
        else:
            step_cost = 1
        speed = (self.speed * (100 / step_cost))

        if self.vel.magnitude() >= speed:
            if speed > 0:
                self.vel = self.vel.normalize() * speed

        if speed == 0:
            self.acc = vec(0, 0)
            self.vel = vec(0, 0)

        if self.is_flying:
            oscillation = 1 if self.scene.game.time_elapsed % 0.25 < 0.125 else 0
            self.jumping_offset = TILE_SIZE + oscillation
        else:
            if not self.is_jumping:
                self.jumping_offset = 0

        if self.is_jumping:
            self.up_acc += self.up_vel * self.up_friction
            self.up_vel += self.up_acc * dt
            # + (self.up_vel / 2) * dt
            self.jumping_offset = int(self.up_vel * dt)
            if self.jumping_offset <= 0:
                self.is_jumping = False
                self.up_acc = 0.0
                self.up_vel = 0.0
                self.jumping_offset = 0

                # TODO not a good place to do it
                self.scene.group.change_layer(self, self.scene.sprites_layer)

        self.pos.x += self.vel.x * dt + (self.vel.x / 2) * dt
        self.pos.y += self.vel.y * dt + (self.vel.y / 2) * dt

        self.adjust_rect()

    #############################################################################################################
    def change_state(self) -> None:
        if new_state := self.state.enter_state(self):
            new_state.enter_time = self.scene.game.time_elapsed
            # print(self.model.name, new_state)
            self.state = new_state

    #############################################################################################################
    def set_entry_point(self, entry_point: str, default: vec) -> bool:
        if entry_point in self.scene.entry_points:
            result: bool = True
            # set first start position for the Player
            ep = self.scene.entry_points[entry_point]
            self.pos = vec(ep.x, ep.y)
            self.adjust_rect()
        else:
            result = False
            print(f"\n[red]ERROR![/] [char]{self.model.name}[/] no entry point found!\n")
            self.pos = default

        return result

    #############################################################################################################
    def check_scene_exit(self) -> None:
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.current_map = exit.to_map
                # self.set_entry_point(exit.entry_point, vec(0, 0))
                # self.scene.NPCs.remove(self)
                # self.scene.group.remove(self)
                # self.shadow.kill()
                # self.health_bar.kill()
                # self.emote.kill()
                self.die(drop_items=False)
                # TODO NPC goes to another map

    #############################################################################################################

    def get_random_pos(self, x_tiles: float = 1.0, y_tiles: float = 1.0) -> vec:
        x = -x_tiles + random.random() * 2.0 * x_tiles
        y = -y_tiles + random.random() * 2.0 * y_tiles

        return vec(x * TILE_SIZE * SCALE, y * TILE_SIZE * SCALE)

    #############################################################################################################
    def die(self, drop_items: bool = True) -> None:
        self.scene.NPCs = [npc for npc in self.scene.NPCs if npc != self]
        self.shadow.kill()
        self.health_bar.kill()
        self.emote.kill()

        # drop items and money on the ground
        if self.model.name != "Player" and drop_items:
            self.is_dead = True

            for item in self.items:
                self.selected_item_idx = len(self.items) - 1
                if self.drop_item():
                    item.rect.center = self.get_random_safe_pos(
                        self.pos, check_allowed_zones=False)  # type: ignore[assignment]
                    self.scene.items.append(item)
                    self.scene.item_sprites.add(item)
                    self.scene.group.add(item, layer=self.scene.sprites_layer - 1)

            if self.model.money >  0:
                pos: vec = self.get_random_safe_pos(self.pos, check_allowed_zones=False)  # type: ignore[assignment]
                item = self.scene.create_item("golden_coin", int(pos[0]), int(pos[1]))
                item.model.value = self.model.money
                self.scene.items.append(item)
                self.scene.item_sprites.add(item)
                self.scene.group.add(item, layer=self.scene.sprites_layer - 1)

        if self.model.name == "Player" and self.model.health <= 0:
            self.is_dead = True
            self.scene.exit_state()
            self.scene.player.reset()
            scene.Scene(self.game, "Village", "start").enter_state()
            splash_screen.SplashScreen(self.game, "GAME OVER").enter_state()

        self.kill()

    #############################################################################################################
    def update(self, dt: float) -> None:
        self.state.update(dt, self)
        self.change_state()

    #############################################################################################################

    def check_cooldown(self) -> None:
        if self.is_attacking and self.game.time_elapsed > self.weapon_cooldown:
            self.is_attacking = False
            self.scene.group.remove(self.selected_weapon)

        if not self.can_switch_weapon and self.game.time_elapsed > self.switch_cooldown:
            self.can_switch_weapon = True

    #############################################################################################################

    def slide(self, colliders: list[Any]) -> None:
        move_vec = self.pos - self.prev_pos
        # can't move by full vector,
        # first try move ony in one axis (reset the movement along the other axis to zero)

        # slide along y axis
        self.pos.x -= move_vec.x
        self.adjust_rect()
        if self.feet.collidelist(colliders) == -1:
            # looks ok, so set prev pos
            self.prev_pos = self.pos.copy()
            return

        # slide along x axis
        self.pos.x += move_vec.x
        self.pos.y -= move_vec.y
        self.adjust_rect()
        if self.feet.collidelist(colliders) == -1:
            # looks ok, so set prev pos
            self.prev_pos = self.pos.copy()
            return

        # slide is not possible, block movement
        self.move_back()

    #############################################################################################################
    # MARK: process_custom_event
    def process_custom_event(self, **kwargs: str) -> None:
        # if self.model.name == "Player":
        #     print(kwargs["action"])

        action = kwargs.get("action", "")
        if action == NPCEventActionEnum.pushed:
            # pushed state is invalidated
            # show health bar
            self.health_bar.hide()
        elif action ==  NPCEventActionEnum.stunned:
            # stunned state is invalidated
            # show health bar
            self.health_bar.hide()
            self.is_stunned = False
            if self.model.health == 0:
                self.die()

        elif action ==  NPCEventActionEnum.attacking:
            # attack cool off end
            self.is_attacking = False
            self.scene.group.remove(self.selected_weapon)
        elif action ==  NPCEventActionEnum.switching_weapon:
            # switching weapon cool off end
            self.can_switch_weapon = True
        else:
            print(f"unknown action '{action}' for npc '{self.name}'")
            self.scene.add_notification(
                f"unknown action '[act]{action}[/act]' for npc '[char]{self.name}[/char]'", NotificationTypeEnum.debug)

    #############################################################################################################
    # MARK: encounter

    def encounter(self, oponent: "NPC") -> None:
        if oponent.model.attitude == AttitudeEnum.enemy:
            # deal damage
            self.model.health -= oponent.model.damage
            if self.selected_weapon:
                damage = self.selected_weapon.model.damage
            else:
                damage = self.model.damage
            oponent.model.health -= damage

            self.model.health = max(0, self.model.health)
            oponent.model.health = max(0, oponent.model.health)

            # print(f"{self.name}: {self.model.health} opponent {oponent.name} {oponent.model.health}")
            if self.model.health == 0:
                self.die()

            # if oponent.model.health == 0:
            #     oponent.die()

            self.is_stunned = True
            self.set_event_timer(self, NPCEventActionEnum.stunned, STUNNED_TIME, 1)
            self.health_bar.show()

            oponent.is_stunned = True
            oponent.set_event_timer(oponent, NPCEventActionEnum.stunned, STUNNED_TIME, 1)
            oponent.emote.set_temporary_emote("fight_anim", 4.0)

            # show health bar (for STUNNED_TIME ms)
            # self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.health_bar.show()

            # push the npc
            player_move = self.pos - oponent.pos
            if not player_move == vec(0, 0):
                self.pos += player_move.normalize() * 8
                oponent.pos -= player_move.normalize() * 8

            # oponent_move = oponent.pos - oponent.prev_pos
            # if not oponent_move == vec(0, 0):
            #     oponent.pos += oponent_move.normalize() * TILE_SIZE
            self.acc = vec(0, 0)
            oponent.acc = vec(0, 0)
            self.adjust_rect()
            oponent.adjust_rect()
        else:
            # push the npc
            player_move = self.pos - self.prev_pos
            if player_move != vec(0, 0):
                oponent.pos += player_move.normalize() * TILE_SIZE
                oponent.emote.set_temporary_emote("shocked_anim", 4.0)
            oponent.adjust_rect()

            self.set_event_timer(self,    NPCEventActionEnum.pushed, PUSHED_TIME, 1)
            oponent.set_event_timer(oponent, NPCEventActionEnum.pushed, PUSHED_TIME, 1)

            # show health bar (for PUSHED_TIME ms)
            # self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.health_bar.show()
            # if oponent.has_dialog and oponent.dialogs:
            #     self.npc_met = oponent
            #     self.scene.ui.dialog_panel.set_text(oponent.dialogs)
            #     self.scene.ui.dialog_panel.formatted_text.scroll_top()

    #############################################################################################################
    # MARK: hit
    def hit(self, oponent: "NPC") -> None:
        if oponent.model.attitude == AttitudeEnum.enemy and self.is_attacking and self.selected_weapon:
            # deal damage to oponent only since we hit wit weapon
            damage = self.selected_weapon.model.damage
            oponent.model.health -= damage
            oponent.model.health = max(0, oponent.model.health)

            # print(f"{self.name}: {self.model.health} opponent {oponent.name} {oponent.model.health}")
            # if oponent.model.health == 0:
            #     oponent.die()

            oponent.is_stunned = True
            oponent.set_event_timer(oponent, NPCEventActionEnum.stunned, STUNNED_TIME, 1)

            # show health bar (for STUNNED_TIME ms)
            # self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.health_bar.show()

            # push the npc
            player_move = self.pos - oponent.pos
            if not player_move == vec(0, 0):
                # self.pos += player_move.normalize() * 8
                oponent.pos -= player_move.normalize() * 8

            # self.acc = vec(0, 0)
            oponent.acc = vec(0, 0)
            # self.adjust_rect()
            oponent.adjust_rect()
        # else:
        #     pass
            # push the npc
            # player_move = self.pos - self.prev_pos
            # if player_move != vec(0, 0):
            #     oponent.pos += player_move.normalize() * TILE_SIZE
            # oponent.adjust_rect()

            # self.set_event_timer(self,    NPCEventActionEnum.pushed, PUSHED_TIME, 1)
            # self.set_event_timer(oponent, NPCEventActionEnum.pushed, PUSHED_TIME, 1)

            # # show health bar (for PUSHED_TIME ms)
            # self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            # oponent.health_bar.set_bar(oponent.model.health / oponent.model.max_health, self.game)

    #############################################################################################################
    def set_event_timer(self, npc: "NPC", action: NPCEventActionEnum, interval: int, repeat: int) -> None:
        event = pygame.event.Event(npc.custom_event_id, action=action)
        pygame.time.set_timer(event, interval, repeat)

    #############################################################################################################
    def set_emote(self, emote: str) -> None:
        if self.has_dialog and str(self.state) in ["Idle", "Bored", "Walk", "Run"]:
            self.emote.set_emote("dots_anim")
        elif self.model.is_merchant and str(self.state) in ["Idle", "Bored", "Walk", "Run"]:
            self.emote.set_emote("$_anim")
        else:
            self.emote.set_emote(emote)

    #############################################################################################################
    def reset(self) -> None:
        self.shadow = self.create_shadow()
        self.emote = self.create_emote()
        self.health_bar = self.create_health_bar()
        self.is_attacking = False
        self.is_dead = False
        self.is_flying = False
        self.is_jumping = False
        self.is_stunned = False
        self.is_talking = False
        self.items = []
        self.selected_item_idx = -1
        self.load_items()
        self.model.health = self.model.max_health

    #############################################################################################################
    def create_emote(self) -> EmoteSprite:
        return EmoteSprite(self.scene.label_sprites, vector_to_tuple(self.pos), self.scene.icons)
    #############################################################################################################

    def move_back(self) -> None:
        """
        If called after an update, the sprite can move back

        """
        # self.debug([f"{self.rect.topleft=}", f"{self.old_rect.topleft=}"])
        self.pos = self.prev_pos.copy()
        if self.model.name == "Player":  # and self.scene.camera.target == self.prev_pos:
            self.scene.camera.target = self.pos

        self.adjust_rect()

    #############################################################################################################
    def adjust_rect(self) -> None:
        self.tileset_coord = self.get_tileset_coord()
        # display sprite n pixels above position so the shadow doesn't stick out from the bottom
        self.rect.midbottom = self.pos + vec(0,  -self.jumping_offset - 3)  # type: ignore[union-attr, assignment]
        # 'hitbox' for collisions
        self.feet.midbottom = vec(self.pos[0], self.pos[1])  # type: ignore[assignment]
        # shadow
        self.shadow.rect.midbottom =  vec(self.pos[0], self.pos[1])  # type: ignore[assignment]
        self.health_bar.rect.midtop =  vec(self.pos[0], self.pos[1])  # type: ignore[assignment]

        # if self.emote:
        self.emote.rect.midbottom = self.rect.midtop

        if self.selected_weapon and self.is_attacking:
            direction = self.get_direction_360()
            # how far between start attack time and weapon cooldown are we
            factor: float = max(0, self.weapon_cooldown - self.game.time_elapsed) / \
                (self.weapon_cooldown - self.attack_time)
            weapon_offset_from = WEAPON_DIRECTION_OFFSET_FROM[direction]
            weapon_offset_to = WEAPON_DIRECTION_OFFSET[direction]
            # smooth out the move using a transition function
            # shift by 0.5 to the weapon is moved away the farthest
            # in the middle of the transition
            # in_out_quad in_out_expo in_out_elastic in_out_back
            factor = AnimationTransition.in_out_elastic(1.0 - abs(factor - 0.5) * 2.0)
            offset = lerp_vectors(weapon_offset_from, weapon_offset_to, factor)
            self.selected_weapon.rect.center = vec(self.pos[0], self.pos[1]) + offset   # type: ignore[assignment]
            self.selected_weapon.image = self.selected_weapon.image_directions[direction].copy()
            self.selected_weapon.mask = self.selected_weapon.masks[direction]

    #############################################################################################################
    def debug(self, msgs: list[str]) -> None:
        if scene.SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (0, HEIGHT - 25 - i * 25))

    #############################################################################################################
    def pick_up(self, item: ItemSprite) -> bool:
        result: bool = False

        if item.model.type == ItemTypeEnum.money:
            self.model.money += item.model.value
            # self.items.append(item)
            result = True
        else:
            found = False
            for idx, owned_item in enumerate(self.items):
                if owned_item.name == item.name:
                    found = True
                    break

            if self.total_items_weight + item.model.weight <= self.model.max_carry_weight:
                if found:
                    self.total_items_weight += item.model.weight

                    # increase amount if already owned
                    self.items[idx].model.count += 1

                    result = True
                else:
                    # check if there are free slots
                    if len(self.items) < MAX_HOTBAR_ITEMS:
                        # add new item if not owned
                        self.total_items_weight += item.model.weight

                        self.items.append(item)

                        # if it's the first owned item, set it as selected
                        if self.selected_item_idx < 0:
                            self.selected_item_idx = 0

                        result = True
                    else:
                        print(
                            f"\n[red]ERROR:[/] {self.name} All '[num]{MAX_HOTBAR_ITEMS}[/num]'"
                            " items slots are taken!\n")
                        self.scene.add_notification(
                            f"All '[num]{MAX_HOTBAR_ITEMS}[/num]' items slots are taken :red_exclamation_anim:",
                            scene.NotificationTypeEnum.failure)
            else:
                print(
                    f"\n[red]ERROR:[/] {self.name} Max carry weight "
                    f"'[num]{self.model.max_carry_weight:4.2f}[/num]' exceeded!\n")
                self.scene.add_notification(
                    f"Max carry weight '[num]{
                        self.model.max_carry_weight:4.2f}[/num]' exceeded :red_exclamation_anim:",
                    scene.NotificationTypeEnum.failure)

        return result

    #############################################################################################################
    def can_buy(self) -> bool:
        if (
            not self.npc_met or not self.npc_met.items or self.npc_met.selected_item_idx < 0
        ):
            return False

        selected_item = self.npc_met.items[self.npc_met.selected_item_idx]

        if self.model.money < selected_item.model.value:
            self.scene.add_notification(
                f"You can't buy '[item]{
                    selected_item.model.name}[/item]' - not enough money :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        if self.model.max_carry_weight < self.total_items_weight + selected_item.model.weight:
            self.scene.add_notification(
                f"You can't buy '[item]{
                    selected_item.model.name}[/item]' - too heavy :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        found = False
        for owned_item in self.items:
            if owned_item.name == selected_item.name:
                found = True
                break

        if not found and len(self.items) == MAX_HOTBAR_ITEMS:
            self.scene.add_notification(
                f"You can't buy '[item]{
                    selected_item.model.name}[/item]' - no free items slots :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        return True

    #############################################################################################################
    def can_sell(self) -> bool:
        if (
            not self.items or self.selected_item_idx < 0 or self.selected_item_idx > len(
                self.items) - 1 or not self.npc_met
        ):
            return False

        selected_item = self.items[self.selected_item_idx]

        if self.npc_met.model.money < selected_item.model.value:
            self.scene.add_notification(
                f"Merchant can't buy '[item]{
                    selected_item.model.name}[/item]' - not enough money :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        if self.npc_met.model.max_carry_weight < self.npc_met.total_items_weight + selected_item.model.weight:
            self.scene.add_notification(
                f"Merchant can't buy '[item]{
                    selected_item.model.name}[/item]' - too heavy :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        found = False
        for owned_item in self.npc_met.items:
            if owned_item.name == selected_item.name:
                found = True
                break

        if not found and len(self.npc_met.items) == MAX_HOTBAR_ITEMS:
            self.scene.add_notification(
                f"Merchant can't buy '[item]{
                    selected_item.model.name}[/item]' - no free items slots :red_exclamation_anim:",
                scene.NotificationTypeEnum.failure)
            return False

        return True

    #############################################################################################################
    def drop_item(self, show: bool = True) -> ItemSprite | None:
        if (
            not self.items or self.selected_item_idx < 0 or self.selected_item_idx > len(self.items) - 1
        ):
            return None

        selected_item = self.items[self.selected_item_idx]
        self.total_items_weight -= selected_item.model.weight  # * selected_item.model.count

        if selected_item.model.count > 1:
            org_item = selected_item
            org_item.model.count -= 1

            # selected_item = copy.copy(org_item)
            selected_item = self.scene.create_item(org_item.name, int(self.pos[0]), int(self.pos[1]), show=show)
            # selected_item.rect = org_item.rect.copy()
            # selected_item.model = copy.copy(org_item.model)
            # selected_item.model.count = 1
        else:
            # are we dropping currently selected weapon
            if selected_item.model.type == ItemTypeEnum.weapon and self.selected_weapon and \
                    self.selected_weapon.name == selected_item.name:
                self.selected_weapon = None

            self.items.remove(selected_item)

            if show:
                self.scene.item_sprites.add(selected_item)
                selected_item.rect.center = self.pos  # type: ignore[assignment]

            if self.selected_item_idx >= len(self.items):
                self.selected_item_idx -= 1
        # item = self.items.pop(-1)

        return selected_item

#################################################################################################################
# MARK: Player


# @dataclass(slots=True, unsafe_hash=True)
# @dataclass(slots=True, frozen=True)
class Player(NPC):
    def __init__(
            self,
            game: game.Game,
            scene: scene.Scene,
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: tuple[int, int],
            name: str,
            emotes: dict[str, list[pygame.Surface]],
            model_name: str = "",
    ):
        self.name = name
        if not model_name:
            model_name = self.name

        super(Player, self).__init__(game, scene, shadow_group, label_group, pos, name, emotes, model_name=model_name)
        # give player some super powers
        self.speed_run  = int(self.speed_run * 1.7)
        self.speed_walk = int(self.speed_walk * 1.4)
        self.speed = self.speed_run
        self.health_bar_ui = self.create_health_bar_ui(label_group, pos, INVENTORY_ITEM_SCALE)
        # label_group.remove(self.health_bar)
    #############################################################################################################

    def __hash__(self) -> int:
        return hash(self.name)

    #############################################################################################################

    def create_health_bar_ui(
        self,
        label_group: pygame.sprite.Group,
        pos: tuple[int, int],
        scale: int = 1
    ) -> HealthBarUI:
        # self.wrong: bool = True
        return HealthBarUI(self.model, label_group, pos, scale)

    #############################################################################################################
    def movement(self) -> None:
        if self.is_stunned or self.is_attacking:
            return

        global INPUTS

        if INPUTS["open"]:
            if self.chest_in_range and self.chest_in_range.model.is_closed and not self.is_talking:
                chest = self.chest_in_range
                chest.open()
                self.scene.add_notification("Chest opened :red_exclamation_anim:", NotificationTypeEnum.success)
                for item_name in chest.model.items:
                    # print(f"[light_green] '{item_name}' item from chest")
                    chest_pos = vec(self.chest_in_range.rect.centerx, self.chest_in_range.rect.centery)
                    pos: vec = self.get_random_safe_pos(
                        chest_pos, range=1.5, check_allowed_zones=False, allow_start_pos=False)
                    rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
                    rect.center = pos  # type: ignore[assignment]
                    item = self.scene.create_item(item_name, rect.left, rect.top)
                    self.scene.items.append(item)
                    self.scene.group.add(item, layer=self.scene.sprites_layer - 1)
            INPUTS["open"] = False
        elif INPUTS["talk"]:
            if self.npc_met and (self.npc_met.has_dialog or self.npc_met.model.is_merchant) and not self.is_talking:
                if self.npc_met.has_dialog:
                    self.scene.ui.activate_dialog_panel(self.npc_met.dialogs or "")
                else:
                    self.scene.ui.activate_trade_panel()
                self.is_talking = True
                self.npc_met.is_talking = True
            INPUTS["talk"] = False

        # prevent player from moving and attacking while talking
        if self.is_talking:
            return

        if not self.target == vec(0, 0):
            self.follow_waypoints()

        # or not self.target == vec(0, 0):
        if INPUTS["left_click"]:
            target = vec(pygame.mouse.get_pos())
            mx, my = self.scene.map_view.get_center_offset()
            # convert screen position to world position
            x = target.x // self.scene.map_view._real_ratio_x - mx
            y = target.y // self.scene.map_view._real_ratio_y - my
            rect = pygame.Rect(x, y, 2, 2)
            fix_exit_target = False
            skip = False
            exit_sprites = list(self.scene.exit_sprites)
            if rect.collidelist(exit_sprites) > -1:
                fix_exit_target = True
                y += TILE_SIZE
            else:
                cell_x = int(x // TILE_SIZE)
                cell_y = int(y // TILE_SIZE)
                walk_cost = self.scene.path_finding_grid[cell_y][cell_x]
                if walk_cost > 0:
                    print("[yellow]INFO[/] destination unreachable")
                    self.scene.add_notification("destination unreachable :red_exclamation_anim:",
                                                NotificationTypeEnum.failure)
                    skip = True

            if not skip:
                self.target = vec(x, y + 8)
                self.find_path()

                if fix_exit_target:
                    exit_target = Point(int(x), int(y - TILE_SIZE))
                    waypoints_l = list(self.waypoints)
                    self.waypoints = tuple(waypoints_l + [exit_target])
                    self.waypoints_cnt = len(waypoints_l)

            INPUTS["left_click"] = False

            self.follow_waypoints()
            # target = vec(pygame.mouse.get_pos())
            # mx, my = self.scene.map_view.get_center_offset()
            # x = target.x // self.scene.map_view._real_ratio_x - mx
            # y = target.y // self.scene.map_view._real_ratio_x - my
            # self.target = vec(x // TILE_SIZE, y // TILE_SIZE)
            # INPUTS["left_click"] = False

        if INPUTS["right_click"]:
            self.target = vec(0, 0)
            self.waypoints_cnt = 0
            self.waypoints = ()
            INPUTS["right_click"] = False

        if INPUTS["attack"]:
            if not self.is_attacking and self.selected_weapon:

                self.is_attacking = True
                self.attack_time = self.game.time_elapsed
                self.scene.group.add(self.selected_weapon, layer=self.scene.sprites_layer - 1)
                weapon_cooldown = int(self.selected_weapon.model.cooldown_time * 1000.0) if self.selected_weapon else 0
                self.weapon_cooldown = self.game.time_elapsed + (weapon_cooldown + self.attack_cooldown) / 1000.0

                self.set_event_timer(
                    self,
                    NPCEventActionEnum.attacking,
                    self.attack_cooldown + weapon_cooldown,
                    1)
            INPUTS["attack"] = False

        if INPUTS["left"]:
            multiplier = INPUTS["left_value"] * JOY_MOVE_MULTIPLIER if self.game.is_joystick_in_use else 1.0
            self.acc.x = -self.force * multiplier
            self.target = vec(0, 0)
        elif INPUTS["right"]:
            multiplier = INPUTS["right_value"] * JOY_MOVE_MULTIPLIER if self.game.is_joystick_in_use else 1.0
            self.acc.x = self.force * multiplier
            self.target = vec(0, 0)
        else:
            if self.target == vec(0, 0):
                self.acc.x = 0

        if INPUTS["up"]:
            multiplier = INPUTS["up_value"] * JOY_MOVE_MULTIPLIER if self.game.is_joystick_in_use else 1.0
            # print(multiplier)
            self.acc.y = -self.force * multiplier
            self.target = vec(0, 0)
        elif INPUTS["down"]:
            multiplier = INPUTS["down_value"] * JOY_MOVE_MULTIPLIER if self.game.is_joystick_in_use else 1.0
            # print(multiplier)
            self.acc.y = self.force * multiplier
            self.target = vec(0, 0)
        else:
            if self.target == vec(0, 0):
                self.acc.y = 0

    #############################################################################################################
    def check_scene_exit(self) -> None:
        if self.scene.transition.exiting:
            return

        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                # if exit.to_map == "Maze":
                #     pass
                self.scene.new_scene = exit
                self.scene.transition.exiting = True
                break
                # self.scene.go_to_scene()

    #############################################################################################################
    def use_item(self) -> None:
        if (
            not self.items or self.selected_item_idx < 0 or self.selected_item_idx > len(self.items) - 1
        ):
            return None

        item = self.items[self.selected_item_idx]
        if item.model.type == ItemTypeEnum.consumable:
            self.model.health += item.model.health_impact
            self.model.health = max(0, min(self.model.health, self.model.max_health))
            item.model.count -= 1
            self.total_items_weight -= item.model.weight
            if item.model.count <= 0:
                self.items.remove(item)
                if self.selected_item_idx >= len(self.items):
                    self.selected_item_idx -= 1
        elif item.model.type == ItemTypeEnum.weapon:
            if self.can_switch_weapon and not self.is_attacking and not self.is_stunned:
                self.can_switch_weapon = False
                self.switch_cooldown = self.game.time_elapsed + (self.switch_duration_cooldown / 1000.0)
                self.set_event_timer(self, NPCEventActionEnum.switching_weapon, self.switch_duration_cooldown, 1)

                if self.selected_weapon:
                    if self.selected_weapon.name == item.name:
                        # self.scene.group.remove(self.selected_weapon)
                        self.selected_weapon = None
                    else:
                        # self.scene.group.remove(self.selected_weapon)
                        self.selected_weapon = item
                        # self.scene.group.add(self.selected_weapon)
                else:
                    self.selected_weapon = item
                    # self.scene.group.add(self.selected_weapon)
