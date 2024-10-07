# GitHub:
# https://github.com/Rabbid76/PyGameExamplesAndAnswers/blob/master/documentation/pygame/pygame_blending_and_transaprency.md
#
# Stack Overflow:
# https://stackoverflow.com/questions/58385570/trying-to-make-sections-of-sprite-change-colour-but-whole-sprite-changes-instea/58402923#58402923

import pygame

color = (0, 0, 255, 0)

pygame.init()
window = pygame.display.set_mode((700, 700))

font = pygame.font.SysFont('Times New Roman', 20)

# bg_image = pygame.Surface((64, 64), pygame.SRCALPHA)
bg_image = pygame.image.load("bg.png").convert_alpha()

night_image = pygame.Surface(bg_image.get_size(), pygame.SRCALPHA)
night_image.fill((0, 0, 120, 120))
night_image = pygame.transform.scale_by(night_image, 4)
# pygame.draw.circle(bg_image, (255, 255, 255, 255), (32, 32), 32)
# pygame.draw.rect(bg_image, (255, 0, 0, 255), (16, 16, 32, 32))

mask = pygame.Surface(bg_image.get_size(), pygame.SRCALPHA)
mask.fill((0, 0, 0, 0))
# pygame.draw.rect(mask, (255, 255, 255, 255), (16, 16, 32, 32))
pygame.draw.circle(mask, (255, 255, 255, 255), (32, 32), 32)

# Create coloured image the size of the entire sprite
day_image = pygame.Surface(bg_image.get_size(), pygame.SRCALPHA)  # TODO UNDO
day_image.fill((255, 255, 0, 110))

# create mask area
masked = mask.copy()
masked.blit(day_image, (0, 0), None, pygame.BLEND_RGBA_MULT)


# create the final image
final_image = night_image.copy()
final_image.blit(masked, (0, 0), None, pygame.BLEND_RGBA_MAX)
final_image.blit(masked, (32, 32), None, pygame.BLEND_RGBA_MAX)
final_image.blit(masked, (64, 64), None, pygame.BLEND_RGBA_MAX)

final_bg = bg_image.copy()
final_bg = pygame.transform.scale_by(final_bg, 4)
final_bg.blit(final_image, (0, 0), None)
# final_bg.blit(final_image, (32, 32), None)
# final_bg.blit(final_image, (64, 64), None)

# final_image =  mask.copy()
# final_image.blit(coloured_image, (0, 0), None, pygame.BLEND_RGBA_MULT)

# masked = final_image.copy()

# put the source image on top of the colored aread
# final_image.blit(image, (0, 0), None)

# main application loop
run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    window.fill((32, 32, 32, 255))
    # window.blit(night_image, (20, 20))
    # window.blit(font.render("night_image", True, (255, 255, 255)), (100, 35))

    window.blit(mask, (20, 90))
    window.blit(font.render("mask", True, (255, 255, 255)), (100, 105))

    window.blit(day_image, (20, 160))
    window.blit(font.render("day_image", True, (255, 255, 255)), (100, 175))

    window.blit(masked, (20, 230))
    window.blit(font.render("masked", True, (255, 255, 255)), (100, 245))

    window.blit(final_image, (300, 20))
    window.blit(font.render("final_image", True, (255, 255, 255)), (580, 35))

    window.blit(bg_image, (20, 380))
    window.blit(font.render("bg_image", True, (255, 255, 255)), (100, 395))

    window.blit(final_bg, (300, 300))
    window.blit(font.render("final_bg", True, (255, 255, 255)), (580, 335))
    pygame.display.flip()

pygame.quit()
exit()
