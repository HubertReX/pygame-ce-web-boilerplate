from settings import *
import pygame
import game

##########################################################################################################################
#MARK: State
class State:
    def __init__(self, game: game.Game) -> None:
        self.game = game
        self.prev_state: "State" | None = None

    def enter_state(self):
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)
        
    def exit_state(self):
        if len(self.game.states) > 1:
            self.game.states.pop()
            
    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS['quit'] and not IS_WEB:
            self.game.running = False
            
        global SHOW_DEBUG_INFO
        if INPUTS['debug']:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()
            
        global SHOW_HELP_INFO
        if INPUTS['help']:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            self.game.reset_inputs()
            
    def draw(self, screen: pygame.Surface):
        raise NotImplementedError("Subclasses should implement this!")
        
    def debug(self, msgs: list[str]):
        if SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (10, 25 * i))
    
    