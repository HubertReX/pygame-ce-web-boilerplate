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
        
    def exit_state(self, quit: bool = True):
        if len(self.game.states) > 1:
            self.game.states.pop()
        else:
            if not IS_WEB and quit:
                self.game.is_running = False
            
    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS["quit"] and not IS_WEB:
            self.game.is_running = False
            
        global SHOW_DEBUG_INFO
        if INPUTS["debug"]:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()
            
        global SHOW_HELP_INFO
        if INPUTS["help"]:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            self.game.reset_inputs()
            
    def draw(self, screen: pygame.Surface, dt: float):
        raise NotImplementedError("Subclasses should implement this!")
        
    def debug(self, msgs: list[str]):
        global SHOW_DEBUG_INFO
        # print(f"STATE {SHOW_DEBUG_INFO=}")
        # if SHOW_DEBUG_INFO:
        rect = pygame.Rect(10 - 4, -10 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING, 600, (len(msgs) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)
        self.game.render_panel(rect, (10,10,10,150))

        for i, msg in enumerate(msgs):
            self.game.render_text(msg, (10, FONT_SIZE_MEDIUM * TEXT_ROW_SPACING * (i + 1)))
    
    