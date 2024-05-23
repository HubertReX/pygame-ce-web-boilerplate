from state import State
from settings import FONT_SIZE_DEFAULT, FONT_SIZE_LARGE, HEIGHT, INPUTS, COLORS, TEXT_ROW_SPACING, WIDTH
import pygame
import game


class SplashScreen(State):
    def __init__(self, game: game.Game, name: str = "") -> None:
        super().__init__(game)
        self.name = name

    def __repr__(self) -> str:
        return f"{__class__.__name__}: {self.name}"

    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS["left_click"]:
            self.game.reset_inputs()
            self.exit_state()

        if INPUTS["right_click"]:
            self.game.reset_inputs()
            self.exit_state()

        if INPUTS["quit"]:
            self.game.reset_inputs()
            self.exit_state()

        if INPUTS["accept"]:
            self.game.reset_inputs()
            self.exit_state()

        if INPUTS["select"]:
            # Scene(self.game, "grasslands", "start").enter_state()
            self.game.reset_inputs()
            self.exit_state()

    def draw(self, screen: pygame.Surface, dt: float):
        screen.fill(COLORS["blue"])
        self.game.render_text(f"{self.name}", (WIDTH / 2, HEIGHT / 2), font_size=FONT_SIZE_LARGE, centred=True)
        self.game.render_text(
            "press space to continue",
            (WIDTH / 2, HEIGHT - (FONT_SIZE_DEFAULT * TEXT_ROW_SPACING)),
            centred=True
        )
