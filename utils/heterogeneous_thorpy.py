"""We show here how to declare heterogeneous text, i.e. text with mixed font styles."""

import pygame
import thorpy as tp

pygame.init()

screen = pygame.display.set_mode((800, 700))
tp.init(screen, tp.theme_human)  # bind screen to gui elements and set theme

texts = [("Hello, world. ", {"name": "arialrounded"}),
         ("How ", {"color": (0, 0, 255)}),
         ("are ", {}),
         ("you ", {"color": (0, 255, 0), "size": 25, "outlined": True, }),  # "outline_color": (255, 0, 0)
         ("doing?", {"name": "timesnewroman"}),
         ("new line?", {}),
         #  ("Can you wrap a very long line of text so it looks good?", {}),
         ]
text = tp.HeterogeneousTexts(texts, mode="grid")  # mode="h", align="bottom"
text.set_max_text_width(150)
# text.set_font_auto_multilines_width(150, refresh=False)
text.set_size((100, 100))
text.center_on(screen)


def before_gui():  # add here the things to do each frame before blitting gui elements
    screen.fill((255,) * 3)


tp.call_before_gui(before_gui)  # tells thorpy to call before_gui() before drawing gui.

# For the sake of brevity, the main loop is replaced here by a shorter but blackbox-like method
player = text.get_updater().launch()
pygame.quit()
