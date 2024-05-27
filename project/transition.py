import pygame
from settings import WIDTH, HEIGHT, COLORS
# import scene

#######################################################################################################################


class Transition():

    def __init__(self, scene: "Scene") -> None:  # noqa:  F821
        self.fade_surf: pygame.Surface = pygame.Surface((WIDTH, HEIGHT))
        self.scene = scene
        self.exiting: bool = False
        self.fade_out_speed: int = 800
        self.fade_in_speed: int = 200
        self.alpha: int = 255
        self.radius: int = 0

    ###################################################################################################################
    def update(self, dt: float):
        if self.exiting:
            self.alpha = min(255, int(self.alpha + self.fade_out_speed * dt))
            if self.alpha == 255:
                # self.scene.go_to_scene()
                self.scene.go_to_map()
        else:
            self.alpha = max(0, self.alpha - int(self.fade_in_speed * dt))
        # self.radius = (WIDTH//2) -  (WIDTH//2) * (self.alpha/255)
        self.radius = (WIDTH * 2.7) -  (WIDTH * 2.7) * (self.alpha / 255)

    ###################################################################################################################
    def draw(self, screen: pygame.Surface):
        self.fade_surf.fill(COLORS["black"])
        self.fade_surf.set_alpha(self.alpha)
        screen.blit(self.fade_surf, (0, 0))
        # pygame.draw.circle(screen, (10,10,10), (WIDTH//2, HEIGHT//2), self.radius)


#######################################################################################################################
class TransitionCircle(Transition):

    def draw(self, screen: pygame.Surface):
        self.fade_surf.fill((1, 1, 1))
        # pos = self.scene.player.pos
        # offset_x, offset_y = self.scene.map_view.get_center_offset()
        # zoom = self.scene.map_view.zoom
        pos = self.scene.map_view.translate_point(self.scene.player.pos)
        # pygame.draw.circle(self.fade_surf, (0,0,0), (WIDTH//2, HEIGHT//2), self.radius)
        pygame.draw.circle(self.fade_surf, (0, 0, 0), pos, self.radius)
        # self.fade_surf.set_alpha(self.alpha)
        self.fade_surf.set_colorkey((0, 0, 0))
        screen.blit(self.fade_surf, (0, 0))
        # pygame.draw.circle(screen, (10,10,10), (WIDTH//2, HEIGHT//2), self.radius)
