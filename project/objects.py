import pygame
from settings import *

class Collider(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], size: list[int], name: str, to_map: str, entry_point: str, is_maze: bool, maze_cols: int, maze_rows: int, return_entry_point: str = ""):
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size))
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.name = name
        self.to_map = to_map
        self.entry_point = entry_point
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows
        self.return_entry_point = return_entry_point
        
class Shadow(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], size: list[int]):
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size)).convert_alpha()
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.image.fill((0,0,0,0))
        # self.image.set_colorkey("black")
        pygame.draw.ellipse(self.image, (0,0,0,255), self.rect)

class HealthBar(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int]):
        super().__init__(groups)
        self.image_full: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniProgress.png").convert_alpha()
        self.image_empty: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniUnder.png").convert_alpha()
        self.image = self.image_full.copy()
        self.rect: pygame.FRect = self.image.get_frect(midbottom = pos)
        
    def set_bar(self, percentage: float):
        self.image.blit(self.image_full, (0, 0))
        # tmp_img = self.image_empty.copy()
        # tmp_img.set_colorkey((0,0,0))
        percentage = min(1.0, percentage)
        percentage = max(0.0, percentage)
        width = int(self.rect.width * percentage)
        rect = pygame.Rect(width, 0, self.rect.width - width, self.rect.height)
        tmp_img = self.image_empty.subsurface(rect)
        # pygame.draw.rect(tmp_img, (0, 0, 0), rect)
        
        # self.image.blit(self.image_empty, rect)
        self.image.blit(tmp_img, (width, 0))
        
        
class Object(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], z: str ="blocks", surf=pygame.Surface((TILE_SIZE, TILE_SIZE))):
        super().__init__(groups)
        
        self.image = surf
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.hitbox: pygame.FRect = self.rect.copy().inflate(0,0)
        self.z = z
        
class Wall(Object):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], z: str ="blocks", surf=pygame.Surface((TILE_SIZE, TILE_SIZE))):
        super().__init__(groups, pos, z, surf)
        # decrease the size of rectangle for collisions aka. hitbox
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, -self.rect.height / 2)
        
