# /// script
# [project]
# name = "Joystick"
# version = "0.1"
# description = "Gamepad/joystick testing script."
# requires-python = ">=3.12"
#
# dependencies = [
#  "rich",
# ]

import asyncio
import os
import pygame
from rich import print
# 00000000000000000000000000000000,XInput Controller,a:b0,b:b1,back:b6,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,
# dpup:h0.1,guide:b10,leftshoulder:b4,leftstick:b8,lefttrigger:a2,leftx:a0,lefty:a1,rightshoulder:b5,rightstick:b9,righttrigger:a5,rightx:a3,righty:a4,start:b7,x:b2,y:b3,platform:Windows,
# SDL_GAMECONTROLLERCONFIG=030000005e040000ea02000000007801,XInput ControllerA-B,
# platform:Windows,a:b1,b:b0,
# os.environ["SDL_GAMECONTROLLERCONFIG"] =\
#     "0300938d5e040000ea02000000007200,XInput ControllerA-B,platform:Windows,a:b1,b:b0,"
# a = "030000005e040000ea02000000000000"
# initialise the joystick module
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
# https://www.reddit.com/r/pygame/comments/12twl0e/cannot_rumble_dualshock_4_via_bluetooth_in_pygame/
os.environ["SDL_JOYSTICK_HIDAPI_PS4_RUMBLE"] = "1"
# Keep watching the joystick feedback even when this window doesn't have focus.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"


pygame.init()
pygame.joystick.init()

# define screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500

# define font
font_size = 30
# font_small_size = 16
font = pygame.font.SysFont("Futura", font_size)
# font_small = pygame.font.SysFont("Futura", font_small_size)

VALUE_X_OFFSET = 200
ROW_HEIGHT = font.get_linesize()
LABEL_COLOR = pygame.Color("royalblue")
VALUE_COLOR = pygame.Color("crimson")
SLIDER_BORDER = 4
SLIDER_SPACING = 1
FPS = 60
JOY_OFFSET = 50


def draw_text(screen:  pygame.Surface, text: str, font: pygame.Font, text_col: pygame.Color, x: int, y: int) -> None:
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_slider(screen:  pygame.Surface, val: float, x: int, y: int) -> None:
    # draw_text(label, font, LABEL_COLOR, x, y)
    pygame.draw.rect(
        screen,
        LABEL_COLOR,
        (x, y + SLIDER_SPACING,
         VALUE_X_OFFSET, ROW_HEIGHT - 2 * SLIDER_SPACING),
        SLIDER_BORDER)
    pygame.draw.rect(
        screen,
        VALUE_COLOR,
        (x + SLIDER_BORDER, y + SLIDER_BORDER + SLIDER_SPACING,
         ((val + 1.0) / 2.0) * (VALUE_X_OFFSET - 2 * SLIDER_BORDER), ROW_HEIGHT - 2 * (SLIDER_BORDER + SLIDER_SPACING)))


def draw_text_property(screen:  pygame.Surface, label: str, val: str, x: int, y: int) -> None:
    draw_text(screen, label, font, LABEL_COLOR, x, y)
    draw_text(screen, val, font, VALUE_COLOR, x + VALUE_X_OFFSET, y)


def draw_float_property(screen:  pygame.Surface, label: str, val: float, x: int, y: int) -> None:
    draw_text(screen, label, font, LABEL_COLOR, x, y)
    draw_slider(screen, val, x + VALUE_X_OFFSET, y)


def draw_properties(screen:  pygame.Surface, properties: list[tuple[int, str, str | float | int]]) -> None:
    for row_no, property in enumerate(properties):

        x = JOY_OFFSET + property[0] * (VALUE_X_OFFSET + JOY_OFFSET) * 2
        y = JOY_OFFSET + (row_no * ROW_HEIGHT)
        if type(property[2]) is str:
            draw_text_property(screen, property[1], property[2], x, y)
        elif type(property[2]) in [float, int]:
            draw_float_property(screen, property[1], property[2], x, y)
        else:
            print(f'Unknown property type {type(property[2])}')


class Joystick():
    def __init__(self, id: int) -> None:
        self.id = id
        self.joy = pygame.joystick.Joystick(id)
        self.guid = self.joy.get_guid()
        self.name = self.joy.get_name()
        self.power_level = self.joy.get_power_level()
        # self.joy.init()
        self.numaxes    = self.joy.get_numaxes()
        self.numballs   = self.joy.get_numballs()
        self.numbuttons = self.joy.get_numbuttons()
        self.numhats    = self.joy.get_numhats()

        self.axis: list[float] = []
        for i in range(self.numaxes):
            self.axis.append(self.joy.get_axis(i))

        self.ball: list[tuple[float, float]] = []
        for i in range(self.numballs):
            self.ball.append(self.joy.get_ball(i))

        self.button: list[bool] = []
        for i in range(self.numbuttons):
            self.button.append(self.joy.get_button(i))

        self.hat: list[tuple[int, int]] = []
        for i in range(self.numhats):
            self.hat.append(self.joy.get_hat(i))


def draw_joystick(screen:  pygame.Surface, id: int, joystick: Joystick) -> None:
    properties: list[tuple[int, str, str | float]] = []
    properties.append((id, f"GUID:{joystick.guid}", ""))
    properties.append((id, f"Press [{id + 1}] to test vibrations (rumble)", ""))
    properties.append((id, "Name:", str(joystick.name)))
    properties.append((id, "Battery level:", joystick.power_level))
    properties.append((id, "No. of axes:", str(joystick.numaxes)))
    properties.append((id, "No. of hats:", str(joystick.numhats)))
    properties.append((id, "No. of buttons:", str(joystick.numbuttons)))

    for axis_id in range(joystick.numaxes):
        properties.append((id, f"Axis({axis_id}):", joystick.axis[axis_id]))

    for hat_id in range(joystick.numhats):
        properties.append((id, f"Hat({hat_id}).x:", str(joystick.hat[hat_id][0])))
        properties.append((id, f"Hat({hat_id}).y:", str(joystick.hat[hat_id][1])))

    properties.append((id, "Buttons pressed:", ", ".join((str(id) for id, b in enumerate(joystick.button) if b))))

    draw_properties(screen, properties)


def process_events(screen:  pygame.Surface, joysticks: dict[int, Joystick]) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED:
            id = event.device_index
            joysticks[id] = Joystick(id)
        elif event.type == pygame.JOYDEVICEREMOVED:
            id = event.instance_id
            if id in joysticks:
                del joysticks[id]
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE) # noqa F841
        elif event.type == pygame.JOYAXISMOTION:
            joysticks[event.joy].axis[event.axis] = event.value
        elif event.type == pygame.JOYBALLMOTION:
            joysticks[event.joy].ball[event.ball] = event.rel
        elif event.type == pygame.JOYHATMOTION:
            joysticks[event.joy].hat[event.hat] = event.value
        elif event.type == pygame.JOYBUTTONUP:
            joysticks[event.joy].button[event.button] = 0
        elif event.type == pygame.JOYBUTTONDOWN:
            joysticks[event.joy].button[event.button] = 1
        elif event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_q]:
            return False
        elif event.type == pygame.KEYDOWN and event.key in range(pygame.K_1, pygame.K_9 + 1):
            id = event.key - pygame.K_1
            if id in joysticks:
                joysticks[id].joy.rumble(1, 1, 250)

    return True


async def main() -> None:

    # create game window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Joysticks")

    # create clock for setting game frame rate
    clock = pygame.time.Clock()

    # create empty list to store joysticks
    joysticks: dict[int, Joystick] = {}

    # game loop
    run = True

    while run:

        clock.tick(FPS)

        # update background
        screen.fill(pygame.Color("midnightblue"))

        # show number of connected joysticks
        draw_text_property(screen, "Controllers count:", str(pygame.joystick.get_count()), 10, 10)
        for id, joystick in joysticks.items():
            draw_joystick(screen, id, joystick)

        # emulate 2 controllers
        # if len(joysticks.keys()) > 0:
        #     key = list(joysticks.keys())[0]
        #     draw_joystick(screen, 0, joysticks[key])
        #     draw_joystick(screen, 1, joysticks[key])

        # event handler
        run = process_events(screen, joysticks)

        # update display
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
