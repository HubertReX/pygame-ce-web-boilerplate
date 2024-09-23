# ---------------------------------------------------------
# sftext - Scrollable Formatted Text for pygame
# Copyright (c) 2016 Lucas de Morais Siqueira
# Distributed under the GNU Lesser General Public License version 3.
#
#       \ vvvvvvvvvvvvvvvvvvvvvvvvv /
#     >>> SCROLLABLE FORMATTED TEXT <<<
#       / ^^^^^^^^^^^^^^^^^^^^^^^^^ \
#
#     Support by using, forking, reporting issues and giving feedback:
#     https://https://github.com/LukeMS/sftext/
#
#     Lucas de Morais Siqueira (aka LukeMS)
#     lucas.morais.siqueira@gmail.com
#
#    This file is part of sftext.
#
#    sftext is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    sftext is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with sftext. If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------------------------------
#  extended by Hubert Nafalski, July 2024
# ---------------------------------------------------------

from rich import print
from typing import Any
import pygame

from settings import TILE_SIZE

# from pygame.locals import *

from . import resources
# import resources
from .style import Style


class SFText():
    def __init__(
        self,
        text: str,
        images: dict[str, pygame.Surface] = {},
        canvas: pygame.Surface = pygame.Surface((TILE_SIZE, TILE_SIZE)),
        font_path: str = ".",
        style: dict[str, Any] = {},
        debug: bool = False,
    ):
        self.debug = debug
        self.text: str = text
        self.parsed: list[dict[str, Any]] = []
        self.links: dict[str, dict[str, Any]] = {}
        # self.last_link_name: str = ""
        # self.last_link_tooltip: pygame.Surface | None = None
        self.needs_update: bool = True
        # if in general we want to show the scrollbar
        self.show_scrollbar: bool = True
        # if text is longer then
        self.needs_scrolling: bool = False

        if images:
            self.images = images
        else:
            self.images = {}

        self.fonts = resources.Fonts(path=font_path)

        if style:
            self.default_style = style
        else:
            self.default_style = Style.default_style

        # narrow down the space where images will be placed
        self.IMAGE_WIDTH_FACTOR =  0.4
        self.MARGIN_HORIZONTAL = 60
        self.MARGIN_VERTICAL = 20  # -self.default_style["size"]

        # position of the text on the canvas in percentage (0.0 => top - 1.0 => bottom)
        self.percentage: float = 0.0

        if not canvas:
            self.canvas = pygame.display.get_surface()
        else:
            self.canvas = canvas
        self.canvas_offset = (0, 0)
        self.canvas_rect = self.canvas.get_rect()

        self.bg = self.canvas.copy()
        self.alpha = self.bg.get_at((0, 0))[3]

        self.parse_text()

    def set_text(self, text: str, resize: bool = False) -> None:
        if self.debug:
            print("Setting new text", text)

        self.revert_to_original_size()
        self.text = text
        self.parse_text()
        self.needs_update = True
        if resize:
            self.resize_to_fit_text()
            self.set_scroll_limits()
        self.on_update()

    def resize_to_fit_text(self) -> None:
        # print(self.bg.get_size())
        self.bg = pygame.transform.scale(
            self.bg,
            (self.max_x + (self.MARGIN_HORIZONTAL * 2),
             self.max_y + (self.MARGIN_VERTICAL * 3)))
        # pygame.transform.scale(self.canvas, (self.max_x + 10, self.max_y + 10))
        self.canvas = self.bg.copy()
        # print(self.max_x, self.max_y, self.canvas.get_size())

        new_size = self.canvas.get_size()
        offset = self.canvas_rect.height - new_size[1]
        for p in self.parsed:
            p["rect"].move_ip(0, -offset)

    def revert_to_original_size(self) -> None:
        self.canvas = pygame.transform.scale(self.canvas, (self.canvas_rect.width, self.canvas_rect.height))
        self.bg = self.canvas.copy()

    def set_font(self, obj: dict[str, Any]) -> None:
        if obj["bold"] and obj["italic"] and obj["separate_bolditalic"]:
            obj["font_obj"] = self.fonts.load(obj["separate_bolditalic"], obj["size"])
        elif obj["separate_bold"] and obj["bold"]:
            obj["font_obj"] = self.fonts.load(obj["separate_bold"], obj["size"])
        elif obj["separate_italic"] and obj["italic"]:
            obj["font_obj"] = self.fonts.load(obj["separate_italic"], obj["size"])
        else:
            obj["font_obj"] = self.fonts.load(obj["font"], obj["size"])

    def parse_text(self) -> None:
        self.parsed = []
        scr_w = self.canvas_rect.width

        # self.default_style = Style.default_style
        self.default_style["font_obj"] = self.fonts.load(self.default_style["font"], self.default_style["size"])
        # self.default_style["w"], self.default_style["h"] = (self.default_style["font_obj"].size("Fg"))
        self.default_style["w"] = self.default_style["font_obj"].size(" ")[0]
        self.default_style["h"] = self.default_style["font_obj"].size("Fg")[1] * 1.5  # get_linesize() * 1.5

        max_x = 0
        y = 0
        for line in self.text.splitlines():
            x = 0
            for style in line.split("{style}"):

                text, styled_txt = Style.split(style)

                self.set_font(styled_txt)
                font = styled_txt["font_obj"]

                # w, h = styled_txt["w"], styled_txt["h"] = font.size("Fg")
                w = font.size(" ")[0]
                styled_txt["w"] = w
                # h = font.get_linesize()
                h = font.size("Fg")[1] * 1.5
                styled_txt["h"] = h
                # determine the amount of space needed to render text

                wraps = self.wrap_text(text, scr_w, x, styled_txt)

                for wrap in wraps:
                    text_size = font.size(wrap["text"])

                    # § is place holder for images/emojis
                    if wrap["text"] == "§":
                        # print(wrap["image"], "§", text_size[0])
                        text_size = (int(text_size[0] * self.IMAGE_WIDTH_FACTOR), text_size[1])
                        # print(wrap["image"], "§", text_size[0])
                    rect = pygame.Rect((0, 0), (text_size[0], text_size[1]))

                    if (x + wrap["w1"] + self.MARGIN_HORIZONTAL) > scr_w:
                        x = 0
                        y += wrap["h"]
                    if len(wraps) == 1 and wrap["align"] == "center":
                        rect.midtop = (
                            self.canvas_rect.centerx,
                            self.canvas_rect.bottom + y + self.MARGIN_VERTICAL)
                    else:
                        rect.topleft = (
                            x + self.MARGIN_HORIZONTAL,
                            self.canvas_rect.bottom + y + self.MARGIN_VERTICAL)
                    # if self.text.splitlines().index(line) == 0:
                    #     print(rect.move(0, self.y).topleft, rect.size)

                    wrap["rect"] = rect
                    wrap["x"] = x
                    wrap["y"] = y
                    if self.debug:
                        print("\n{}: {},".format("x", wrap["x"]), end="")
                        print("{}: {},".format("y", wrap["y"]), end="")
                        print("{}: {},".format("w", wrap["w"]), end="")
                        print("{}: {}".format("h", wrap["h"]))
                        print(wrap["text"])
                    self.parsed.append(wrap)

                    x += wrap["w1"]
                    max_x = max(max_x, x)
            y += wrap["h"]
        self.max_x = max_x
        self.max_y = y
        # print("max_x", self.max_x)
        # print("max_y", self.max_y)
        # exit()
        # print("done parsing")
        self.set_scroll_limits()

    def set_scroll_limits(self) -> None:
        # self.start_y = 0 - self.canvas_rect.h + self.default_style["h"]
        size = self.canvas.get_size()
        self.start_y = self.MARGIN_VERTICAL - size[1]

        self.y = int(self.start_y)

        # self.end_y = (-sum(p["h"] for p in self.parsed if p["x"] == 0) - self.default_style["h"] * 2)
        self.end_y = -self.max_y - (self.MARGIN_HORIZONTAL * 2)  # - sum(p["h"] for p in self.parsed if p["x"] == 0)
        # print("y", self.y, self.start_y, self.end_y)

    def wrap_text(self, text: str, width: int, _x: int, styled_txt: dict[str, Any]) -> list[dict[str, Any]]:
        style = dict(styled_txt)
        x = int(_x)
        wrapped: list[dict[str, Any]] = []
        size = style["font_obj"].size
        c_width = style["w"]

        # print(size(text))
        # print(width)
        if size(text)[0] <= (width - c_width * 6 - x):
            # print("fits")
            style["text"] = text
            style["w1"] = size(text)[0]
            if style["text"] == "§":
                style["w1"] = int(style["w1"] * self.IMAGE_WIDTH_FACTOR)

            wrapped.append(style)

            return wrapped
        else:
            # print("doesn't fit")
            # print(text)
            wrapped_list: list[str] = [text]
            guessed_length = ((width - c_width * 6 - x) // c_width)
            all_fit = False
            all_fit_iter = 1
            while not all_fit:
                #########
                # DEBUG #
                if self.debug:
                    print("all_fit iterations: {}".format(all_fit_iter), guessed_length * 5)
                if all_fit_iter >= guessed_length * 5:
                    print(
                        f"[red]ERROR![/] SFTEXT wrap_text FAILED: can't fit text '{text}' - breaking to prevent infinite loop")

                    # exit()
                    break
                # DEBUG #
                #########
                for i in range(len(wrapped_list)):
                    # print("for i in range(len(wrapped_list))")
                    fit = size(wrapped_list[i])[0] < width - c_width * 6 - x
                    # print(width - c_width * 6 - x)
                    iter_length = int(guessed_length)
                    # print(iter_length)
                    fit_iter = 0
                    while not fit:
                        #########
                        # DEBUG #
                        fit_iter += 1
                        if self.debug:
                            print("fit iterations: {}, iter_length: {}".format(fit_iter, iter_length))
                        # fit failed - break to prevent infinite loop
                        if fit_iter >= guessed_length * 5:
                            print(
                                f"[red]ERROR![/] SFTEXT wrap_text FAILED: can't fit text '{text}' - breaking to prevent infinite loop")
                            # exit()
                            break
                        # DEBUG #
                        #########
                        if guessed_length <= 2 or iter_length <= 2:
                            # print("if guessed_length <= 2")
                            x = 0
                            guessed_length = ((width - c_width * 6 - x) // c_width)
                            iter_length = int(guessed_length)
                            continue
                        guess = wrapped_list[i][:iter_length]
                        # print("while not fit: "{}"".format(guess))
                        if guess[-1:] not in [" ", ",", ".", "-", "\n"]:
                            # print("if guess[-1:] not in:")
                            iter_length -= 1
                        else:
                            if size(guess)[0] < width - c_width * 6 - x:
                                remains = wrapped_list[i][iter_length:]
                                wrapped_list[i] = guess
                                wrapped_list.append(remains)
                                fit = True
                            else:
                                iter_length -= 1
                    all_fit_iter += 1
                    # print("Cut point: {}".format(iter_length))
                    # print("Guess: ({})"{}"".format(type(guess), guess))
                    # print("Remains: "{}"".format(remains))
                    # print("[{}]fit? {}".format(i, fit))
                status = True
                for i in range(len(wrapped_list)):
                    if size(wrapped_list[i])[0] >= width:
                        status = False
                all_fit = status

            for i in range(len(wrapped_list)):
                # print(""{}"".format(wrapped_list[i]))
                style["text"] = wrapped_list[i]
                style["w1"] = size(wrapped_list[i])[0]
                if style["text"] == "§":
                    style["w1"] = int(style["w1"] * self.IMAGE_WIDTH_FACTOR)
                wrapped.append(dict(style))

            return wrapped

    def on_update(self) -> None:
        if not self.needs_update:
            return

        self.clear()
        self.links = {}

        if self.show_scrollbar:
            font = self.fonts.load(self.default_style["font"], self.default_style["size"])
            top = self.MARGIN_VERTICAL
            bottom = self.canvas_rect.height - self.default_style["h"] - self.MARGIN_VERTICAL
            bar_size = self.default_style["h"]
            size = bottom - top - (bar_size * 2)
            scrollbar_pos = int(top + bar_size + (size * self.percentage))
            self.needs_scrolling = bottom < self.max_y
            # print(top, bottom, self.max_y, bar_size, size, self.percentage, scrollbar_pos)
            # show scrollbar only if text is bigger than canvas
            if self.needs_scrolling:
                if self.percentage > 0.0:
                    self.canvas.blit(font.render("/\\", True, self.default_style["color"]),
                                     (self.canvas_rect.width - self.default_style["w"] * 2, top))
                self.canvas.blit(font.render("|", True, self.default_style["color"]),
                                 (self.canvas_rect.width - self.default_style["w"] * 2, scrollbar_pos))

                if self.percentage < 1.0:
                    self.canvas.blit(font.render("\\/", True, self.default_style["color"]),
                                     (self.canvas_rect.width - self.default_style["w"] * 2, bottom))

        # for i, p in enumerate(self.parsed[:]):
        # print(self.parsed[0].keys())
        for p in self.parsed:
            rect = p["rect"].move(0, self.y)

            if not isinstance(p["text"], pygame.Surface):
                p["font_obj"].set_bold(False)
                p["font_obj"].set_italic(False)

                if p["bold"] and p["italic"] and not p["separate_bolditalic"]:
                    if self.debug:
                        print("separate_bolditalic", p["text"])
                    p["font_obj"].set_bold(p["bold"])
                    p["font_obj"].set_italic(p["italic"])
                elif not p["separate_bold"] and p["bold"]:
                    if self.debug:
                        print("separate_italic", p["text"])
                    p["font_obj"].set_bold(p["bold"])
                elif not p["separate_italic"] and p["italic"]:
                    if self.debug:
                        print("separate_bold", p["text"])
                    p["font_obj"].set_italic(p["italic"])

                p["font_obj"].set_underline(p["underline"])

                p["shadow"] = p["font_obj"].render(p["text"], 1, p["shadow_color"])
                # if len(p["color"]) == 4:
                #     print(p["color"][3])
                p["text"] = p["font_obj"].render(p["text"], 1, p["color"])

            if p["link"]:
                self.links[p["link"]] = p
                self.links[p["link"]]["absolute_rect"] = rect

            if p["image"] and p["image"] in self.images:
                image = self.images[p["image"]]
                image_rect = image.get_rect(center=rect.center)
                # font_height = p["font_obj"].get_height()
                scale = p["h"] / image_rect.height
                # scale *= 0.8  # self.IMAGE_WIDTH_FACTOR
                # image = pygame.transform.scale(image, (int(image_rect.width * scale), int(image_rect.height * scale)))
                # print(p["image"], p["h"], image_rect.height, image_rect.width, scale)

                image = pygame.transform.scale_by(image, scale)
                image_rect = image.get_rect(center=rect.center)
                # print(p["image"], p["h"], image_rect.height, image_rect.width, scale)
                self.canvas.blit(image, image_rect)
            else:
                if p["cast_shadow"]:
                    self.canvas.blit(p["shadow"], rect.move(p["shadow_offset"]))
                self.canvas.blit(p["text"], rect)
            self.needs_update = False

            canvas_height = self.canvas.get_size()[1]
            # if rect.top >= (self.canvas_rect.bottom - self.default_style["h"]):
            # if rect.top >= (canvas_height - (self.MARGIN_VERTICAL * 2) - self.default_style["h"]):

            if rect.top >= (canvas_height - self.default_style["h"]):
                break

    def scroll(self, y: int = 0) -> None:
        # do not try to scroll if text fits on the screen
        if not self.needs_scrolling:
            return

        # if isinstance(y, int):
        self.y += y
        if self.y < self.end_y:
            self.y = self.end_y
        elif self.y > self.start_y:
            self.y = self.start_y

        size = abs(self.end_y - self.start_y)
        self.percentage = (self.start_y - self.y) / size

        self.needs_update = True

        # print(self.y, self.start_y, self.end_y, size, (self.start_y - self.y) / size)
        # elif isinstance(y, str):
        #     if y == "home":
        #         self.y = self.start_y
        #     elif y == "end":
        #         self.y = self.end_y

    def clear(self) -> None:
        self.canvas.blit(self.bg, (0, 0))

        if self.alpha < 255:
            self.canvas.fill((0, 0, 0, self.alpha))
            # self.canvas.fill((0, 0, 0, 0))

    def is_scroll_top(self) -> bool:
        # return self.y == self.start_y
        return self.percentage <= 0.0

    def is_scroll_bottom(self) -> bool:
        # return self.y == self.end_y
        return self.percentage >= 0.90

    def scroll_line_up(self) -> None:
        self.scroll(50)

    def scroll_line_down(self) -> None:
        self.scroll(-50)

    def scroll_page_up(self) -> None:
        self.scroll(200)

    def scroll_page_down(self) -> None:
        self.scroll(-300)

    def scroll_top(self) -> None:
        self.scroll(-self.start_y)

    def scroll_bottom(self) -> None:
        self.scroll(self.end_y)

    def on_key_press(self, event: pygame.event.Event) -> None:

        if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
            self.scroll_line_up()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
            self.scroll_page_up()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_HOME:
            # self.scroll("home")
            self.scroll_top()

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
            self.scroll_line_down()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
            self.scroll_page_down()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_END:
            # self.scroll("end")
            self.scroll_bottom()

    def on_mouse_move(self, mouse_position: tuple[int, int]) -> str:
        return self.check_link_activation(mouse_position)

    def check_link_activation(self, pos: tuple[int, int]) -> str:
        pos_offset = pos[0] - self.canvas_offset[0], pos[1] - self.canvas_offset[1]

        for link in self.links:
            # print(self.links[link]["rect"])
            if self.links[link]["absolute_rect"].collidepoint(pos_offset):
                # print("hovering over", link)
                return link
                # if link != self.last_link_name:
                #     self.last_link_name = link
                #     # self.default_style["font_obj"] = self.fonts.load(
                #     #     self.default_style["font"], self.default_style["size"])
                #     font = self.default_style["font_obj"]
                # self.last_link_tooltip = pygame.Surface(font.size(link), pygame.SRCALPHA)
                # self.last_link_tooltip.fill((150, 90, 150, 200))
                # self.last_link_tooltip.blit(font.render(link, 1, (255, 255, 255)), (0, 0))
                # self.needs_update = True
        return ""

    def on_mouse_button(self, event: pygame.event.Event) -> str:
        if event.type == pygame.MOUSEBUTTONDOWN:
            # left click
            if event.button == 1:
                return self.check_link_activation(pygame.mouse.get_pos())
            # scroll up
            if event.button == 4:
                self.scroll_line_up()
            # scroll down
            elif event.button == 5:
                self.scroll_line_down()

        return ""
