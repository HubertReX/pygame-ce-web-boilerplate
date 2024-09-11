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
import re
import pygame
import thorpy as tp
from sftext import SFText
from style import Style
# from rich import print

pygame.init()

W, H = 1200, 700
screen = pygame.display.set_mode((W, H))
bck = pygame.image.load(tp.fn("data/bck.jpg"))
bck = pygame.transform.smoothscale(bck, (W, H))  # load some background pic

# style_tags_dict = {
#     "bold":      ("{bold True}",      "{style}{bold False}"),
#     "italic":    ("{italic True}",    "{style}{italic False}"),
#     "underline": ("{underline True}", "{style}{underline False}"),
#     "big":       ("{size 55}",        "{style}"),
#     "small":     ("{size 12}",        "{style}"),
#     "left":      ("{align left}",     "{style}{align left}"),
#     "right":     ("{align right}",    "{style}{align left}"),
#     "center":    ("{align center}",   "{style}{align left}"),
#     "act":       ("{color (255,110,104)}", "{style}{color (0,197,199)}"),
#     "char":      ("{color (255,252,103)}", "{style}{color (0,197,199)}"),
#     "item":      ("{color (104,113,255)}", "{style}{color (0,197,199)}"),
#     "loc":       ("{color (95,250,104)}",  "{style}{color (0,197,199)}"),
#     "num":       ("{color (255,119,255)}", "{style}{color (0,197,199)}"),
#     "quest":     ("{color (96,253,255)}",  "{style}{color (0,197,199)}"),
#     "text":      ("{color (0,197,199)}",   "{style}{color (0,197,199)}"),
# }

style_tags_dict = {
    "bold":      "{bold True}",
    "italic":    "{italic True}",
    "underline": "{underline True}",
    "big":       "{size 55}",
    "small":     "{size 12}",
    "left":      "{align left}",
    "right":     "{align right}",
    "center":    "{align center}",
    "act":       "{color (255,110,104)}",
    "char":      "{color (255,252,103)}",
    "item":      "{color (104,113,255)}",
    "loc":       "{color (95,250,104)}",
    "num":       "{color (255,119,255)}",
    "quest":     "{color (96,253,255)}",
    "text":      "{color (0,197,199)}",
}

text_rich = """Title ([act]F[/act]) [bold]Confrontations[/bold]

If there is any [char]character[/char] in the current [loc]lo[bold]cat[/bold]ion[/loc], you must first [act]confront[/act] with her/him in order to access that [loc]location[/loc]. The [char]enemy[/char] can be defeated in one of three ways:
- 💪 [bold]grappling[/bold] - you have to land as many successful hits until the [char]opponent's[/char] health will drop to [num]123,98[/num].
- 🐍 [bold]incapacitate[/bold] - as above, try multiple times until you manage to defeat the opponent.

And there's always...
- 🏃 [bold]Escape[/bold] - well, sometimes that can be the best "[italic]way out[/italic]". This is treated as a random event: you may be able to escape unscathed, but you may also lose something while escaping 🏃 and it's not just about your honor.

The outcome of a given encounter is affected by the [item]equipment[/item], current [quest]quest[/quest] ([act]D[/act]).

[small]Morbi orci leo, [char]scelerisque[/char] [bold][act]a arcu ac[/act], viverra eleifend risus[/bold]. Nulla ultrices lorem ac rutrum tristique. Etiam sed posuere enim. Nullam sed sollicitudin odio. Mauris a semper ante. Duis nec mauris ipsum. Pellentesque euismod iaculis felis a venenatis. Maecenas tincidunt, erat non pretium eleifend, massa eros aliquam felis, eu dapibus tortor mauris eget tellus. Mauris dapibus fermentum enim nec lacinia. Nam sed velit lacinia, interdum massa sit amet, congue nibh.[/small]

([act]D[/act]) see chapter "[item][underline]Items[/underline][/item]".
"""

opening_tags = [f"[{key}]" for key in style_tags_dict.keys()]
closing_tags = [f"[/{key}]" for key in style_tags_dict.keys()]


def reformat_text(text_rich, style_tags_dict):
    for tag, styles in style_tags_dict.items():
        opening_tag = f"[{tag}]"
        closing_tag = f"[/{tag}]"
        opening_style, closing_style = styles
        text_rich = text_rich.replace(opening_tag, "{style}" + opening_style)
        text_rich = text_rich.replace(closing_tag, closing_style)  # + closing_style)
    return text_rich


def parse_text(text_rich: str, style_tags_dict: dict[str, str]) -> str:
    tags = style_tags_dict.keys()
    tags_pattern = "|".join(tags)
    # user regex to find all tags in the text_rich
    # opening_tag_pattern = r"\[(" + tags_pattern + r")\]"
    opening_tag_pattern = f"\\[(/?)({tags_pattern})\\]"
    print(opening_tag_pattern)
    print()
    current_tags: list[str] = []
    parsed_text: str = ""
    prev_tag_index = 0
    # iterate over all tags found in the text_rich
    for match in re.finditer(opening_tag_pattern, text_rich):
        # print(match.group(0))
        res = match.group()[1:-1]  # replace("[", "").replace("]", "")
        # print(res)
        before_tag = match.string[prev_tag_index:match.start()]
        # after_tag = match.string[match.end() - 1:]

        parsed_text += before_tag

        if "/" not in res:
            current_tags.append(res)
            # tag, _ = style_tags_dict[res]
            # parsed_text = f"{parse_text}{{style}}{tag}{after_tag}"
        else:
            res = res.replace("/", "")
            current_tags.remove(res)
            # before_tag = match.string[:match.start()]
            # after_tag = match.string[match.end():]
            # tag, _ = style_tags_dict[res]
        if current_tags:
            tag = "".join([style_tags_dict[tag] for tag in current_tags])
        else:
            tag = ""
        parsed_text += f"{{style}}{tag}"
        prev_tag_index = match.end()
    parsed_text += text_rich[prev_tag_index:]
    # print(match.group(1))
    return parsed_text


reformatted_text = parse_text(text_rich, style_tags_dict)

print(reformatted_text)

# reformatted_text = reformat_text(text_rich, style_tags_dict)
# print(reformatted_text)
# exit(1)
# Here's an example of how the chance of success against a opponent is calculated (e.g.: incapacitate 🐍):
#  - base probability - depends on the difficulty level (e.g. for level 1 👶 to 75%)
#  - Trait modifier - is the level of a given trait of your hero minus the level of this t
# rait of the character (e.g.: 50 - 60 = -10%)
#  - Item modifier - is the sum of the effect of all equipped [item]items[/] on this trait (e.g.: -10 + 30 = +20%)
#  - Chance of success - sum of values, and for the example above it is: 75% - 10% + 20% = 85%

# Of course when you have a 100% chance of success then you act, and when you have a 0% chance you run 🏃,
# but usually it will be an intermediate situation. It's up to you what you
# consider an acceptable level of risk.


def before_gui():  # add here the things to do before blitting gui elements
    screen.fill((32, 32, 32))
    # screen.blit(bck, (0, 0))  # blit background pic


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
# s["indent"] = 10
s["color"] = (0, 197, 199)
# stylized_text = Style.stylize(some_long_text, s)
stylized_text = Style.stylize(reformatted_text, s)
text, style = Style.split(stylized_text)
# print('\n"{}"'.format(style))
# print(text)
# print(style)
Style.set_default(s)

formatted_text = SFText(text=reformatted_text, font_path=os.path.join('.', 'resources'), style=s)

# let's replace the \n inserted in the str above. Note that you can manually place line breaks, but
#   we do remove them here as we want to illustrate auto line break only, for pedagogic purpose.
# some_long_text = some_long_text.replace("\n", " ")

# text = tp.Text.style_normal.insert_auto_breakline(some_long_text, 300)
# print(text)

# my_button = tp.Button(some_long_text, generate_surfaces=False)
my_button = tp.Text(reformatted_text, generate_surfaces=True)
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
