from pathlib import Path
import re
from rich.markup import escape
from rich import print
import pygame
import thorpy as tp
from settings import EMOJIS_DICT, EMOJIS_PATH, FONTS_PATH, HEIGHT, HUD_DIR, HUD_ICONS, STYLE_TAGS_DICT, WIDTH, vec
from sftext.sftext import SFText
from sftext.style import Style
# from utils.sftext import sftext
# from rich import print


class RichPanel():

    # custom styles, syntax:
    # [emphasis]this is important[/emphasis] -> {style}{bold True}{cast_shadow True}this is important{style}
    # or
    # [link WIKI_CHARACTERS_WOLF.md]bad wolf[/link] -> {style}{link WIKI_CHARACTERS_WOLF.md}bad wolf{style}
    # or
    # :angry: -> {style}{image angry}§{style}

    def __init__(
            self,
            rich_text: str,
            tooltip_rich_text: str,
            background_canvas: pygame.Surface,
            screen_offset: tuple[int, int],
            default_font_size: int = 20,
            default_font_color: tuple[int, int, int] = (0, 197, 199),
            shadow_color: tuple[int, int, int] = (130, 32, 32),
            shadow_offset: tuple[int, int] = (4, 4),
            border_size: tuple[int, int] = (0, 0),
            margin_horizontal: int = 0,
            margin_vertical: int = 0,
            show_scrollbar: bool = True,
            is_tooltip_available: bool = True,
            tooltip_canvas: pygame.Surface | None = None,
            tooltip_font_size: int = 12,
            tooltip_offset: tuple[int, int] = (0, 0),
            debug: bool = False,
    ) -> None:
        """
        `RichPanel` is interactive rectangle rendered with custom rich formatted text.
        It contains 2 `sftext` helper objects (for main text and for tooltips).
        Rich text can contain mixture of following formatting tags:
            - font faces
            - font sizes
            - font colors
            - bold/italic/underline
            - text background
            - links with custom text shown in tooltip when hovered or clicked
            - emojis (actually any images) mixed in between the text
            - text alignment
            - text margin

        Panel can be used as static texture (Surface) by calling `get_panel()`
        or interactively to scroll text (up, down, home, end) and show tooltips
        by passing events to `on_key_press()`, `on_mouse_move()`, `on_mouse_button()`
        and calling `on_update()`, `get_tooltip()`

        Args:
            rich_text (str): The main rich text content with tags to be displayed in the panel.
            tooltip_rich_text (str): The rich text content with tags to be displayed in the
            tooltip when hovered or clicked. A `'%s'`placeholder will be replaced with link text.
            background_canvas (pygame.Surface): The surface on which the rich text will be rendered.
            If too narrow, text will be wrapped, but's its buggy.
            screen_offset (tuple[int, int]): The offset of the rich text panel relative to
            the main screen (required to handel absolute mouse position over Links).
            default_font_size (int, optional): The default font size if no style applied. Defaults to `20`.
            default_font_color (tuple[int, int, int], optional): The default font color if
            no style applied. Defaults to `(0, 197, 199)`.
            shadow_color (tuple[int, int, int], optional): The color of the shadow. Defaults to `(130, 32, 32)`.
            shadow_offset (tuple[int, int], optional): The offset of the shadow. Defaults to `(4, 4)`.
            margin_horizontal (int, optional): The horizontal margin to be added from both sides. Defaults to `0`.
            margin_vertical (int, optional): The vertical margin to be added at the top and bottom. Defaults to `0`.
            show_scrollbar (bool, optional): Whether to show a simplified text based vertical scrollbar panel
            on the right. It won't be shown if text fits on canvas and there is no need for scrolling.
            Defaults to `True` on the panel and `False` on the tooltip.
            is_tooltip_available (bool, optional): Whether a link was activated and tooltip is available.
            Defaults to `False`.
            tooltip_canvas (pygame.Surface | None, optional): The surface on which the tooltip will be rendered.
            It can be very large, but then it will be rescaled to fit tooltip text. If `None`,
            default grey with semitransparent one will be used. Defaults to `None`.
            tooltip_font_size (int, optional): The font size for the tooltip text. Defaults to `12`.
            tooltip_offset (tuple[int, int]): The position offset of the tooltip panel. Defaults to `(0, 0)`.
            debug (bool, optional): Whether to enable debug mode sftext. Defaults to `False`.
        """

        self.EMOJIS_IMAGE_DICT: dict[str, pygame.Surface] = {}
        for emoji in EMOJIS_DICT.keys():
            path = EMOJIS_PATH / EMOJIS_DICT[emoji]
            image = pygame.image.load(path).convert_alpha()
            self.EMOJIS_IMAGE_DICT[emoji] = pygame.transform.scale2x(image)

        for emoji in HUD_ICONS.keys():
            path = HUD_DIR / HUD_ICONS[emoji]
            image = pygame.image.load(path).convert_alpha()
            self.EMOJIS_IMAGE_DICT[emoji] = pygame.transform.scale(image, (32, 32))

        self.rich_text = rich_text
        self.processed_text = self._parse_text(self.rich_text)

        self.pixel_art_style = Style().get_default("")
        self.pixel_art_style["size"] = default_font_size
        self.pixel_art_style["font"] = "font_pixel.ttf"
        # s["font"] = "Homespun.ttf"
        self.pixel_art_style["separate_italic"] = None
        self.pixel_art_style["separate_bold"] = None
        self.pixel_art_style["separate_bolditalic"] = None
        # pixel_art_style["indent"] = 10 # indent is actually not implemented in sftext
        # default text color
        self.pixel_art_style["color"] = default_font_color
        # default text shadow color
        self.pixel_art_style["shadow_color"] = shadow_color
        # direction of the shadow offset, needs to be aligned with the font size
        self.pixel_art_style["shadow_offset"] = shadow_offset

        self.background_canvas = background_canvas
        self.border_size = border_size
        self.background_canvas_size = self.background_canvas.get_size()

        self.text_canvas = pygame.Surface(
            (self.background_canvas_size[0] - self.border_size[0] * 2,
             self.background_canvas_size[1] - self.border_size[1] * 2)).convert_alpha()
        self.text_canvas.fill((0, 0, 0, 0))

        self.debug = debug
        self.formatted_text = SFText(
            text=self.processed_text,
            images=self.EMOJIS_IMAGE_DICT,
            canvas=self.text_canvas,
            # font_path=os.path.join(".", "sftext", "resources"),
            font_path=str(FONTS_PATH),
            style=self.pixel_art_style,
            debug=self.debug
        )
        # in order to detect mouse hover over a link,
        # sftext object needs to know it's offset relative to the main screen
        self.formatted_text.canvas_offset = (
            screen_offset[0] + self.border_size[0],
            screen_offset[1] + self.border_size[0])
        self.formatted_text.show_scrollbar = show_scrollbar
        self.formatted_text.MARGIN_HORIZONTAL = margin_horizontal
        self.formatted_text.MARGIN_VERTICAL = margin_vertical

        self.is_tooltip_available: bool = is_tooltip_available
        self.tooltip_style = self.pixel_art_style.copy()
        self.tooltip_style["size"] = tooltip_font_size
        self.tooltip_offset = tooltip_offset

        if tooltip_canvas:
            self.tooltip_canvas = tooltip_canvas
        else:
            self.tooltip_canvas = pygame.Surface((1_000, 1_000)).convert_alpha()
            # self.tooltip_canvas.fill((255, 255, 0, 255))
            self.tooltip_canvas.fill((30, 30, 30, 200))
            # it can also be an image/texture
            # self.tooltip_canvas.blit(bck, (0, 0))  # blit background pic

        self.tooltip_rich_text = tooltip_rich_text

        self.formatted_rich_tooltip_text = self._parse_text(self.tooltip_rich_text)
        self.tooltip_text = SFText(
            text=self.formatted_rich_tooltip_text,
            images=self.EMOJIS_IMAGE_DICT,
            canvas=self.tooltip_canvas,
            # font_path=os.path.join(".", "sftext", "resources"),
            font_path=str(FONTS_PATH),
            style=self.tooltip_style,
            debug=self.debug
        )
        self.tooltip_rect: pygame.Rect = self.tooltip_text.canvas.get_rect()

        self.tooltip_text.MARGIN_HORIZONTAL = 20
        self.tooltip_text.MARGIN_VERTICAL = 10
        # most commonly tooltip won't need scrollbar
        self.tooltip_text.show_scrollbar = False

    def get_panel(self) -> pygame.Surface:
        """
        Recommended way of accessing final panel do be blitted on the screen.
        Do not use canvas passed to the constructor, since it might reference a wrong object.

        Returns:
            pygame.Surface: the rich panel himself
        """

        text_canvas = self.formatted_text.canvas
        panel = self.background_canvas.copy()
        panel.blit(text_canvas, self.border_size)
        return panel

    def get_tooltip(self) -> tuple[pygame.Surface, pygame.Rect]:
        """
        Recommended way of accessing tooltip do be blitted on the screen.
        Do not use canvas passed to the constructor, since it might reference a wrong object.
        Before using it, make sure to call `on_mouse_button()` and/or `on_mouse_move()`
        and check `is_tooltip_available` flag.


        Returns:
            pygame.Surface: the tooltip itself
        """

        return self.tooltip_text.canvas, self.tooltip_rect

    def on_key_press(self, event: pygame.Event) -> None:
        """
        To be called in the main game loop.

        Handles vertical panel **scrolling** when `up arrow`, `down arrow`, `Page Up`, `Page Down`, `Home` or `End`
        was pressed.
        It won't have any effect if text fits on the canvas.

        Args:
            event (pygame.Event): event element form pygame.event.get() list
        """

        self.formatted_text.on_key_press(event)

    def on_mouse_button(self, event: pygame.Event) -> None:
        """
        To be called in the main game loop.

        Handles **scrolling** and **links** clicking.

        1. Vertical panel scrolling will be applied when mouse wheel goes `up` or `down`.
        It won't scroll if text fits on the canvas.

        2. When left mouse button is clicked on a link, a tooltip will be created.
        Check `is_tooltip_available` flag it that was a case.

        Args:
            event (pygame.Event): event element form pygame.event.get() list
        """

        link = self.formatted_text.on_mouse_button(event)
        self._process_tooltip(link)

    def on_mouse_move(self, mouse_pos: tuple[int, int] | None = None) -> None:
        """
        To be called in the main game loop.

        When mouse hovers over a link, a tooltip will be created.
        Check `is_tooltip_available` flag it that was a case.
        For this to work correctly, a proper `screen_offset` must be set.
        It is the offset of the rich text panel relative to the main screen.

        Ff `mouse_pos` is not provided, `pygame.mouse.get_pos()` will be called.

        If hovering is not required, simply do not call this method.


        Args:
            mouse_pos (tuple[int, int] | None): tuple of `x`, `y` mouse absolute position on the main screen
        """

        if not mouse_pos:
            mouse_pos = pygame.mouse.get_pos()

        link = self.formatted_text.on_mouse_move(mouse_pos)
        self._process_tooltip(link)

    def on_update(self) -> None:
        """
        To be called in the main game loop.

        The panel will be rendered again only if text has changed or the content has been scrolled.
        """

        self.formatted_text.on_update()

    @staticmethod
    def _parse_text(rich_text: str) -> str:
        """
        converts custom rich text to sftext format
        # [emphasis]this is important[/emphasis] -> {style}{bold True}{cast_shadow True}this is important{style}
        # or
        # [link WIKI_CHARACTERS_WOLF.md]bad wolf[/link] -> {style}{link WIKI_CHARACTERS_WOLF.md}bad wolf{style}
        # or
        # :angry: -> {style}{image angry}§{style}

        Args:
            text_rich (str): original rich text with custom tags (e.g. [bold]this is bold[/bold])

        Returns:
            str: sftext formatted text
        """

        tags_list = STYLE_TAGS_DICT.keys()
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

            parsed_text += RichPanel._parse_emojis(before_tag, active_tags)

            if "/" not in res:
                active_tags_list.append(res)
            else:
                res = res.replace("/", "")
                # if "link" in res:
                #     print(f"res close: {res}")
                if res not in active_tags_list:
                    print(
                        f"[red]ERROR[/] parsing '{escape(rich_text)}' string failed - closing tag has no corresponding open tag '{escape(res)}'")
                else:
                    active_tags_list.remove(res)

            if active_tags_list:
                active_tags = "".join([STYLE_TAGS_DICT[tag] for tag in active_tags_list])
                if "LINK_URL" in active_tags:
                    active_tags = active_tags.replace("LINK_URL", url)
            else:
                active_tags = ""
            parsed_text += f"{{style}}{active_tags}"
            prev_tag_index = match.end()

        parsed_text += RichPanel._parse_emojis(rich_text[prev_tag_index:], active_tags)

        return parsed_text

    @staticmethod
    def _parse_emojis(text: str, active_tags: str) -> str:
        """
        converts emojis tags to sftext format
        :angry: -> {style}{image angry}§{style}

        Args:
            text (str): text with emojis tags (e.g. :angry:), changed in place
            active_tags (str): list active of sftext style tags to carry on

        Returns:
            str: sf text formatted text
        """
        for emoji in EMOJIS_DICT.keys():
            text = text.replace(f":{emoji}:", f"{{style}}{{image {emoji}}}§{{style}}{active_tags}")
        return text

    def _process_tooltip(self, link: str) -> None:
        """
        Process the tooltip based on the provided `link` text
        and sets the flag `show_tooltip` if there is a tooltip to be shown

        Args:
            link (str): The link text clicked in the rich text.

        Returns:
            None
        """

        if link:
            # print(f"link: {link}")
            new_text = self.formatted_rich_tooltip_text % link
            self.is_tooltip_available = True
            if new_text != self.tooltip_text.text:
                self.tooltip_text.set_text(new_text, resize=True)
            self._process_tooltip_rect()
        else:
            self.is_tooltip_available = False

    def _process_tooltip_rect(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        # cursor_size = self.game.cursor_img.get_size()
        mouse_x: int = mouse_pos[0] + self.tooltip_offset[0] // 2
        mouse_y: int  = mouse_pos[1] + self.tooltip_offset[1]
        tooltip_canvas = self.tooltip_text.canvas
        if mouse_x + tooltip_canvas.get_width() > WIDTH:
            mouse_x = WIDTH - tooltip_canvas.get_width()

        if mouse_y + tooltip_canvas.get_height() > HEIGHT:
            mouse_y = HEIGHT - tooltip_canvas.get_height()
        self.tooltip_rect.topleft = (mouse_x, mouse_y)

    def set_text(self, rich_text: str, resize: bool = False) -> None:
        """
        Recommended way to update rich text after the panel has been created.
        Changing `rich_text` property of the panel won't work.
        Text will be parsed again and panel will be rendered
        so there is not need to call `on_update()` (it won't bother either).
        The `is_tooltip_available` flag will be set to `False`.

        Args:
            rich_text (str): the new rich text
            resize (bool, optional): Whether to resize panel canvas. Defaults to `False`.
        """

        if rich_text != self.rich_text:
            self.rich_text = rich_text
            self.processed_text = self._parse_text(self.rich_text)
            self.formatted_text.set_text(self.processed_text, resize=resize)
        self.is_tooltip_available = False


# def before_gui() -> None:
#     """ add here the things to do before blitting gui elements"""
#     pass
#     # screen.blit(bck, (0, 0))  # blit background pic


def main() -> None:
    pygame.init()

    # screen resolution
    W, H     = 1800, 900  # 1800, 900
    # rich panel canvas resolution
    C_W, C_H = W - 100, H - 200  # 1700, 700

    screen = pygame.display.set_mode((W, H))
    # screen or panel background
    bck = pygame.image.load(r"assets\NinjaAdventure\HUD\dark_panel_1700x900.png")
    # bck = pygame.transform.smoothscale(bck, (W, H))  # load some background pic
    bck = pygame.transform.smoothscale(bck, (C_W, C_H))  # load some background pic

    # rich_text_file = Path("rich_text_sample.md")
    rich_text_file = Path(r"assets\dialogs\rich_text_sample.md")
    test_rich_text = rich_text_file.read_text()

    # helper canvas to render the rich text on
    # it will determine the size of the rendered text with wrapping if needed
    # alpha channel can be used to create a (semi)transparent background
    canvas = pygame.Surface((C_W, C_H)).convert_alpha()
    # canvas.fill((255, 255, 0, 255))
    # canvas.fill((30, 30, 30, 125))
    canvas.blit(pygame.transform.scale(bck, canvas.get_size()), (0, 0))

    screen_offset = (50, 50)

    tooltip_rich_text = """[act][shadow][bold]This is a tooltip[/bold][/shadow][/act]\n\n[underline]%s[/[underline]]"""
    rich_panel = RichPanel(test_rich_text, tooltip_rich_text, bck, screen_offset)

    # print()
    # print(reformatted_text)

    tp.init(screen, tp.theme_game1)

    # Style.set_default(pixel_art_style)

    # stylized_text = Style.stylize(reformatted_text, pixel_art_style)
    # text, style = Style.split(stylized_text)
    # print(text)
    # print(style)

    # it can also be an image/texture
    # canvas.blit(bck, (0, 0))  # blit background pic

    # stylized_text = Style.stylize(formatted_rich_tooltip_text, pixel_art_style)
    # text, style = Style.split(stylized_text)
    # print(len(text))
    # print(text)
    # print()
    # print(style)

    close_button = tp.Button("Close", )  # , generate_surfaces=True)
    close_button.set_center(W // 2, H - 200)
    # my_button.set_font_auto_multilines_width(700, refresh=False)
    # print(my_button.get_text_size())
    # print(my_button.get_value())
    # Arbitrarily choosing "#" as the tag here, but you are free to set whatever you like.
    # my_button.set_font_color([255, 255, 255])
    # my_button.set_font_rich_text_tag("#")  # setting a tag automatically enable rich text (disabled by default)
    # my_button.set_style_attr("font_align", "l")  # font_align is either "l", "r" or "c" (left, right and center)
    # my_button.center_on(screen)

    tp_elements = tp.Group([close_button],)
    tp_elements.set_center(W // 2, H - 200)
    tp_updater = tp_elements.get_updater()

    # tp_loop = tp.Loop(element=close_button)
    clock = pygame.time.Clock()

    is_running = True
    while is_running:
        clock.tick(60)
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                is_running = False
            if e.type == pygame.KEYDOWN:
                rich_panel.on_key_press(e)
                if e.key in [pygame.K_q, pygame.K_ESCAPE]:
                    is_running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                rich_panel.on_mouse_button(e)
                # show_tooltip = process_tooltip(link, formatted_rich_tooltip_text, show_tooltip, tooltip_text)

        # comment out to disable hover effect
        # it will still be possible to click on the link
        rich_panel.on_mouse_move(pygame.mouse.get_pos())
        # show_tooltip = process_tooltip(link, formatted_rich_tooltip_text, show_tooltip, tooltip_text)
        # before_gui()
        screen.fill((60, 90, 30))
        # close_button.set_center(100, 100)

        # screen.blit(bck, (0, 0))  # blit background pic

        rich_panel.on_update()
        screen.blit(rich_panel.get_panel(), screen_offset)
        tp_updater.update(events=events)
        # tp_loop.update(before_gui)

        # screen.blit(close_button.surface, (W // 2, H - 200))
        # screen.blit(close_button.surface, (0, 0))
        if rich_panel.is_tooltip_available:
            # tooltip_text.on_update()
            # print(tooltip_canvas.get_size())
            # screen.blit(tooltip_text.canvas, pygame.mouse.get_pos())
            # screen.blit(rich_panel.get_tooltip(), pygame.mouse.get_pos())
            screen.blit(*rich_panel.get_tooltip())
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
