from __future__ import annotations

from typing import TYPE_CHECKING

import pygame
from settings import COLORS, HEIGHT, WIDTH

if TYPE_CHECKING:
    from scene import Scene

#################################################################################################################


class Transition():

    def __init__(self, scene: Scene) -> None:
        self.fade_surf: pygame.Surface = pygame.Surface((WIDTH, HEIGHT))
        self.scene = scene
        self.exiting: bool = False
        self.fade_out_speed: int = 800
        self.fade_in_speed: int = 200
        self.alpha: int = 255
        self.radius: int = 0

    #############################################################################################################
    def update(self, dt: float) -> None:
        if self.exiting:
            self.alpha = min(255, int(self.alpha + self.fade_out_speed * dt))
            if self.alpha == 255:
                # self.scene.go_to_scene()
                self.scene.go_to_map()
        else:
            self.alpha = max(0, self.alpha - int(self.fade_in_speed * dt))
        # self.radius = (WIDTH//2) -  (WIDTH//2) * (self.alpha/255)
        self.radius = int((WIDTH * 2.7) -  (WIDTH * 2.7) * (self.alpha / 255))

    #############################################################################################################
    def draw(self, screen: pygame.Surface) -> None:
        # if alpha is at either of both value limits, do not show
        if self.alpha not in (0, 255):
            self.fade_surf.fill(COLORS["black"])
            self.fade_surf.set_alpha(self.alpha)
            screen.blit(self.fade_surf, (0, 0))
            # pygame.draw.circle(screen, (10,10,10), (WIDTH//2, HEIGHT//2), self.radius)


#################################################################################################################
class TransitionCircle(Transition):

    def draw(self, screen: pygame.Surface) -> None:
        # if alpha is at either of both value limits, do not show
        if self.alpha not in (0, 255):
            self.fade_surf.fill((1, 1, 1))
            # pos = self.scene.player.pos
            # offset_x, offset_y = self.scene.map_view.get_center_offset()
            # zoom = self.scene.map_view.zoom
            pos = self.scene.map_view.translate_point(self.scene.player.pos)  # type: ignore[has-type]
            # pygame.draw.circle(self.fade_surf, (0,0,0), (WIDTH//2, HEIGHT//2), self.radius)
            pygame.draw.circle(self.fade_surf, (0, 0, 0), pos, self.radius)
            # self.fade_surf.set_alpha(self.alpha)
            self.fade_surf.set_colorkey((0, 0, 0))
            screen.blit(self.fade_surf, (0, 0))
            # pygame.draw.circle(screen, (10,10,10), (WIDTH//2, HEIGHT//2), self.radius)
