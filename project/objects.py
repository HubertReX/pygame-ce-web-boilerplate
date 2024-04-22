import pygame
from settings import *

class Collider(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], size: list[int], name: str, to_map: str, entry_point: str):
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size))
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.name = name
        self.to_map = to_map
        self.entry_point = entry_point
        
class Shadow(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], size: list[int]):
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size))
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.image.set_colorkey("black")
        pygame.draw.ellipse(self.image, (10,10,10), self.rect)
        
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
        
