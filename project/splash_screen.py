from state import State
from settings import *
import pygame
import game

class SplashScreen(State):
    def __init__(self, game: game.Game, name: str="") -> None:
        super().__init__(game)
        self.name = name
        
    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS['left_click']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['right_click']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['quit']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['accept']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['select']:
            # Scene(self.game, 'grasslands', 'start').enter_state()
            self.game.reset_inputs()
            self.exit_state()
            
    def draw(self, screen: pygame.Surface):
        screen.fill(COLORS["blue"])
        self.game.render_text(f"{self.__class__.__name__}-{self.name}", (WIDTH / 2, HEIGHT / 2), centred=True)
        self.game.render_text(f"press space to continue", (WIDTH / 2, HEIGHT / 2 + TILE_SIZE + 10), centred=True)
