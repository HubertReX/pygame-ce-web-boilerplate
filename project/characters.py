import os
import random
import pygame
from pygame.math import Vector2 as vec
from maze_generator.maze_utils import a_star
from settings import *
import game
import scene
import npc_state
from objects import Shadow

##########################################################################################################################
#MARK: NPC

class NPC(pygame.sprite.Sprite):
    def __init__(
            self, 
            game: game.Game, 
            scene: scene.Scene, 
            groups: list[pygame.sprite.Group], 
            shadow_group: pygame.sprite.Group,
            pos: list[int], 
            name: str, 
            waypoints: tuple[Point] = ()
        ):
        super().__init__(groups)
        self.game = game
        self.scene = scene
        self.name = name # monochrome_ninja
        self.shadow = Shadow(shadow_group, (0,0), [TILE_SIZE - 2, 6])
        self.animations: dict[str, list[pygame.surface.Surface]] = {}
        self.animation_speed = ANIMATION_SPEED
        # self.import_image(f"assets/{self.name}/")
        self.import_sprite_sheet(CHARACTERS_DIR / self.name / "SpriteSheet.png")
        self.frame_index: float = 0.0
        # self.image = self.animations["idle"][int(self.frame_index)].convert_alpha()
        self.image = self.animations["idle_down"][int(self.frame_index)]
        # self.image.set_colorkey(COLORS["black"])
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
        self.target: vec | None = vec(0,0)
        
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
        
        # actual NPC state, mainly to determine type of animation and speed
        self.state: npc_state.NPC_State = npc_state.Idle()
        self.state.enter_time = self.scene.game.time_elapsed
        
    def get_tileset_coord(self, pos: vec | None = None) -> Point:
        """
        map position in world coordinates to tileset grid 
        """
        if not pos:
            pos = self.pos
            
        # shift up by 4 pixels since perceived location is different than actual Sprite position on screen
        return Point(int(pos.x // TILE_SIZE), int((pos.y - 4) // TILE_SIZE))
        
    def import_sprite_sheet(self, path: str):
        """ 
        Load sprite sheet and cut it into animation names and frames using SPRITE_SHEET_DEFINITION dict.
        If provided sheet is missing some of the animations from dict, a frame from upper left corner (0,0)
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
        
            
    def animate(self, state, fps: float, loop=True):
        self.frame_index += fps
        
        if self.frame_index >= len(self.animations[state]) - 1:
            if loop:
                self.frame_index = 0.0
            else:
                self.frame_index = len(self.animations[state]) - 1.0
                
        self.image = self.animations[state][int(self.frame_index)]
        
    def get_direction_360(self) -> str:
        angle = self.vel.angle_to(vec(0,1))
        angle = (angle + 360) % 360
        
        if 45 <= angle < 135: return "right"
        elif 135 <= angle < 225: return "up"
        elif 225 <= angle < 315: return "left"
        else: return "down"
        
    def get_direction_horizontal(self) -> str:
        angle = self.vel.angle_to(vec(0,1))
        angle = (angle + 360) % 360
        
        if angle < 180: return "right"
        else: return "left"
        
    def movement(self):
        if not self.target == vec(0,0) or self.waypoints_cnt == 0:
            if not self.name == "GreenNinja" and (self.waypoints_cnt == 0 or not self.target == self.scene.player.pos):
                self.target = self.scene.player.pos.copy()
                self.find_path()
                
            global INPUTS
            if INPUTS["left_click"] and self.name == "GreenNinja":
                target = vec(pygame.mouse.get_pos())
                mx, my = self.scene.map_layer.get_center_offset()
                x = target.x // self.scene.map_layer._real_ratio_x - mx
                y = target.y // self.scene.map_layer._real_ratio_x - my 
                self.target = vec(x, y)
                self.find_path()                        
                INPUTS["left_click"] = False
            
        if self.waypoints_cnt > 0:
            npc_pos = self.pos
            current_way_point_vec = vec(self.waypoints[self.current_waypoint_no])
            current_way_point_vec.y += 4
            # skip to next waypoint when within around 1 pixel
            if current_way_point_vec.distance_squared_to(npc_pos) <= 2.0:
                self.current_waypoint_no += 1
                # if following target and reached goal do not start over again
                if self.current_waypoint_no >= self.waypoints_cnt:
                    if not self.target == vec(0,0):
                        self.waypoints = ()
                        self.waypoints_cnt = 0
                        self.current_waypoint_no = 0
                        self.acc = vec(0,0)
                        self.vel = vec(0,0)
                        return
                    else:
                        self.current_waypoint_no = 0
                    current_way_point_vec = vec(self.waypoints[self.current_waypoint_no])
                    current_way_point_vec.y += 4
            direction = current_way_point_vec - npc_pos
            direction = direction.normalize() * self.force
            self.acc.x = direction.x
            self.acc.y = direction.y

    def find_path(self):
        start = (self.tileset_coord.y, self.tileset_coord.x)
        target = self.get_tileset_coord(self.target)
        goal = (target.y, target.x)
        path = a_star(start=start, goal=goal, grid=self.scene.path_finding_grid)
        if path:
            waypoints = []
            path_list = list(path)
            start_index = 0
            # if first waypoint is the same map grid, than skip it
            # hack to prevent NPC jitter (coming back to center of current grid, than to next, but then path is recalculated and goes back to current grid center)
            if len(path_list) >= 2:
                if path_list[0] == start:
                    start_index = 1
                        
            # when following Player, stop 1 step before
            for waypoint in path_list[start_index:-1]:
                y, x = waypoint
                p = Point(x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2)
                waypoints.append(p)
            self.waypoints = tuple(waypoints)
            self.waypoints_cnt = len(waypoints)
            self.current_waypoint_no = 0
        else:
            print(f"{self.name}: Path not found!")
            self.waypoints = ()
            self.waypoints_cnt = 0
            self.current_waypoint_no = 0
            self.acc = vec(0,0)
            self.vel = vec(0,0)

    def jump(self):
        self.is_jumping = True
        self.up_acc = self.up_force
        # self.up_vel = 50
        self.jumping_offset = 1
        
        
    def physics(self, dt: float):
        self.prev_pos = self.pos.copy()
        
        self.acc.x += self.vel.x * self.friction
        self.vel.x += self.acc.x * dt
        
        self.acc.y += self.vel.y * self.friction
        self.vel.y += self.acc.y * dt
        
        step_cost = abs(self.scene.path_finding_grid[self.tileset_coord.y][self.tileset_coord.x])
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
            self.jumping_offset = self.up_vel * dt #+ (self.up_vel / 2) * dt
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
        
        
    def change_state(self):
        new_state = self.state.enter_state(self)
        if new_state:
            new_state.enter_time = self.scene.game.time_elapsed
            self.state = new_state
        
                    
    def check_scene_exit(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.scene.NPC = [npc for npc in self.scene.NPC if not npc == self]
                self.shadow.kill()
                self.kill()
                # TODO NPC goes to another map


    def update(self, dt: float):
        self.state.update(dt, self)
        self.change_state()
        
        
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
        
        
    def move_back(self) -> None: # start_index = 0
        """
        If called after an update, the sprite can move back

        """
        # self.debug([f"{self.rect.topleft=}", f"{self.old_rect.topleft=}"])
        self.pos = self.prev_pos.copy()
        
        self.adjust_rect()

    def adjust_rect(self):
        self.tileset_coord = self.get_tileset_coord() 
        # display sprite n pixels above position so the shadow doesn't stick out from the bottom
        self.rect.midbottom = self.pos + vec(0,  -self.jumping_offset - 3)
        # 'hitbox' for collisions
        self.feet.midbottom = self.pos
        # shadow
        self.shadow.rect.midbottom = self.pos #+ vec(0, -1)
            
        
    def debug(self, msgs: list[str]):
        if SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (0, HEIGHT - 25 - i * 25))

##########################################################################################################################
#MARK: Player        
class Player(NPC):
    def __init__(
            self, 
            game: game.Game, 
            scene: scene.Scene, 
            groups: list[pygame.sprite.Group],
            shadow_group: pygame.sprite.Group,
            pos: list[int], 
            name: str
        ):
        super().__init__(game, scene, groups, shadow_group, pos, name)
        # give player some super powers
        self.speed_run  *= 1.5
        self.speed_walk *= 1.2
        self.speed = self.speed_walk
        
    def movement(self):
        global INPUTS
        if INPUTS["left_click"] or not self.target == vec(0,0):
            super().movement()
            # target = vec(pygame.mouse.get_pos())
            # mx, my = self.scene.map_layer.get_center_offset()
            # x = target.x // self.scene.map_layer._real_ratio_x - mx
            # y = target.y // self.scene.map_layer._real_ratio_x - my
            # self.target = vec(x // TILE_SIZE, y // TILE_SIZE)
            # INPUTS["left_click"] = False
        if INPUTS["right_click"]:
            self.target = vec(0,0)
            self.waypoints_cnt = 0
            self.waypoints = ()
            
        if INPUTS["left"]:
            self.acc.x = -self.force
            self.target = vec(0,0)
        elif INPUTS["right"]:
            self.acc.x = self.force
            self.target = vec(0,0)
        else:
            if self.target == vec(0,0):
                self.acc.x = 0
            
        if INPUTS["up"]:
            self.acc.y = -self.force
            self.target = vec(0,0)
        elif INPUTS["down"]:
            self.acc.y = self.force
            self.target = vec(0,0)
        else:
            if self.target == vec(0,0):
                self.acc.y = 0

                    
    def check_scene_exit(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                if exit.to_map == "Maze":
                    pass
                self.scene.new_scene = exit
                self.scene.transition.exiting = True
                # self.scene.go_to_scene()
                
