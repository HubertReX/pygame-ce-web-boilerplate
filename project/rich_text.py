import os
from pathlib import Path
import re
import pygame
import thorpy as tp
from sftext.sftext import SFText
from sftext.style import Style
# from utils.sftext import sftext
# from rich import print

pygame.init()

# screen resolution
W, H     = 1800, 900
# rich text canvas resolution
C_W, C_H = 1700, 700
screen = pygame.display.set_mode((W, H))
# screen background
bck = pygame.image.load(tp.fn("data/bck.jpg"))
bck = pygame.transform.smoothscale(bck, (W, H))  # load some background pic
# bck = pygame.transform.smoothscale(bck, (C_W, C_H))  # load some background pic

# emojis can be used in the rich text
# syntax:
# :angry: -> {style}{image angry}§{style}
EMOJIS_DICT: dict[str, str] = {
    "empty":   "emote00.png",
    "shocked": "emote01.png",
    "blessed": "emote02.png",
    "love":    "emote03.png",
    "angry":   "emote04.png",
    "indifferent":   "emote05.png",
    "happy":         "emote06.png",
    "wondering":     "emote07.png",
    "blink":   "emote08.png",
    "doubt":   "emote09.png",
    "frounce":   "emote10.png",
    "smile":   "emote11.png",
    "dreaming":   "emote12.png",
    "sad":   "emote13.png",
    "neutral":   "emote14.png",
    "dead":   "emote15.png",
    "miserable":   "emote16.png",
    "offended":   "emote17.png",
    "peaceful":   "emote18.png",
    "evil":   "emote19.png",
    "dots":   "emote20.png",
    "exclamation":   "emote21.png",
    "red_exclamation":   "emote22.png",
    "question":   "emote23.png",
    "human":   "emote24.png",
    "red_question":   "emote25.png",
    "broken_heart":   "emote26.png",
    "heart":   "emote27.png",
    "sleeping":   "emote28.png",
    "star":   "emote29.png",
    "cross":   "emote30.png",
    "fight":   "emote31_fight.png",
    "walk":   "emote32_walk.png",
}
# custom styles, syntax:
# [emphasis]this is important[/emphasis] -> {style}{bold True}{cast_shadow True}this is important{style}
# or
# [link WIKI_CHARACTERS_WOLF.md]bad wolf[/link] -> {style}{link WIKI_CHARACTERS_WOLF.md}bad wolf{style}
# or
# :angry: -> {style}{image angry}§{style}

STYLE_TAGS_DICT: dict[str, str] = {
    "shadow":    "{cast_shadow True}",
    "dark":      "{shadow_color (30,30,30)}",
    "light":     "{shadow_color (230,230,230)}",
    "bold":      "{bold True}",
    "italic":    "{italic True}",
    "underline": "{underline True}",
    "link( +[^\\]]+)?": "{underline True}{link LINK_URL}",
    "big":       "{size 42}",
    "small":     "{size 12}",
    "left":      "{align left}",
    "right":     "{align right}",
    "center":    "{align center}",
    "act":       "{color (255,110,104)}",
    # "char":      "{color (255,252,103,255)}",
    "char":      "{color (255,252,103)}",
    "item":      "{color (104,113,255)}",
    "loc":       "{color (95,250,104)}",
    "num":       "{color (255,119,255)}",
    "quest":     "{color (96,253,255)}",
    "text":      "{color (0,197,199)}",
}

EMOJIS_IMAGE_DICT: dict[str, pygame.Surface] = {}
for emoji in EMOJIS_DICT.keys():
    path = Path("assets") / "NinjaAdventure" / "Emote" / EMOJIS_DICT[emoji]
    image = pygame.image.load(path).convert_alpha()
    EMOJIS_IMAGE_DICT[emoji] = pygame.transform.scale2x(image)

test_rich_text = """[center][big][shadow][act]Title[/act][/shadow][/big][/center]

([act]F[/act]) [bold]Confrontations[/bold]  [link http://www.onet.pl]LINK[/link]

[shadow]If there is any [char]character[/char] :smile: in the current [loc]lo[bold]cat[/bold]ion[/loc], you [link PLEASE READ THE WIKI]must[/link] first [act]confront[/act] with her/him in order to access that [loc]location[/loc]. The [char]enemy[/char] can be defeated in one of three ways:[/shadow]

- :angry: [bold]grappling[/bold] - you have to land as many successful hits until the [char]opponent's[/char] health will drop to [num]123,98[/num].

- :blink: [bold]incapacitate[/bold] - as above, try multiple times until you manage to defeat the opponent.

And there's always...
- :doubt: [bold]Escape[/bold] - well, sometimes that can be the best "[italic]ITALIC way out[/italic]". This is treated as a random event: you may be able to escape unscathed, but you may also lose something while escaping and it's not just about your honor.

[shadow]SHADOW The outcome of a given encounter is affected by the [item]equipment[/item], current [quest]quest[/quest] ([act]D[/act]).[/shadow]
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789

[small]SMALL font Morbi orci leo, [char]scelerisque[/char] [bold][act]a arcu ac[/act], viverra eleifend risus[/bold]. Nulla ultrices lorem ac rutrum tristique. Etiam sed posuere enim. Nullam sed sollicitudin odio. Mauris a semper ante. Duis nec mauris ipsum. Pellentesque euismod iaculis felis a venenatis. Maecenas tincidunt, erat non pretium eleifend, massa eros aliquam felis, eu dapibus tortor mauris eget tellus. Mauris dapibus fermentum enim nec lacinia. Nam sed velit lacinia, interdum massa sit amet, congue nibh.[/small]

([act]D[/act]) see chapter "[item][link Open inventory by pressing (I).]Items[/link][/item]".
"""

# test_rich_text = """[center][shadow][act]Title[/act][/shadow][/center]
# ([act]F[/act]) [bold]Confrontations[/bold]  [link http://www.onet.pl]LINK[/link]
# [shadow]If there is any [char]character[/char] :smile: in the current [loc]lo[bold]cat[/bold]ion[/loc]:[/shadow]
# - :angry: [bold]grappling[/bold] the [char]opponent's[/char] health will drop to [num]123,98[/num].
# - :blink: [bold]incapacitate[/bold] - as above, try multiple times until you manage to defeat
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# And there's always...
# - :doubt: [bold]Escape[/bold] - well, sometimes that can be the best "[italic]ITALIC way out[/italic]".
# [shadow]SHADOW The outcome of a the [item]equipment[/item], current [quest]quest[/quest] ([act]D[/act]).[/shadow]
# ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789
# ([act]D[/act]) see chapter "[item][link Open inventory by pressing (I).]Items[/link][/item]".
# """


def parse_text(rich_text: str, style_tags_dict: dict[str, str], emojis_names: list[str]) -> str:
    """
    converts custom rich text to sftext format
    # [emphasis]this is important[/emphasis] -> {style}{bold True}{cast_shadow True}this is important{style}
    # or
    # [link WIKI_CHARACTERS_WOLF.md]bad wolf[/link] -> {style}{link WIKI_CHARACTERS_WOLF.md}bad wolf{style}
    # or
    # :angry: -> {style}{image angry}§{style}

    Args:
        text_rich (str): original rich text with custom tags (e.g. [bold]this is bold[/bold])
        style_tags_dict (dict[str, str]): maps custom tags to sftext style tags (e.g. "bold" -> "{bold True}")

    Returns:
        str: sftext formatted text
    """

    tags_list = style_tags_dict.keys()
    tags_pattern = "|".join(tags_list)
    opening_tag_pattern = f"\\[(/?)({tags_pattern})\\]"
    # print(opening_tag_pattern)
    # print()
    active_tags_list: list[str] = []
    parsed_text: str = ""
    prev_tag_index: int = 0
    active_tags: str = ""
    # iterate over all tags found in the text_rich
    for match in re.finditer(opening_tag_pattern, rich_text):
        url: str = ""
        res: str = match.group()[1:-1]  # replace("[", "").replace("]", "")
        # process link url
        if "link" in res:
            # opening tag
            if " " in res:
                split_pos = res.find(" ")
                url = res[split_pos + 1:]
                res = res[:split_pos]
            # needs to be exactly the same as in the style_tags_dict
            res = f"{res}( +[^\\]]+)?"
            # print(f"res: {res}", url)

        before_tag = match.string[prev_tag_index:match.start()]

        parsed_text += parse_emojis(before_tag, emojis_names, active_tags)

        if "/" not in res:
            active_tags_list.append(res)
        else:
            res = res.replace("/", "")
            # if "link" in res:
            #     print(f"res close: {res}")
            active_tags_list.remove(res)

        if active_tags_list:
            active_tags = "".join([style_tags_dict[tag] for tag in active_tags_list])
            if "LINK_URL" in active_tags:
                active_tags = active_tags.replace("LINK_URL", url)
        else:
            active_tags = ""
        parsed_text += f"{{style}}{active_tags}"
        prev_tag_index = match.end()

    parsed_text += parse_emojis(rich_text[prev_tag_index:], emojis_names, active_tags)

    return parsed_text


def parse_emojis(text: str, emojis_names: list[str], active_tags: str) -> str:
    """
    converts emojis tags to sftext format
    :angry: -> {style}{image angry}§{style}

    Args:
        text (str): text with emojis tags (e.g. :angry:), changed in place
        emojis_dict (list[str]): list of allowed emojis names
        active_tags (str): list active of sftext style tags to carry on

    Returns:
        str: sf text formatted text
    """
    for emoji in emojis_names:
        text = text.replace(f":{emoji}:", f"{{style}}{{image {emoji}}}§{{style}}{active_tags}")
    return text


def process_tooltip(link: str, show_tooltip: bool, tooltip_text: SFText) -> bool:
    """
    Process the tooltip based on the link and show_tooltip flag.

    Args:
        link (str): The link text clicked in the rich text.
        show_tooltip (bool): Flag indicating whether to show the tooltip or not.
        tooltip_text (SFText): The tooltip sftext object.

    Returns:
        bool: Flag indicating whether to show the tooltip or not.
    """
    # Add your implementation here
    if link:
        # print(f"link: {link}")
        new_text = formatted_rich_tooltip_text % link
        show_tooltip = True
        if new_text != tooltip_text.text:
            tooltip_text.set_text(new_text)
    else:
        show_tooltip = False

    return show_tooltip


reformatted_text = parse_text(test_rich_text, STYLE_TAGS_DICT, EMOJIS_DICT.keys())

# print()
# print(reformatted_text)


# tp.init(screen, tp.theme_classic)


pixel_art_style = Style().get_default("")
pixel_art_style["size"] = 20
pixel_art_style["font"] = "font_pixel.ttf"
# s["font"] = "Homespun.ttf"
pixel_art_style["separate_italic"] = None
pixel_art_style["separate_bold"] = None
pixel_art_style["separate_bolditalic"] = None
# pixel_art_style["indent"] = 10 # indent is actually not implemented in sftext
# default text color
pixel_art_style["color"] = (0, 197, 199)
# default text shadow color
pixel_art_style["shadow_color"] = (0, 32, 32)
# direction of the shadow offset, needs to be aligned with the font size
pixel_art_style["shadow_offset"] = (4, 4)
# Style.set_default(pixel_art_style)

# stylized_text = Style.stylize(reformatted_text, pixel_art_style)
# text, style = Style.split(stylized_text)
# print(text)
# print(style)

# helper canvas to render the rich text on
# it will determine the size of the rendered text with wrapping if needed
# alpha channel can be used to create a (semi)transparent background
canvas = pygame.Surface((C_W, C_H)).convert_alpha()
# canvas.fill((255, 255, 0, 255))
canvas.fill((30, 30, 30, 125))
# it can also be an image/texture
# canvas.blit(bck, (0, 0))  # blit background pic

formatted_text = SFText(text=reformatted_text,
                        images=EMOJIS_IMAGE_DICT,
                        screen=canvas,
                        # font_path=os.path.join(".", "sftext", "resources"),
                        font_path=str(Path(".") / "assets" / "fonts"),
                        style=pixel_art_style,
                        debug=False
                        )

pixel_art_style["size"] = 12
tooltip_canvas = pygame.Surface((1_000, 1_000)).convert_alpha()
# canvas.fill((255, 255, 0, 255))
tooltip_canvas.fill((30, 30, 30, 200))
# it can also be an image/texture
# canvas.blit(bck, (0, 0))  # blit background pic
tooltip_rich_text = """[act][shadow][bold]This is a tooltip[/bold][/shadow][/act]

[underline]%s"""

formatted_rich_tooltip_text = parse_text(tooltip_rich_text, STYLE_TAGS_DICT, EMOJIS_DICT.keys())
tooltip_text = SFText(text=formatted_rich_tooltip_text,
                      images=EMOJIS_IMAGE_DICT,
                      screen=tooltip_canvas,
                      # font_path=os.path.join(".", "sftext", "resources"),
                      font_path=str(Path(".") / "assets" / "fonts"),
                      style=pixel_art_style,
                      debug=False
                      )

tooltip_text.MARGIN_HORIZONTAL = 20
tooltip_text.MARGIN_VERTICAL = 10
tooltip_text.show_scrollbar = False

stylized_text = Style.stylize(formatted_rich_tooltip_text, pixel_art_style)
text, style = Style.split(stylized_text)
# print(len(text))
# print(text)
# print()
# print(style)

# my_button = tp.Text(reformatted_text, generate_surfaces=True)
# my_button.set_font_auto_multilines_width(700, refresh=False)
# print(my_button.get_text_size())
# print(my_button.get_value())
# Arbitrarily choosing "#" as the tag here, but you are free to set whatever you like.
# my_button.set_font_color([255, 255, 255])
# my_button.set_font_rich_text_tag("#")  # setting a tag automatically enable rich text (disabled by default)
# my_button.set_style_attr("font_align", "l")  # font_align is either "l", "r" or "c" (left, right and center)
# my_button.center_on(screen)
# my_ui_elements = tp.Group([my_button])
# updater = my_ui_elements.get_updater()

# m = tp.Loop(element=my_button)
clock = pygame.time.Clock()
screen_offset = (50, 50)
# in order to detect mouse hover over a link,
# sftext object needs to know it's offset relative to the main screen
formatted_text.screen_offset = screen_offset

show_tooltip: bool = False
is_running = True
while is_running:
    clock.tick(60)
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            is_running = False
        if e.type == pygame.KEYDOWN:
            formatted_text.on_key_press(e)
            if e.key in [pygame.K_q, pygame.K_ESCAPE]:
                is_running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            link = formatted_text.on_mouse_button(e)
            show_tooltip = process_tooltip(link, show_tooltip, tooltip_text)

        # comment out to disable hover effect
        # it will still be possible to click on the link
        link = formatted_text.on_mouse_move(pygame.mouse.get_pos())
        show_tooltip = process_tooltip(link, show_tooltip, tooltip_text)
    # m.update(before_gui)
    # before_gui()
    screen.fill((30, 30, 30))
    screen.blit(bck, (0, 0))  # blit background pic

    # updater.update(events=events)
    # screen.blit(my_button.surface, (0, 0))
    formatted_text.on_update()
    screen.blit(canvas, screen_offset)
    if show_tooltip:
        # tooltip_text.on_update()
        # print(tooltip_canvas.get_size())
        screen.blit(tooltip_text.screen, pygame.mouse.get_pos())
    pygame.display.flip()

pygame.quit()
