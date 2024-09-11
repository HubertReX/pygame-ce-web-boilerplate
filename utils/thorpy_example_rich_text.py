"""
Rich text allows you to define a tag that can be used inside strings to modify the text of gui's
elements.

Text properties that can be modified using tags :
    * Color
Text properties that cannot be modified using tags :
    * Font family
    * Font size
Text properties that are modified at the element level :
    * Text-align
    * Max text width

To mix font families or font sizes, you should rather consider to wrap your elements into a parent
that sorts its elements horizontally.
"""
# tags: set_font_rich_text_tag, advanced styling, rich text, rich, text, color text, color, text style,
# text styling, align, set_font_auto_multilines_width, set_style_attr

import os
import pygame
import thorpy as tp
from sftext.sftext import SFText
from sftext.style import Style
from rich import print

pygame.init()

W, H = 1200, 700
screen = pygame.display.set_mode((W, H))
bck = pygame.image.load(tp.fn("data/bck.jpg"))
bck = pygame.transform.smoothscale(bck, (W, H))  # load some background pic


def before_gui():  # add here the things to do before blitting gui elements
    screen.blit(bck, (0, 0))  # blit background pic


tp.init(screen, tp.theme_classic)

some_long_text = """#RGB(255,255,255)Hello, world.
This is a #RGB(255,0,0)rich# text that should #RGB(0,0,255)automatically be cut# in 😋 several => lines ⬅️.
I repeat, this is a rich text that should be auto cut in several lines.#"""

some_long_text = """{style}{indent 20}{bold True}Really?{style} You got so wasted that you don't even remember me? It's odd that a fool like you managed to survive this long. I, of all, am your only and most faithful companion. Not that I have much choice - you keep me by your side, and I can't walk on my own. {style}{indent 20}Thus, I'm an involuntary witness to all of your {style}{underline True}exploits{style}. I'm a sword, forged from the soul of fire, and besides a sharp edge, I have an equally sharp tongue. My name is {style}{color (255, 255, 0)}Clapback Sword{style}, and if only you could wield me skillfully, we would be invincible.
{style}

1.\tOh, I see. Thanks for clearing that up. What would I do without you?

2.\tYou talk as if you were my mother. I'm an adult, I can do whatever I want.

3.\t{style}{color (255, 255, 0)}Clapback Sword{style} isn't just your name, but also your specialty - you're a real riot.
"""

s = Style().get_default("")
s["indent"] = 10
stylized_text = Style.stylize(some_long_text, s)
text, style = Style.split(stylized_text)
# print('\n"{}"'.format(style))
print(text)
print(style)
s['color'] = (255, 255, 255)
Style.set_default(s)

formatted_text = SFText(text=some_long_text, font_path=os.path.join('.', 'sftext', 'example', 'resources'), style=s)

# let's replace the \n inserted in the str above. Note that you can manually place line breaks, but
#   we do remove them here as we want to illustrate auto line break only, for pedagogic purpose.
# some_long_text = some_long_text.replace("\n", " ")

# text = tp.Text.style_normal.insert_auto_breakline(some_long_text, 300)
# print(text)

# my_button = tp.Button(some_long_text, generate_surfaces=False)
my_button = tp.Text(some_long_text, generate_surfaces=True)
my_button.set_font_auto_multilines_width(700, refresh=False)
# print(my_button.get_text_size())
# print(my_button.get_value())
# Arbitrarily choosing '#' as the tag here, but you are free to set whatever you like.
my_button.set_font_color([255, 255, 255])
my_button.set_font_rich_text_tag("#")  # setting a tag automatically enable rich text (disabled by default)
my_button.set_style_attr("font_align", "l")  # font_align is either 'l', 'r' or 'c' (left, right and center)
my_button.center_on(screen)
my_ui_elements = tp.Group([my_button])
updater = my_ui_elements.get_updater()

m = tp.Loop(element=my_button)
clock = pygame.time.Clock()
while m.playing:
    clock.tick(m.fps)
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            m.playing = False
    # m.update(before_gui)
    before_gui()
    # updater.update(events=events)
    # screen.blit(my_button.surface, (0, 0))
    formatted_text.on_update()
    pygame.display.flip()

pygame.quit()
