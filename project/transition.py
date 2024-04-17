import pygame
from settings import *

class Transition():
    
    def __init__(self, scene) -> None:
        self.fade_surf: pygame.Surface = pygame.Surface((WIDTH, HEIGHT))
        self.scene = scene
        self.exiting: bool = False
        self.fade_out_speed: int = 800
        self.fade_in_speed: int = 200
        self.alpha: int = 255
        
    def update(self, dt: float):
        if self.exiting:
            self.alpha = min(255, int(self.alpha + self.fade_out_speed * dt))
            if self.alpha == 255:
                self.scene.go_to_scene()
        else:
            self.alpha = max(0, self.alpha - int(self.fade_in_speed * dt))
            
    def draw(self, screen: pygame.Surface):
        self.fade_surf.fill(COLORS["black"])
        self.fade_surf.set_alpha(self.alpha)
        screen.blit(self.fade_surf, (0,0))