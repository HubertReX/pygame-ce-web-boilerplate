import pygame

pygame.init()

display_surface = pygame.display.set_mode((800, 800))

temp_surface = pygame.Surface((512, 512), pygame.SRCALPHA)

# use this to set the amount of 'segments' we rotate our blend into
# this helps stop blends from looking 'boxy' or like a cross.
circular_smoothness_steps = 5

colour_1 = pygame.Color((160, 160, 0, 200))
colour_1.r = colour_1.r//circular_smoothness_steps
colour_1.g = colour_1.g//circular_smoothness_steps
colour_1.b = colour_1.b//circular_smoothness_steps
colour_1.a = colour_1.a//circular_smoothness_steps

colour_2 = pygame.Color((180, 30, 255, 255))
colour_2.r = colour_2.r//circular_smoothness_steps
colour_2.g = colour_2.g//circular_smoothness_steps
colour_2.b = colour_2.b//circular_smoothness_steps
colour_2.a = colour_2.a//circular_smoothness_steps


# 3x3 - starter
radial_grad_starter = pygame.Surface((3, 3), pygame.SRCALPHA)
radial_grad_starter.fill(colour_1)
radial_grad_starter.fill(colour_2, pygame.Rect(1, 1, 1, 1))

# 5x5 - starter
# radial_grad_starter = pygame.Surface((5, 5))
# radial_grad_starter.fill((0, 0, 0))
# radial_grad_starter.fill((255//circular_smoothness_steps,
#                           255//circular_smoothness_steps,
#                           255//circular_smoothness_steps), pygame.Rect(2, 1, 1, 3))
# radial_grad_starter.fill((255//circular_smoothness_steps,
#                           255//circular_smoothness_steps,
#                           255//circular_smoothness_steps), pygame.Rect(1, 2, 3, 1))


radial_grad = pygame.transform.smoothscale(radial_grad_starter, (512, 512))

for i in range(0, circular_smoothness_steps):
    radial_grad_rot = pygame.transform.rotate(radial_grad, (360.0/circular_smoothness_steps) * i)

    pos_rect = pygame.Rect((0, 0), (512, 512))

    area_rect = pygame.Rect(0, 0, 512, 512)
    area_rect.center = radial_grad_rot.get_width()//2, radial_grad_rot.get_height()//2
    temp_surface.blit(radial_grad_rot, pos_rect,
                      area=area_rect,
                      special_flags=pygame.BLEND_RGBA_ADD)

final_pos_rect = pygame.Rect((0, 0), (512, 512))
final_pos_rect.center = 400, 400
display_surface.blit(temp_surface, final_pos_rect)

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()