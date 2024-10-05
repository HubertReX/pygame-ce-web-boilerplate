# ---------------------------------------------------------
# sftext - Scrollable Formatted Text for pygame
# Copyright (c) 2016 Lucas de Morais Siqueira
# Distributed under the GNU Lesser General Public License version 3.
#
#       \ vvvvvvvvvvvvv /
#     >>> STYLE MANAGER <<<
#       / ^^^^^^^^^^^^^ \
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

import re

DEFAULT_STYLE = {
    # At the moment only font filenames are supported. That means the font
    # must be in the same directory as the main script.
    # Or you could (should?) use a resource manager such as
    "font": "caladea-regular.ttf",
    "size": 20,
    "indent": 0,
    "bold": False,
    "italic": False,
    "underline": False,
    "link": "",
    "color": (128, 144, 160),  # RGB values
    "cast_shadow": False,
    "shadow_color": (30, 30, 30),  # RGB values
    "shadow_offset": (2, 2),
    "align": "left",
    "image": "",  # png image filename
    # if a separate file should be used for italic/bold, specify it;
    # if not, use None
    "separate_italic": "caladea-italic.ttf",
    "separate_bold": "caladea-bold.ttf",
    "separate_bolditalic": "caladea-bolditalic.ttf",
}


class Style:
    default_style = DEFAULT_STYLE

    @classmethod
    def set_default(cls, source):
        if isinstance(source, str):
            cls.string = str(source)
            cls._get_style()
            cls.default_style = dict(cls.style)
        elif isinstance(source, dict):
            for key, value in source.items():
                cls.default_style[key] = value
        return cls.default_style

    @classmethod
    def get_default(cls, string):
        return cls.default_style

    @classmethod
    def stylize(cls, string, style=None):
        if style is None:
            style = cls.default_style
        stylized = ""

        for key, value in style.items():
            if isinstance(value, str):
                stylized += ("{" + "{} \"{}".format(key, value) + "\"}")
            else:
                stylized += ("{" + "{} {}".format(key, value) + "}")
        stylized += string
        return stylized

    @classmethod
    def split(cls, string):
        cls.string = str(string)
        cls._get_style()
        return cls.string, cls.style

    @classmethod
    def remove(cls, string):
        cls.string = str(string)
        cls._get_style()
        return cls.string

    @classmethod
    def get(cls, string):
        cls.string = str(string)
        cls._get_style()
        return cls.style

    @classmethod
    def _get_style(cls):
        cls.style = {}
        cls.style["font"] = cls._get_font()
        cls.style["size"] = cls._get_size()
        cls.style["bold"] = cls._get_font_bold()
        cls.style["italic"] = cls._get_font_italic()
        cls.style["underline"] = cls._get_font_underline()
        cls.style["link"] = cls._get_link()
        cls.style["color"] = cls._get_font_color()
        cls.style["cast_shadow"] = cls._get_cast_shadow()
        cls.style["shadow_color"] = cls._get_shadow_color()
        cls.style["shadow_offset"] = cls._get_shadow_offset()
        cls.style["align"] = cls._get_font_align()
        cls.style["image"] = cls._get_image()
        cls.style["indent"] = cls._get_font_indent()
        cls.style["separate_bold"] = cls._get_separate_bold()
        cls.style["separate_italic"] = cls._get_separate_italic()
        cls.style["separate_bolditalic"] = cls._get_separate_bolditalic()

    @classmethod
    def _get_font(cls):
        pattern = (
            r"{font(_name)? ('|\")(?P<font>[A-Za-z0-9_ -]+"
            r"(?P<ext>.ttf))('|\")}")
        search_group = re.search(pattern, cls.string)
        if search_group:
            if search_group.group("ext"):
                font = search_group.group("font")
            else:
                font = search_group.group("font") + ".ttf"
                # print(font)
        else:
            font = cls.default_style["font"]
        cls.string = re.sub(
            (
                r"({font(_name)? ('|\")([A-Za-z0-9_ -]+"
                r"(.ttf)?)('|\")})"),
            "",
            cls.string)
        return font

    @classmethod
    def _get_separate_italic(cls):
        pattern = (
            r"{separate_italic ('|\")(?P<separate_italic>[A-Za-z0-9_ -]+"
            r"(?P<ext>.ttf))('|\")}")
        search_group = re.search(pattern, cls.string)
        if search_group:
            if search_group.group("ext"):
                separate_italic = search_group.group("separate_italic")
            else:
                separate_italic = search_group.group("separate_italic") + ".ttf"
                # print(separate_italic)
        else:
            if cls.style["font"] == cls.default_style["font"]:
                separate_italic = cls.default_style["separate_italic"]
            else:
                separate_italic = None
        cls.string = re.sub(
            (
                r"({separate_italic ('|\")([A-Za-z0-9_ -]+"
                r"(.ttf)?)('|\")})"),
            "",
            cls.string)
        return separate_italic

    @classmethod
    def _get_separate_bold(cls):
        pattern = (
            r"{separate_bold ('|\")(?P<separate_bold>[A-Za-z0-9_ -]+"
            r"(?P<ext>.ttf))('|\")}")
        search_group = re.search(pattern, cls.string)
        if search_group:
            if search_group.group("ext"):
                separate_bold = search_group.group("separate_bold")
            else:
                separate_bold = search_group.group("separate_bold") + ".ttf"
                # print(separate_bold)
        else:
            if cls.style["font"] == cls.default_style["font"]:
                separate_bold = cls.default_style["separate_bold"]
            else:
                separate_bold = None
        cls.string = re.sub(
            (
                r"({separate_bold ('|\")([A-Za-z0-9_ -]+"
                r"(.ttf)?)('|\")})"),
            "",
            cls.string)
        return separate_bold

    @classmethod
    def _get_separate_bolditalic(cls):
        pattern = (
            r"{separate_bolditalic ('|\")"
            r"(?P<separate_bolditalic>[A-Za-z0-9_ -]+"
            r"(?P<ext>.ttf))('|\")}")
        search_group = re.search(pattern, cls.string)
        if search_group:
            if search_group.group("ext"):
                separate_bolditalic = search_group.group("separate_bolditalic")
            else:
                separate_bolditalic = search_group.group(
                    "separate_bolditalic") + ".ttf"
                # print(separate_bolditalic)
        else:
            if cls.style["font"] == cls.default_style["font"]:
                separate_bolditalic = cls.default_style["separate_bolditalic"]
            else:
                separate_bolditalic = None
        cls.string = re.sub(
            (
                r"({separate_bold ('|\")([A-Za-z0-9_ -]+"
                r"(.ttf)?)('|\")})"),
            "",
            cls.string)
        return separate_bolditalic

    @classmethod
    def _get_size(cls):
        pattern = r"{(font_)?size (?P<size>\d+)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            size = search_group.group("size")
        else:
            size = cls.default_style["size"]
        cls.string = re.sub(pattern, "", cls.string)
        return int(size)

    @classmethod
    def _get_font_bold(cls):
        pattern = r"{bold ('|\"|)(?P<bold>True|False)('|\"|)}"
        search_group = re.search(pattern, cls.string, re.I)
        if search_group:
            bold = search_group.group("bold")
            cls.string = re.sub(pattern, "", cls.string)
            return bold.lower() == "true"
        else:
            bold = cls.default_style["bold"]
            cls.string = re.sub(pattern, "", cls.string)
            return bold

    @classmethod
    def _get_font_italic(cls):
        pattern = r"{italic ('|\"|)(?P<italic>True|False)('|\"|)}"
        search_group = re.search(pattern, cls.string, re.I)
        if search_group:
            italic = search_group.group("italic")
            cls.string = re.sub(pattern, "", cls.string)
            return italic.lower() == "true"
        else:
            italic = cls.default_style["italic"]
            cls.string = re.sub(pattern, "", cls.string)
            return italic

    @classmethod
    def _get_font_underline(cls):
        pattern = r"{underline ('|\"|)(?P<underline>True|False)('|\"|)}"
        search_group = re.search(pattern, cls.string, re.I)
        if search_group:
            underline = search_group.group("underline")
            cls.string = re.sub(pattern, "", cls.string)
            return underline.lower() == "true"
        else:
            underline = cls.default_style["underline"]
            cls.string = re.sub(pattern, "", cls.string)
            return underline

    @classmethod
    def _get_link(cls):
        pattern = r"{link ('|\"|)(?P<link>[^\]]+)('|\"|)}"
        search_group = re.search(pattern, cls.string, re.I)
        if search_group:
            link = search_group.group("link")
            cls.string = re.sub(pattern, "", cls.string)
            return link
        else:
            link = cls.default_style["link"]
            cls.string = re.sub(pattern, "", cls.string)
            return link

    @classmethod
    def _get_font_color(cls):
        # pattern = r"{color \((?P<color>\d+\, *\d+\, *\d+)(?P<alpha>\, *\d+)?\)}"
        pattern = r"{color \((?P<color>\d+\, *\d+\, *\d+(\, *\d+)?)\)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            color = search_group.group("color")
            color = tuple(int(c) for c in color.split(","))
        else:
            color = cls.default_style["color"]
        cls.string = re.sub(pattern, "", cls.string)
        return color

    @classmethod
    def _get_cast_shadow(cls):
        pattern = r"{cast_shadow ('|\"|)(?P<cast_shadow>True|False)('|\"|)}"
        search_group = re.search(pattern, cls.string, re.I)
        if search_group:
            cast_shadow = search_group.group("cast_shadow")
            cls.string = re.sub(pattern, "", cls.string)
            return cast_shadow.lower() == "true"
        else:
            cast_shadow = cls.default_style["cast_shadow"]
            cls.string = re.sub(pattern, "", cls.string)
            return cast_shadow

    @classmethod
    def _get_shadow_color(cls):
        # pattern = r"{shadow_color \((?P<shadow_color>\d+\, *\d+\, *\d+)(?P<alpha>\, *\d+)?\)}"
        pattern = r"{shadow_color \((?P<shadow_color>\d+\, *\d+\, *\d+(\, *\d+)?)\)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            shadow_color = search_group.group("shadow_color")
            shadow_color = tuple(int(c) for c in shadow_color.split(","))
        else:
            shadow_color = cls.default_style["shadow_color"]
        cls.string = re.sub(pattern, "", cls.string)
        return shadow_color

    @classmethod
    def _get_shadow_offset(cls):
        pattern = r"{shadow_offset \((?P<shadow_offset>\d+\, *\d+)\)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            shadow_offset = search_group.group("shadow_offset")
            shadow_offset = tuple(int(c) for c in shadow_offset.split(","))
        else:
            shadow_offset = cls.default_style["shadow_offset"]
        cls.string = re.sub(pattern, "", cls.string)
        return shadow_offset

    @classmethod
    def _get_font_align(cls):
        pattern = "{(.)?align ('|\"|)(?P<align>(left|center|right))('|\"|)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            align = search_group.group("align")
        else:
            align = cls.default_style["align"]
        cls.string = re.sub(pattern, "", cls.string)
        return align

    @classmethod
    def _get_image(cls):
        pattern = r"{(.)?image ('|\"|)(?P<image>([A-Za-z0-9_ -\.]+))('|\"|)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            image = search_group.group("image")
        else:
            image = cls.default_style["image"]
        cls.string = re.sub(pattern, "", cls.string)
        return image

    @classmethod
    def _get_font_indent(cls):
        pattern = r"{indent (?P<indent>\d+)}"
        search_group = re.search(pattern, cls.string)
        if search_group:
            indent = search_group.group("indent")
        else:
            indent = cls.default_style["indent"]
        cls.string = re.sub(pattern, "", cls.string)
        return int(indent)


if __name__ == "__main__":
    my_style = {
        # At the moment only font filenames are supported. That means the font
        # must be in the same directory as the main script.
        # Or you could (should?) use a resource manager such as
        "font": "Fontin.ttf",
        "size": 20,
        "indent": 0,
        "bold": False,
        "italic": False,
        "underline": False,
        "link": "",
        "color": (128, 144, 160),  # RGB values
        "cast_shadow": False,
        "shadow_color": (30, 30, 30),  # RGB values
        "shadow_offset": (2, 2),
        "align": "left",
        "image": "",  # png image filename
        # if a separate file should be used for italic/bold, specify it;
        # if not, use None
        "separate_italic": "Fontin-Italic.ttf",
        "separate_bold": "Fontin-Bold.ttf"
    }

    Style.set_default(my_style)
    plain_text, new_style = Style.split("{bold True}Boldy!")
    print("\n\"{}\"".format(new_style))
