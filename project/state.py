from __future__ import annotations

import game
import pygame
from settings import FONT_SIZE_MEDIUM, INPUTS, IS_WEB, SHOW_DEBUG_INFO, SHOW_HELP_INFO, TEXT_ROW_SPACING

#################################################################################################################


class State:
    # MARK: State
    def __init__(self, game: game.Game) -> None:
        self.game = game
        self.prev_state: State | None  = None

    #############################################################################################################
    def enter_state(self) -> None:
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)

    #############################################################################################################
    def exit_state(self, quit: bool = True) -> None:
        if len(self.game.states) > 1:
            self.game.states.pop()
        else:
            if not IS_WEB and quit:
                self.game.is_running = False

    #############################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]) -> None:
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

    #############################################################################################################
    def draw(self, screen: pygame.Surface, dt: float) -> None:
        raise NotImplementedError("Subclasses should implement this!")

    #############################################################################################################
    def debug(self, msgs: list[str]) -> None:
        global SHOW_DEBUG_INFO
        # print(f"STATE {SHOW_DEBUG_INFO=}")
        # if SHOW_DEBUG_INFO:
        rect = pygame.Rect(
            10 - 4,
            -10 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING,
            600,
            (len(msgs) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING
        )
        self.game.render_panel(rect, (10, 10, 10, 150))

        for i, msg in enumerate(msgs):
            self.game.render_text(msg, (10, int(FONT_SIZE_MEDIUM * TEXT_ROW_SPACING * (i + 1))))
