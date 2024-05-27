from enum import StrEnum, auto
import os
import random
import pygame
from pygame.math import Vector2 as vec
from maze_generator.maze_utils import a_star, a_star_cached
from config_model.config import AttitudeEnum, Character
from settings import (
    ANIMATION_SPEED, CHARACTERS_DIR,
    HEIGHT, PUSHED_TIME, RECALCULATE_PATH_DISTANCE,
    SPRITE_SHEET_DEFINITION, STUNNED_COLOR, STUNNED_TIME, TILE_SIZE,
    Point, INPUTS
)
import game
import scene
import npc_state
from objects import HealthBar, Shadow
import splash_screen


########################################################################################################################
class NPCEventActionEnum(StrEnum):
    stunned  = auto()
    pushed   = auto()
    standard = auto()


###################################################################################################################
# MARK: NPC
class NPC(pygame.sprite.Sprite):
    def __init__(
            self,
            game: game.Game,
            scene: scene.Scene,
            groups: list[pygame.sprite.Group],
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: list[int],
            name: str,
            waypoints: tuple[Point] = ()
    ):

        super().__init__(groups)
        self.game = game
        self.scene = scene
        self.name = name
        self.model: Character = game.conf.characters[name]
        self.shadow = self.create_shadow(shadow_group)
        self.health_bar = self.create_health_bar(label_group, pos)
        # hide health bar at start (negative value makes it transparent)
        self.health_bar.set_bar(-1.0, self.game)

        self.animations: dict[str, list[pygame.surface.Surface]] = {}
        self.animation_speed = ANIMATION_SPEED
        self.import_sprite_sheet(CHARACTERS_DIR / self.model.sprite / "SpriteSheet.png")
        self.frame_index: float = 0.0
        self.image = self.animations["idle_down"][int(self.frame_index)]
        self.pos: vec = vec(pos[0], pos[1])
        self.prev_pos: vec = self.pos.copy()
        self.tileset_coord: Point = self.get_tileset_coord()
        self.rect = self.image.get_frect(midbottom = self.pos)
        # hit box size is half the TILE_SIZE, bottom, centered
        self.feet = pygame.Rect(0, 0, self.rect.width // 2, TILE_SIZE // 2)
        self.feet.midbottom = self.pos
        # individual steps to follow (mainly a center of a given tile, but pixel accurate)
        # provided by A* path finding
        self.waypoints: tuple[Point] = waypoints
        self.waypoints_cnt: int = len(waypoints)
        self.current_waypoint_no: int = 0
        # list of targets to follow
        self.target: vec = vec(0, 0)
        self.targets: list[vec] = []

        # basic planar (N,E, S, W) physics
        # speed in pixels per second
        self.speed_walk: int = 30
        self.speed_run: int = 40
        self.speed: int = random.choice([self.speed_walk, self.speed_run])

        # movement inertia
        self.force: int = 2000
        self.friction: int = -12
        self.acc = vec(0, 0)
        self.vel = vec(0, 0)

        # jump/fly physics
        self.up_force: int = 3200
        self.up_friction: int = -1
        self.up_acc = 0.0
        self.up_vel = 0.0

        self.jumping_offset = 0
        # flags set by key strokes - not real NPC states
        self.is_flying = False
        self.is_jumping = False
        self.is_stunned = False

        # general purpose custom event, action is defined by the payload passed to event
        self.custom_event_id  = pygame.event.custom_type()
        self.game.register_custom_event(self.custom_event_id, self.process_custom_event)

        # actual NPC state, mainly to determine type of animation and speed
        self.state: npc_state.NPC_State = npc_state.Idle()
        self.state.enter_time = self.scene.game.time_elapsed

    ###################################################################################################################
    def create_health_bar(self, label_group: pygame.sprite.Group, pos: list[int]):
        return HealthBar(self.model, label_group, pos)

    ###################################################################################################################
    def create_shadow(self, shadow_group: pygame.sprite.Group):
        return Shadow(shadow_group, (0, 0), [TILE_SIZE - 2, 6])

    ###################################################################################################################
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    ###################################################################################################################
    def get_tileset_coord(self, pos: vec | None = None) -> Point:
        """
        map position in world coordinates to tileset grid
        """
        if not pos:
            pos = self.pos

        # shift up by 4 pixels since perceived location is different than actual Sprite position on screen
        return Point(int(pos.x // TILE_SIZE), int((pos.y - 4) // TILE_SIZE))

    ###################################################################################################################
    def import_sprite_sheet(self, path: str):
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

            if len(animation) > 0:
                self.animations[key] = animation
            else:
                self.animations[key] = animation_def

            # if there is only one animation for each direction
            # that is when animation name doesn't include direction (e.g. 'idle')
            # than add reference in all directions (e.g. 'idle_up', 'idle_down',...)
            for direction in directions:
                if direction not in key:
                    self.animations[f"{key}_{direction}"] = self.animations[key]

    ###################################################################################################################
    def import_image(self, path: str):
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

    ###################################################################################################################
    # MARK: animate
    def animate(self, state, dt: float, loop=True):
        self.frame_index += dt

        if self.frame_index >= len(self.animations[state]) - 1:
            if loop:
                self.frame_index = 0.0
            else:
                self.frame_index = len(self.animations[state]) - 1.0

        self.image = self.animations[state][int(self.frame_index)].copy()

        if self.is_stunned:
            red_filter = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            red_filter.fill(STUNNED_COLOR)
            self.image.blit(red_filter, (0, 0))

    ###################################################################################################################
    def get_direction_360(self) -> str:
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

    ###################################################################################################################
    def get_direction_horizontal(self) -> str:
        angle = self.vel.angle_to(vec(0, 1))
        angle = (angle + 360) % 360

        if angle < 180:
            return "right"
        else:
            return "left"

    ###################################################################################################################
    # MARK: movement
    def movement(self):
        if self.is_stunned:
            return

        # if character has a set target (and needs to follow it) or there are no waypoints to follow any more
        if not self.target == vec(0, 0) or self.waypoints_cnt == 0:
            # if (no more waypoints or the player has moved) and (character is a monster chasing player)
            # not self.target == self.scene.player.pos)
            distance_player_moved = (self.target - self.scene.player.pos).magnitude_squared()

            # if (self.waypoints_cnt == 0 or not self.target == self.scene.player.pos) and \
            #     self.model.attitude == AttitudeEnum.enemy.value:
            if (self.waypoints_cnt == 0 or distance_player_moved > RECALCULATE_PATH_DISTANCE ** 2) \
                    and self.model.attitude == AttitudeEnum.enemy.value:
                self.target = self.scene.player.pos.copy()
                self.find_path()

        self.follow_waypoints()

    ###################################################################################################################
    def follow_waypoints(self):
        if self.waypoints_cnt > 0:
            npc_pos = self.pos
            current_way_point_vec = vec(self.waypoints[self.current_waypoint_no])
            current_way_point_vec.y += 4
            # skip to next waypoint when within around 1 pixel
            if current_way_point_vec.distance_squared_to(npc_pos) <= 2.0:
                self.current_waypoint_no += 1
                # if following target and reached goal do not start over again
                if self.current_waypoint_no >= self.waypoints_cnt:
                    if not self.target == vec(0, 0):
                        self.target = vec(0, 0)
                        self.waypoints = ()
                        self.waypoints_cnt = 0
                        self.current_waypoint_no = 0
                        self.acc = vec(0, 0)
                        # self.vel = vec(0, 0)
                        return
                    else:
                        self.current_waypoint_no = 0
                    current_way_point_vec = vec(self.waypoints[self.current_waypoint_no])
                    current_way_point_vec.y += 4
            direction = current_way_point_vec - npc_pos
            direction = direction.normalize() * self.force
            self.acc.x = direction.x
            self.acc.y = direction.y

    ###################################################################################################################
    def find_path(self):
        start = (self.tileset_coord.y, self.tileset_coord.x)
        target = self.get_tileset_coord(self.target)
        goal = (target.y, target.x)
        # fps = f"FPS:\t{self.game.fps: 6.1f}\t3s:\t{self.game.avg_fps_3s: 6.1f}
        # \t10s:\t{self.game.avg_fps_10s: 6.1f}\ttime:\t{self.game.time_elapsed:4.1f}"
        path = a_star_cached(start=start, goal=goal, grid=self.scene.path_finding_grid, fps="")
        if path:
            waypoints = []
            path_list = list(path)
            start_index = 0
            # if first waypoint is the same map grid, than skip it
            # hack to prevent NPC jitter (coming back to center of current grid, than to next,
            # but then path is recalculated and goes back to current grid center)
            if len(path_list) >= 2:
                if path_list[0] == start:
                    start_index = 1

            # when following Player, stop 1 step before
            # for waypoint in path_list[start_index:-1]:
            for waypoint in path_list[start_index:]:
                y, x = waypoint
                p = Point(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
                waypoints.append(p)
            self.waypoints = tuple(waypoints)
            self.waypoints_cnt = len(waypoints)
            self.current_waypoint_no = 0
            # self.acc = vec(0, 0)
            # self.vel = vec(0, 0)
        else:
            print(f"{self.name}: Path not found!")
            self.waypoints = ()
            self.waypoints_cnt = 0
            self.current_waypoint_no = 0
            self.acc = vec(0, 0)
            self.vel = vec(0, 0)

    ###################################################################################################################
    def jump(self):
        self.is_jumping = True
        self.up_acc = self.up_force
        # self.up_vel = 50
        self.jumping_offset = 1

    ###################################################################################################################
    # MARK: physics
    def physics(self, dt: float):
        if self.is_stunned:
            return

        self.prev_pos = self.pos.copy()

        self.acc.x += self.vel.x * self.friction
        self.vel.x += self.acc.x * dt

        self.acc.y += self.vel.y * self.friction
        self.vel.y += self.acc.y * dt

        if self.tileset_coord.y < len(self.scene.path_finding_grid) and \
                self.tileset_coord.x < len(self.scene.path_finding_grid[0]):
            step_cost = abs(self.scene.path_finding_grid[self.tileset_coord.y][self.tileset_coord.x])
        else:
            step_cost = 1
        speed = (self.speed * (100 / step_cost))

        if self.vel.magnitude() >= speed:
            self.vel = self.vel.normalize() * speed

        if self.is_flying:

            if self.scene.game.time_elapsed % 0.25 < 0.125:
                oscillation = 1
            else:
                oscillation = 0
            self.jumping_offset = TILE_SIZE + oscillation
        else:
            if not self.is_jumping:
                self.jumping_offset = 0.0

        if self.is_jumping:
            self.up_acc += self.up_vel * self.up_friction
            self.up_vel += self.up_acc * dt
            # + (self.up_vel / 2) * dt
            self.jumping_offset = self.up_vel * dt
            if int(self.jumping_offset) <= 0:
                self.is_jumping = False
                self.up_acc = 0.0
                self.up_vel = 0.0
                self.jumping_offset = 0

                # TODO not a good place to do it
                self.scene.group.change_layer(self, self.scene.sprites_layer)

        self.pos.x += self.vel.x * dt + (self.vel.x / 2) * dt
        self.pos.y += self.vel.y * dt + (self.vel.y / 2) * dt

        self.adjust_rect()

    ###################################################################################################################
    def change_state(self):
        new_state = self.state.enter_state(self)
        if new_state:
            new_state.enter_time = self.scene.game.time_elapsed
            self.state = new_state

    ###################################################################################################################
    def check_scene_exit(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.die()
                # TODO NPC goes to another map

    ###################################################################################################################
    def die(self):
        self.scene.NPC = [npc for npc in self.scene.NPC if not npc == self]
        self.shadow.kill()
        self.health_bar.kill()
        if self.model.health <= 0:
            self.scene.exit_state()
            scene.Scene(self.game, "Village", "start").enter_state()
            splash_screen.SplashScreen(self.game, "GAME OVER").enter_state()
        self.kill()

    ###################################################################################################################
    def update(self, dt: float):
        self.state.update(dt, self)
        self.change_state()

    ###################################################################################################################
    def slide(self, colliders) -> None:
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

    ###################################################################################################################
    # MARK: process_custom_event
    def process_custom_event(self, **kwargs):
        # print(self.model.name, kwargs)

        if kwargs.get("action", "") == NPCEventActionEnum.pushed.value:
            # pushed state is invalidated
            # show health bar
            self.health_bar.set_bar(-1.0, self.game)
        elif kwargs.get("action", "") ==  NPCEventActionEnum.stunned.value:
            # stunned state is invalidated
            # show health bar
            self.health_bar.set_bar(-1.0, self.game)
            self.is_stunned = False
        else:
            print("unknown action", self.model.name, kwargs)

    ###################################################################################################################
    # MARK: encounter
    def encounter(self, oponent: "NPC"):
        if oponent.model.attitude == AttitudeEnum.enemy.value:
            # deal damage
            self.model.health -= oponent.model.damage
            oponent.model.health -= self.model.damage

            self.model.health = max(0, self.model.health)
            oponent.model.health = max(0, oponent.model.health)

            # print(f"{self.name}: {self.model.health} opponent {oponent.name} {oponent.model.health}")
            if self.model.health == 0:
                self.die()

            if oponent.model.health == 0:
                oponent.die()

            self.is_stunned = True
            self.set_event_timer(self, NPCEventActionEnum.stunned, STUNNED_TIME, 1)

            oponent.is_stunned = True
            self.set_event_timer(oponent, NPCEventActionEnum.stunned, STUNNED_TIME, 1)

            # show health bar (for STUNNED_TIME ms)
            self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.health_bar.set_bar(oponent.model.health / oponent.model.max_health, self.game)

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
            oponent.adjust_rect()

            self.set_event_timer(self,    NPCEventActionEnum.pushed, PUSHED_TIME, 1)
            self.set_event_timer(oponent, NPCEventActionEnum.pushed, PUSHED_TIME, 1)

            # show health bar (for PUSHED_TIME ms)
            self.health_bar.set_bar(self.model.health / self.model.max_health, self.game)
            oponent.health_bar.set_bar(oponent.model.health / oponent.model.max_health, self.game)

    ###################################################################################################################
    def set_event_timer(self, npc: "NPC", action: NPCEventActionEnum, interval: int, repeat: int) -> None:
        event = pygame.event.Event(npc.custom_event_id, action=action.value)
        pygame.time.set_timer(event, interval, repeat)

    ###################################################################################################################
    def move_back(self) -> None:
        """
        If called after an update, the sprite can move back

        """
        # self.debug([f"{self.rect.topleft=}", f"{self.old_rect.topleft=}"])
        self.pos = self.prev_pos.copy()

        self.adjust_rect()

    ###################################################################################################################
    def adjust_rect(self):
        self.tileset_coord = self.get_tileset_coord()
        # display sprite n pixels above position so the shadow doesn't stick out from the bottom
        self.rect.midbottom = self.pos + vec(0,  -self.jumping_offset - 3)
        # 'hitbox' for collisions
        self.feet.midbottom = self.pos
        # shadow
        # + vec(0, -1)
        self.shadow.rect.midbottom = self.pos
        # + vec(0, -TILE_SIZE - 4)
        self.health_bar.rect.midtop = self.pos

    ###################################################################################################################
    def debug(self, msgs: list[str]):
        if scene.SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (0, HEIGHT - 25 - i * 25))


#######################################################################################################################
# MARK: Player
class Player(NPC):
    def __init__(
            self,
            game: game.Game,
            scene: scene.Scene,
            groups: list[pygame.sprite.Group],
            shadow_group: pygame.sprite.Group,
            label_group: pygame.sprite.Group,
            pos: list[int],
            name: str
    ):
        super().__init__(game, scene, groups, shadow_group, label_group, pos, name)
        # give player some super powers
        self.speed_run  *= 1.5
        self.speed_walk *= 1.2
        self.speed = self.speed_run

    ###################################################################################################################
    def movement(self):
        global INPUTS

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
            exit_sprites = list(self.scene.exit_sprites)
            if rect.collidelist(exit_sprites) > -1:
                fix_exit_target = True
                y += TILE_SIZE
            self.target = vec(x, y + 8)
            self.find_path()
            if fix_exit_target:
                self.waypoints = tuple(list(self.waypoints) + [Point(x, y - TILE_SIZE)])
                self.waypoints_cnt = len(self.waypoints)

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

        if INPUTS["left"]:
            self.acc.x = -self.force
            self.target = vec(0, 0)
        elif INPUTS["right"]:
            self.acc.x = self.force
            self.target = vec(0, 0)
        else:
            if self.target == vec(0, 0):
                self.acc.x = 0

        if INPUTS["up"]:
            self.acc.y = -self.force
            self.target = vec(0, 0)
        elif INPUTS["down"]:
            self.acc.y = self.force
            self.target = vec(0, 0)
        else:
            if self.target == vec(0, 0):
                self.acc.y = 0

    ###################################################################################################################
    def check_scene_exit(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                # if exit.to_map == "Maze":
                #     pass
                self.scene.new_scene = exit
                self.scene.transition.exiting = True
                # self.scene.go_to_scene()
