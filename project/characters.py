import os
import random
import pygame
from pygame.math import Vector2 as vec
from settings import *
# from settings import CHARACTERS_DIR, HEIGHT, INPUTS, ANIMATION_SPEED, RESOURCES_DIR, SHOW_DEBUG_INFO, COLORS, SPRITE_SHEET_DEFINITION, TILE_SIZE
# from state import Scene, State
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
        self.image.set_colorkey(COLORS["black"])
        self.rect = self.image.get_frect(center = pos)
        self.old_rect = pygame.Rect(self.rect)
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 8)
        self.waypoints: tuple[Point] = waypoints
        self.waypoints_cnt: int = len(waypoints)
        # self.current_waypoint: Point | None = (self.way_points[0] if self.way_points_cnt > 0 else None)
        self.current_waypoint_no: int = 0
        self.speed_walk: int = 50
        self.speed_run: int = 70
        self.speed: int = random.choice([self.speed_walk, self.speed_run])
        self.force: int = 2000 # random.choice([self.force_walk, self.force_run]) # 350 => speed = 23 # 800 => speed = 53 + random.randint(-200, 200)
        self.acc = vec()
        self.vel = vec()
        self.friction: int = -12
        self.is_jumping = False
        self.state: npc_state.NPC_State = npc_state.Idle()
        
    def import_sprite_sheet(self, path: str):
        img = pygame.image.load(path).convert_alpha()
        
        for key, definition in SPRITE_SHEET_DEFINITION.items():
            self.animations[key] = []
            for coord in definition:
                x, y = coord
                # shadow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE+4))
                # shadow_surf.set_colorkey("black")
                
                # pygame.draw.ellipse(shadow_surf, (10,10,10), (1, TILE_SIZE-3, TILE_SIZE-2, 6))
                rec = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                img_part = img.subsurface(rec)
                # shadow_surf.blit(img_part, (0,0,TILE_SIZE,TILE_SIZE))
                # self.animations[key].append(shadow_surf)
                self.animations[key].append(img_part)
        
    def import_image(self, path: str):
        # old implementation used with separate img per frame (e.g. monochrome_ninja)
        self.animations = self.game.get_animations(path)
        animations_keys = list(self.animations.keys())
        for animation in animations_keys:
            full_path = os.path.join(path, animation)
            self.animations[animation] = self.game.get_images(full_path)
            if animation in ["idle", "run"]:
                self.animations[f"{animation}_right"] = [] # self.animations[animation]
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
                
        # self.image = self.animations[state][int(self.frame_index)].convert_alpha()
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
        if self.waypoints_cnt > 0:
            npc_pos = vec(self.feet.centerx, self.feet.bottom)
            current_way_point_vec = vec(self.waypoints[self.current_waypoint_no])
            # print(f"Distance to way point {self.current_way_point}: {current_way_point_vec.distance_squared_to(npc_pos):5.0f}")
            if current_way_point_vec.distance_squared_to(npc_pos) < 3.0 ** 2:
                self.current_waypoint_no += 1
                if self.current_waypoint_no >= self.waypoints_cnt:
                    self.current_waypoint_no = 0
                # print(f"New way point: {self.current_way_point}")
            direction = current_way_point_vec - npc_pos
            direction = direction.normalize() * self.force
            self.acc.x = direction.x
            self.acc.y = direction.y

    def physics(self, dt: float):
        self.old_rect.topleft = self.rect.topleft
        
        self.acc.x += self.vel.x * self.friction
        self.vel.x += self.acc.x * dt
        # if -0.01 < self.vel.x < 0.01:
        #     self.vel.x = 0.0
        
        self.acc.y += self.vel.y * self.friction
        self.vel.y += self.acc.y * dt
        # if -0.01 < self.vel.y < 0.01:
        #     self.vel.y = 0.0
        
        if self.vel.magnitude() >= self.speed:
            self.vel = self.vel.normalize() * self.speed
            
        self.rect.centerx += self.vel.x * dt + (self.vel.x / 2) * dt
        self.rect.centery += self.vel.y * dt + (self.vel.y / 2) * dt
        
        self.feet.midbottom = self.rect.midbottom
        self.shadow.rect.center = self.rect.midbottom
        if self.is_jumping:
            # self.shadow.rect.centerx = self.rect.centerx
            self.shadow.rect.centery = self.rect.bottom + (TILE_SIZE)
            self.feet.centery = self.rect.bottom + (TILE_SIZE)

    def change_state(self):
        new_state = self.state.enter_state(self)
        if new_state:
            self.state = new_state
        
    def update(self, dt: float):
        self.change_state()
        self.state.update(dt, self)
        
    def move_back(self, dt: float) -> None:
        """
        If called after an update, the sprite can move back

        """
        # self.debug([f"{self.rect.topleft=}", f"{self.old_rect.topleft=}"])
        self.rect.topleft = self.old_rect.topleft
        self.feet.midbottom = self.rect.midbottom
        self.shadow.rect.center = self.old_rect.midbottom
        if self.is_jumping:
            self.shadow.rect.centery = self.old_rect.bottom + (TILE_SIZE)
            self.feet.centery = self.old_rect.bottom + (TILE_SIZE)
            
        
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
        # self.friction: int = -10
        self.speed_run  *= 1.2
        self.speed_walk *= 1.2
        self.speed = self.speed_walk
        
    def movement(self):
        # return
        if INPUTS["left"]:
            self.acc.x = -self.force
        elif INPUTS["right"]:
            self.acc.x = self.force
        else:
            self.acc.x = 0
            
        if INPUTS["up"]:
            self.acc.y = -self.force
        elif INPUTS["down"]:
            self.acc.y = self.force
        else:
            self.acc.y = 0
                    
    def check_scene_exit(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.scene.new_scene = exit.to_map
                self.scene.entry_point = exit.entry_point
                self.scene.transition.exiting = True
                # self.scene.go_to_scene()
                
    def update(self, dt: float):
        self.check_scene_exit()
        super().update(dt)