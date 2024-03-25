import pygame
from settings import *

class Object(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], z: str ="blocks", surf=pygame.Surface((TILE_SIZE,TILE_SIZE))):
        super().__init__(groups)
        
        self.image = surf
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.hitbox: pygame.FRect = self.rect.copy().inflate(0,0)
        self.z = z
        
class Wall(Object):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], z: str ="blocks", surf=pygame.Surface((TILE_SIZE,TILE_SIZE))):
        super().__init__(groups, pos, z, surf)
        
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, -self.rect.height / 2)
        
    # def draw(self, surface):
    #     self.image.fill(COLORS["blue"])
    #     surface.blit(self.image, self.rect.topleft)
