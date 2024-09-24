import copy
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
    SPRITE_SHEET_DEFINITION,
    STUNNED_COLOR,
    STUNNED_TIME,
    TILE_SIZE,
    WEAPON_DIRECTION_OFFSET,
    WEAPON_DIRECTION_OFFSET_FROM,
    Point,
    lerp_vectors,
    vector_to_tuple,
)

if IS_WEB:
    from config_model.config import AttitudeEnum, Character, ItemTypeEnum
else:
    from config_model.config_pydantic import AttitudeEnum, Character, ItemTypeEnum  # type: ignore[assignment]

import game
import npc_state
import scene
import splash_screen
from objects import ChestSprite, EmoteSprite, HealthBar, HealthBarUI, ItemSprite, NotificationTypeEnum, Shadow
from animation.transitions import AnimationTransition

#################################################################################################################


class NPCEventActionEnum(Enum):
    stunned: int  = auto()
    pushed: int   = auto()
    standard: int = auto()
    attacking: int = auto()
    switching_weapon: int = auto()


#################################################################################################################
# MARK: NPC
# @dataclass(slots=True)
class NPC(pygame.sprite.Sprite):
    def __init__(
            self,
            game: game.Game,
            scene: scene.Scene,
            groups: pygame.sprite.Group,
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: tuple[int, int],
            name: str,
            emotes: dict[str, list[pygame.Surface]],
            waypoints: tuple[Point, ...] = (),
    ):

        self.name = name
        super(NPC, self).__init__(groups)
        self.game = game
        self.scene = scene
        self.model: Character = game.conf.characters[name]
        self.dialogs: str | None = None
        self.has_dialog: bool = False

        self.load_dialogs()

        self.shadow_group = shadow_group
        self.label_group = label_group
        self.pos: vec = vec(pos[0], pos[1])
        self.prev_pos: vec = self.pos.copy()

        self.shadow = self.create_shadow()
        self.health_bar = self.create_health_bar()
        # self.weapon_group = groups[-1]
        # hide health bar at start (negative value makes it transparent)
        self.hide_health_bar()
        self.items: list[ItemSprite] = []
        self.selected_weapon: ItemSprite | None = None
        self.selected_item_idx: int = -1
        self.total_items_weight: float = 0.0
        self.animations: dict[str, list[pygame.surface.Surface]] = {}
        self.masks: dict[str, list[pygame.mask.Mask]] = {}
        self.animation_speed = ANIMATION_SPEED
        self.import_sprite_sheet(str(CHARACTERS_DIR / self.model.sprite / "SpriteSheet.png"))
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

        # basic planar (N,E, S, W) physics
        # speed in pixels per second
        self.speed_walk: int = self.model.speed_walk
        self.speed_run: int = self.model.speed_run
        self.speed: int = random.choice([self.speed_walk, self.speed_run])
        if self.model.attitude == AttitudeEnum.enemy:
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
        self.is_flying = False
        self.is_jumping = False
        self.is_stunned = False
        self.is_talking = False

        # general purpose custom event, action is defined by the payload passed to event
        self.custom_event_id: int  = pygame.event.custom_type()
        self.game.register_custom_event(self.custom_event_id, self.process_custom_event)

        # actual NPC state, mainly to determine type of animation and speed
        self.state: npc_state.NPC_State = npc_state.Idle()
        self.state.enter_time = self.scene.game.time_elapsed

    #############################################################################################################

    def __hash__(self) -> int:
        return hash(self.name)

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
        return HealthBar(self.model, self.label_group, vector_to_tuple(self.pos))

    #############################################################################################################
    def create_shadow(self) -> Shadow:
        return Shadow(self.shadow_group, (0, 0), (TILE_SIZE - 2, 6))

    #############################################################################################################
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    #############################################################################################################
    def get_tileset_coord(self, pos: vec | None = None) -> Point:
        """
        map position in world coordinates to tileset grid
        """
        if not pos:
            pos = self.pos

        # shift up by 4 pixels since perceived location is different than actual Sprite position on screen
        return Point(int(pos.x // TILE_SIZE), int((pos.y - 4) // TILE_SIZE))

    #############################################################################################################
    def import_sprite_sheet(self, path: str) -> None:
        """
        Load sprite sheet and cut it into animation names and frames using SPRITE_SHEET_DEFINITION dict.
        If provided sheet is missing some of the animations from dict, a frame from upper left corner (0, 0)
        will be used.
        If directional variants are missing (e.g.: only idle animation, but no idle left, idle right...)
        the general animation will be copied.
        """
        img = pygame.image.load(path).convert_alpha()
        img_rect = img.get_rect()
        # use first tile (from upper left corner) as default 1 frame animation
        rec_def = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        img_def = img.subsurface(rec_def)
        animation_def = [img_def]
        directions = ["up", "down", "left", "right"]

        for key, definition in SPRITE_SHEET_DEFINITION.items():
            animation = []
            for coord in definition:
                x, y = coord
                rec = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if rec.colliderect(img_rect):
                    img_part = img.subsurface(rec)
                    animation.append(img_part)
                else:
                    continue
                    # print(f"ERROR! {self.name}: coordinate {x}x{y} not inside sprite sheet for {key} animation")

            self.animations[key] = animation or animation_def
            # if there is only one animation for each direction
            # that is when animation name doesn't include direction (e.g. 'idle')
            # than add reference in all directions (e.g. 'idle_up', 'idle_down',...)
            for direction in directions:
                if direction not in key:
                    self.animations[f"{key}_{direction}"] = self.animations[key]

    #############################################################################################################

    def import_image(self, path: str) -> None:
        """
        old implementation used with separate img per frame (e.g. monochrome_ninja)
        """
        self.animations = self.game.get_animations(path)
        animations_keys = list(self.animations.keys())
        for animation in animations_keys:
            full_path = os.path.join(path, animation)
            self.animations[animation] = self.game.get_images(full_path)
            if animation in ["idle", "run"]:
                self.animations[f"{animation}_right"] = []
                self.animations[f"{animation}_left"] = []
                for frame in self.animations[animation]:
                    converted = frame
                    # converted = frame.convert_alpha()
                    # converted.set_colorkey(COLORS["yellow"])
                    self.animations[f"{animation}_right"].append(converted)
                    self.animations[f"{animation}_left"].append(pygame.transform.flip(converted, True, False))

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
            angle = direction.angle_to(vec(0, 1))
        else:
            angle = self.vel.angle_to(vec(0, 1))
        angle = (angle + 360) % 360

        if 45 <= angle < 135:
            return "right"
        elif 135 <= angle < 225:
            return "up"
        elif 225 <= angle < 315:
            return "left"
        else:
            return "down"

    #############################################################################################################
    def get_direction_horizontal(self) -> str:
        angle = self.vel.angle_to(vec(0, 1))
        angle = (angle + 360) % 360

        return "right" if angle < 180 else "left"

    #############################################################################################################
    # MARK: movement
    def movement(self) -> None:
        if self.is_stunned or self.is_talking:
            return

        distance_from_player = (self.pos - self.scene.player.pos).magnitude_squared()
        # activate monsters in maze when player is near
        # no designated waypoints, distance from player in range, is enemy
        if self.waypoints_cnt == 0 and distance_from_player < MONSTER_WAKE_DISTANCE**2 and \
                self.model.attitude == AttitudeEnum.enemy:
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

        self.follow_waypoints()

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
            print(f"Path not found for npc '{self.name}'!")
            self.scene.add_notification(
                f"Path not found for npc '[char]{self.name}[/char]'", NotificationTypeEnum.debug)
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
            self.vel = self.vel.normalize() * speed

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
    def check_scene_exit(self) -> None:
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.die(drop_items=False)
                # TODO NPC goes to another map

    def get_random_pos(self, x_tiles: int = 1, y_tiles: int = 1) -> vec:
        return vec(random.randint(-x_tiles * TILE_SIZE * SCALE, x_tiles * TILE_SIZE * SCALE),
                   random.randint(-y_tiles * TILE_SIZE * SCALE, y_tiles * TILE_SIZE * SCALE))

    #############################################################################################################
    def die(self, drop_items: bool = True) -> None:
        self.scene.NPC = [npc for npc in self.scene.NPC if npc != self]
        self.shadow.kill()
        self.health_bar.kill()
        self.emote.kill()
        # drop items and money on the ground
        if self.name != "Player" and drop_items:
            for item in self.items:
                self.selected_item_idx = len(self.items) - 1
                if self.drop_item():
                    item.rect.center = self.pos + self.get_random_pos()  # type: ignore[assignment]
                    self.scene.item_sprites.add(item)
                    self.scene.group.add(item, layer=self.scene.sprites_layer - 1)
            if self.model.money >  0:
                pos: vec = self.pos + self.get_random_pos()  # type: ignore[assignment]
                item = self.scene.create_item("golden_coin", int(pos[0]), int(pos[1]))
                item.model.value = self.model.money
                self.scene.item_sprites.add(item)
                self.scene.group.add(item, layer=self.scene.sprites_layer - 1)
        if self.name == "Player" and self.model.health <= 0:
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
            self.hide_health_bar()
        elif action ==  NPCEventActionEnum.stunned:
            # stunned state is invalidated
            # show health bar
            self.hide_health_bar()
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
    def hide_health_bar(self) -> None:
        self.health_bar.set_bar(-1.0, self.game)

    #############################################################################################################
    def show_health_bar(self) -> None:
        self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)

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

            oponent.is_stunned = True
            oponent.set_event_timer(oponent, NPCEventActionEnum.stunned, STUNNED_TIME, 1)
            oponent.emote.set_temporary_emote("fight_anim", 4.0)

            # show health bar (for STUNNED_TIME ms)
            # self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.show_health_bar()

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
            oponent.show_health_bar()
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
            oponent.show_health_bar()

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
        else:
            self.emote.set_emote(emote)

    #############################################################################################################
    def reset(self) -> None:
        self.shadow = self.create_shadow()
        self.emote = self.create_emote()
        self.health_bar = self.create_health_bar()
        self.is_attacking = False
        self.is_flying = False
        self.is_jumping = False
        self.is_stunned = False
        self.is_talking = False
        self.items = []
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
            self.selected_weapon.image = self.selected_weapon.image_directions[direction]
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
            if len(self.items) < MAX_HOTBAR_ITEMS:
                item_total_weight = item.model.weight  # * item.model.count
                if self.total_items_weight + item_total_weight <= self.model.max_carry_weight:
                    self.total_items_weight += item_total_weight
                    found = False
                    # increase amount if already owned
                    for idx, owned_item in enumerate(self.items):
                        if owned_item.name == item.name:
                            self.items[idx].model.count += 1
                            found = True
                            break

                    # add new item if not owned
                    if not found:
                        self.items.append(item)

                    # if it's the first owned item, set it as selected
                    if self.selected_item_idx < 0:
                        self.selected_item_idx = 0
                    result = True
                else:
                    print(
                        f"\n[red]ERROR:[/] {self.name} Max carry weight "
                        f"'[num]{self.model.max_carry_weight:4.2f}[/num]' exceeded!\n")
                    self.scene.add_notification(
                        f"Max carry weight '[num]{self.model.max_carry_weight:4.2f}[/num]' exceeded :red_exclamation:",
                        scene.NotificationTypeEnum.failure)

            else:
                print(f"\n[red]ERROR:[/] {self.name} All '[num]{MAX_HOTBAR_ITEMS}[/num]' items slots are taken!\n")
                self.scene.add_notification(
                    f"All '[num]{MAX_HOTBAR_ITEMS}[/num]' items slots are taken :red_exclamation:",
                    scene.NotificationTypeEnum.failure)
        # print(f"Picked up {item.name}({item.model.type.value})")

        return result

    #############################################################################################################
    def drop_item(self) -> ItemSprite | None:
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
            selected_item = self.scene.create_item(org_item.name, int(self.pos[0]), int(self.pos[1]))
            # selected_item.rect = org_item.rect.copy()
            # selected_item.model = copy.copy(org_item.model)
            # selected_item.model.count = 1
        else:
            # are we dropping currently selected weapon
            if selected_item.model.type == ItemTypeEnum.weapon and self.selected_weapon and \
                    self.selected_weapon.name == selected_item.name:
                self.selected_weapon = None

            self.items.remove(selected_item)
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
            groups: pygame.sprite.Group,
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: tuple[int, int],
            name: str,
            emotes: dict[str, list[pygame.Surface]]
    ):
        self.name = name
        super(Player, self).__init__(game, scene, groups, shadow_group, label_group, pos, name, emotes)
        # give player some super powers
        self.speed_run  = int(self.speed_run * 1.7)
        self.speed_walk = int(self.speed_walk * 1.4)
        self.speed = self.speed_run
        self.health_bar_ui = self.create_health_bar_ui(label_group, pos, 4)
        label_group.remove(self.health_bar)
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
                self.scene.add_notification("Chest opened :red_exclamation:", NotificationTypeEnum.success)
                for item_name in chest.model.items:
                    # print(f"[light_green] '{item_name}' item from chest")
                    pos: vec = self.pos + self.get_random_pos()  # type: ignore[assignment]
                    item = self.scene.create_item(item_name, int(pos[0]), int(pos[1]))
                    self.scene.items.append(item)
                    self.scene.group.add(item, layer=self.scene.sprites_layer - 1)
            INPUTS["open"] = False
        elif INPUTS["talk"]:
            if self.npc_met and self.npc_met.has_dialog and not self.is_talking:
                self.scene.ui.activate_dialog_panel(self.npc_met.dialogs or "")
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
                    self.scene.add_notification("destination unreachable :red_exclamation:",
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
