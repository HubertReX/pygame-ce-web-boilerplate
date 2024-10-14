import pygame
import sys
import pygame._sdl2
from pygame._sdl2.controller import Controller
import os
os.environ["SDL_GAMECONTROLLERCONFIG"] =\
    "0300938d5e040000ea02000000007200,XInput ControllerA-B,platform:Windows,a:b1,b:b0,"


pygame.init()
window = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Testing controllers")

font = pygame.font.Font(None, 30)


def debug(info, y=10, x=20):
    display_surf = pygame.display.get_surface()
    debug_surf = font.render(str(info), False, 'white', 'black')
    debug_rect = debug_surf.get_rect(topleft=(x, y))
    display_surf.blit(debug_surf, debug_rect)


clock = pygame.time.Clock()

pygame._sdl2.controller.init()

debug_messages = []

while True:
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    window.fill('white')

    for joystick in joysticks:
        controller = Controller.from_joystick(joystick)
        controller.init()
        js = []
        js.append(joystick.get_guid())
        js.append(joystick.get_name())
        for button in range(joystick.get_numbuttons()):
            btn_message = 'Button ' + str(button) + ': ' + str(controller.get_button(button))
            js.append(btn_message)
        for axis in range(joystick.get_numaxes()):
            axis_message = 'Axis ' + str(axis) + ': ' + str(controller.get_axis(axis))
            js.append(axis_message)

        debug_messages.append(js)

    for js, dbg_messages in enumerate(debug_messages):
        for i, message in enumerate(dbg_messages):
            y = i * 18
            if js == 0:
                x = 20
            else:
                x = js * 420
            debug(message, y, x)

    pygame.display.flip()
    clock.tick(60)
    debug_messages.clear()
