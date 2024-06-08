import pygame

pygame.init()

# initialise the joystick module
pygame.joystick.init()

# define screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500

JOY_DRIFT = 0.11
JOY_MOVE_MULTIPLIER = 15
# create game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Joysticks")

# define font
font_size = 30
font = pygame.font.SysFont("Futura", font_size)

# function for outputting text onto the screen


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# create clock for setting game frame rate
clock = pygame.time.Clock()
FPS = 60

# create empty list to store joysticks
joysticks = []

# create player rectangle
x = 350
y = 200
player_w = 100
player_h = 100
player = pygame.Rect(x, y, player_w, player_h)

# define player colour
col = "royalblue"

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
    draw_text("Controllers: " + str(pygame.joystick.get_count()), font, pygame.Color("azure"), 10, 10)
    for joystick in joysticks:
        draw_text("Battery Level: " + str(joystick.get_power_level()), font, pygame.Color("azure"), 10, 35)
        draw_text("Controller Type: " + str(joystick.get_name()), font, pygame.Color("azure"), 10, 60)
        draw_text("Number of axes: " + str(joystick.get_numaxes()), font, pygame.Color("azure"), 10, 85)
        draw_text(
            f"Number of hats: {str(joystick.get_numhats())} ", font, pygame.Color("azure"), 10, 110)
        # str(joystick.get_hat(0))}
        buttons = []
        for i in range(joystick.get_numbuttons()):
            if joystick.get_button(i):
                buttons.append(str(i))
        draw_text("Buttons pressed: " + ", ".join(buttons), font, pygame.Color("azure"), 10, 135)

    for joystick in joysticks:
        # change player colour with buttons
        if joystick.get_button(0):
            col = "royalblue"
        if joystick.get_button(1):
            col = "crimson"
        if joystick.get_button(2):
            col = "fuchsia"
        if joystick.get_button(3):
            col = "forestgreen"

        if joystick.get_button(4):
            joystick.rumble(1, 1, 250)

        # player movement with joystick
        if joystick.get_button(14):
            x += 5
        if joystick.get_button(13):
            x -= 5
        if joystick.get_button(11):
            y -= 5
        if joystick.get_button(12):
            y += 5

        # player movement with first analogue sticks
        horiz_move = joystick.get_axis(0)
        vert_move = joystick.get_axis(1)
        if abs(vert_move) > JOY_DRIFT:
            y += vert_move * JOY_MOVE_MULTIPLIER
        if abs(horiz_move) > JOY_DRIFT:
            x += horiz_move * JOY_MOVE_MULTIPLIER

        # resize player with second analogue stick
        horiz_size = joystick.get_axis(2)
        vert_size = joystick.get_axis(3)
        if abs(vert_size) > JOY_DRIFT:
            player_h += vert_size * 15
        if abs(horiz_size) > JOY_DRIFT:
            player_w += horiz_size * 15

        player_w = max(5, player_w)
        player_h = max(5, player_h)

    # event handler
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED:
            joy = pygame.joystick.Joystick(event.device_index)
            joysticks.append(joy)
        # quit program
        elif event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_q]:
            run = False

    # update display
    pygame.display.flip()

pygame.quit()
