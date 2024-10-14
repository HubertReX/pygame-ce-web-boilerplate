import os
import pygame
from rich import print
# 00000000000000000000000000000000,XInput Controller,a:b0,b:b1,back:b6,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,
# dpup:h0.1,guide:b10,leftshoulder:b4,leftstick:b8,lefttrigger:a2,leftx:a0,lefty:a1,rightshoulder:b5,rightstick:b9,righttrigger:a5,rightx:a3,righty:a4,start:b7,x:b2,y:b3,platform:Windows,
# SDL_GAMECONTROLLERCONFIG=030000005e040000ea02000000007801,XInput ControllerA-B,
# platform:Windows,a:b1,b:b0,
os.environ["SDL_GAMECONTROLLERCONFIG"] =\
    "0300938d5e040000ea02000000007200,XInput ControllerA-B,platform:Windows,a:b1,b:b0,"
a = "030000005e040000ea02000000000000"
# initialise the joystick module
pygame.init()
pygame.joystick.init()

# define screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500

JOY_DRIFT = 0.11
JOY_MOVE_MULTIPLIER = 15
# create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Joysticks")

# define font
font_size = 30
font_small_size = 16
font = pygame.font.SysFont("Futura", font_size)
font_small = pygame.font.SysFont("Futura", font_small_size)

# function for outputting text onto the screen
VALUE_OFFSET = 180
VALUE_HEIGHT = font.get_linesize()
LABEL_COLOR = pygame.Color("royalblue")
VALUE_COLOR = pygame.Color("crimson")
SLIDER_BORDER = 4


def draw_text(text: str, font: pygame.Font, text_col: pygame.Color, x: int, y: int) -> None:
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_slider(val: float, x: int, y: int) -> None:
    # draw_text(label, font, LABEL_COLOR, x, y)
    pygame.draw.rect(screen, LABEL_COLOR, (x, y,
                                           VALUE_OFFSET, VALUE_HEIGHT), SLIDER_BORDER)
    pygame.draw.rect(screen, VALUE_COLOR, (x + SLIDER_BORDER, y + SLIDER_BORDER,
                                           ((val + 1.0) / 2.0) * (VALUE_OFFSET - 2 * SLIDER_BORDER), VALUE_HEIGHT - 2 * SLIDER_BORDER))


def draw_text_property(label: str, val: str, x: int, y: int) -> None:
    draw_text(label, font, LABEL_COLOR, x, y)
    draw_text(val, font, VALUE_COLOR, x + VALUE_OFFSET, y)


def draw_float_property(label: str, val: float, x: int, y: int) -> None:
    draw_text(label, font, LABEL_COLOR, x, y)
    draw_slider(val, x + VALUE_OFFSET, y)


# create clock for setting game frame rate
clock = pygame.time.Clock()
FPS = 60


# create player rectangle
x = 350
y = 200
player_w = 100
player_h = 100
player = pygame.Rect(x, y, player_w, player_h)

# define player color
col = "royalblue"


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

        self.hat: list[tuple[float, float]] = []
        for i in range(self.numhats):
            self.hat.append(self.joy.get_hat(i))


# create empty list to store joysticks
joysticks: dict[int, Joystick] = {}

# game loop
run = True
while run:

    clock.tick(FPS)

    # update background
    screen.fill(pygame.Color("midnightblue"))

    # draw player
    player.topleft = (x, y)
    player.width = player_w
    player.height = player_h
    pygame.draw.rect(screen, pygame.Color(col), player)

    # show number of connected joysticks
    draw_text_property("controllers count:", str(pygame.joystick.get_count()), 10, 10)
    for id, joystick in joysticks.items():
        draw_text_property("Battery level: ", joystick.power_level, 200, 35)
        # draw_text_property(f"ID: {str(joystick.guid)}", "", 10, 35)
        draw_text(f"GUID: {str(joystick.guid)}", font_small, VALUE_COLOR, 10, 35)
        # print(joystick.guid)
        draw_text_property("Name:", str(joystick.name), 10, 60)
        draw_text_property("No of axes:", str(joystick.numaxes), 10, 85)
        draw_text_property("No of hats:", str(joystick.numhats), 10, 110)
        draw_text_property("No of buttons:", str(joystick.numbuttons), 10, 135)
        # str(joystick.hat(0))}
        buttons = []
        for i in range(joystick.numbuttons):
            if joystick.button[i]:
                buttons.append(str(i))

        draw_text_property("Buttons pressed:", ", ".join(buttons), 10, 160)
        draw_float_property("Left X:", joystick.axis[0], 10, 185)
        draw_float_property("LB:", joystick.axis[4], 10, 210)
        draw_text_property("Hat_X:", str(joystick.hat[0][0]), 10, 235)
        # draw_float_property("Hat_X:", joystick.hat[0][0], 10, 235)
        draw_float_property("Hat_Y:", joystick.hat[0][1], 10, 260)

    for joystick in joysticks.values():
        # change player color with buttons
        # if joystick.button[0]:
        #     col = "royalblue"
        # if joystick.button[1]:
        #     col = "crimson"
        # if joystick.button[2]:
        #     col = "fuchsia"
        # if joystick.button[3]:
        #     col = "forestgreen"

        if joystick.button[4]:
            joystick.joy.rumble(1, 1, 250)

        # player movement with joystick
        # if joystick.button[14]:
        #     x += 5
        # if joystick.button[13]:
        #     x -= 5
        # if joystick.button[11]:
        #     y -= 5
        # if joystick.button[12]:
        #     y += 5

        # player movement with first analogue sticks
        hor_move = joystick.axis[0]
        vert_move = joystick.axis[1]
        if abs(vert_move) > JOY_DRIFT:
            y += vert_move * JOY_MOVE_MULTIPLIER
        if abs(hor_move) > JOY_DRIFT:
            x += hor_move * JOY_MOVE_MULTIPLIER

        # resize player with second analogue stick
        hor_size = joystick.axis[2]
        vert_size = joystick.axis[3]
        if abs(vert_size) > JOY_DRIFT:
            player_h += vert_size * 15
        if abs(hor_size) > JOY_DRIFT:
            player_w += hor_size * 15

        player_w = max(5, player_w)
        player_h = max(5, player_h)

    # event handler
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED:
            # joy = pygame.joystick.Joystick(event.device_index)
            id = event.device_index
            joy = Joystick(id)
            print(event)
            joysticks[id] = joy
        elif event.type == pygame.JOYDEVICEREMOVED:
            print(event)
            # joy = pygame.joystick.Joystick(event.instance_id)
            id = event.instance_id
            # joysticks.remove(joy)
            del joysticks[id]
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
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
        # quit program
        elif event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_q]:
            run = False

    # update display
    pygame.display.flip()

pygame.quit()
