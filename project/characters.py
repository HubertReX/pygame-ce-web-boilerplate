import os
from pathlib import Path
import pygame
from pygame.math import Vector2 as vec
from settings import CHARACTERS_DIR, HEIGHT, INPUTS, ANIMATION_SPEED, RESOURCES_DIR, SHOW_DEBUG_INFO, COLORS, SPRITE_SHEET_DEFINITION, TILE_SIZE
# from state import Scene, State
import game
import state

class NPC_State():
    def enter_state(self, character: "NPC"):
        raise NotImplemented(f"'enter_state' is not implemented. NPC_State should be used only as abstract class")
    
    def update(self, dt: float, character: "NPC"):
        raise NotImplemented(f"'update' is not implemented. NPC_State should be used only as abstract class")

class Idle(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.vel.magnitude() > 1:
            return Run()

    def update(self, dt: float, character: "NPC"):
        # character.animate(f"idle_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"idle_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class Run(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.vel.magnitude() < 1:
            return Idle()
    
    def update(self, dt: float, character: "NPC"):
        # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class NPC(pygame.sprite.Sprite):
    def __init__(self, game: game.Game, scene: state.Scene, groups: list[pygame.sprite.Group], pos: list[int], name: str):
        super().__init__(groups)
        
        self.game = game
        self.scene = scene
        self.name = name # monochrome_ninja
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
        self.speed: int = 160
        self.force: int = 2000
        self.acc = vec()
        self.vel = vec()
        self.friction: int = -15
        self.state: NPC_State = Idle()
        
    def import_sprite_sheet(self, path: str):
        img = pygame.image.load(path).convert_alpha()
        
        for key, definition in SPRITE_SHEET_DEFINITION.items():
            self.animations[key] = []
            for coord in definition:
                x, y = coord
                rec = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.animations[key].append(img.subsurface(rec))
        
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
        return

    def physics(self, dt: float):
        self.old_rect.topleft = self.rect.topleft
        
        self.acc.x += self.vel.x * self.friction
        self.vel.x += self.acc.x * dt
        # if -0.01 < self.vel.x < 0.01:
        #     self.vel.x = 0.0
        self.rect.centerx += self.vel.x * dt #+ (self.vel.x / 2) * dt
        
        self.acc.y += self.vel.y * self.friction
        self.vel.y += self.acc.y * dt
        # if -0.01 < self.vel.y < 0.01:
        #     self.vel.y = 0.0
        self.rect.centery += self.vel.y * dt #+ (self.vel.y / 2) * dt
        
        self.feet.midbottom = self.rect.midbottom
        
        if self.vel.magnitude() >= self.speed:
            self.vel = self.vel.normalize() * self.speed

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
        
    def debug(self, msgs: list[str]):
        if SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (0, HEIGHT - 25 - i * 25))
        
class Player(NPC):
    def __init__(self, game: game.Game, scene: state.Scene, groups: list[pygame.sprite.Group], pos: list[int], name: str):
        super().__init__(game, scene, groups, pos, name)
        
    def movement(self):
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
                    
    def exit_scene(self):
        for exit in self.scene.exit_sprites:
            if self.feet.colliderect(exit.rect):
                self.scene.new_scene = exit.to_map
                self.scene.entry_point = exit.entry_point
                self.scene.transition.exiting = True
                # self.scene.go_to_scene()
                
    def update(self, dt: float):
        self.exit_scene()
        super().update(dt)