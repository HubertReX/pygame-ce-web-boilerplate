
"""We show here how to extend a Style class to create a custom one and use it as default style."""
# tags: style, styling, advanced styling, default, default style, set default style, mystyle,
# assign style, set_style_attr, generate_shadow

import pygame
import math
import thorpy as tp

from settings import HUD_DIR, MAIN_FONT, load_image
from ui import NinePatch

pygame.init()

WIDTH, HEIGHT = 1200, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
# tp.set_default_font("arialrounded", 15)
tp.set_default_font(str(MAIN_FONT), 12)
tp.init(screen, tp.theme_human)  # bind screen to gui elements and set theme


# here we will go from a lower level to make polygonal frame for buttons
class NinePatchStyle(tp.styles.TextStyle):
    bck_color = (50, 50, 50, 0)

    # margins = (4 * 4, 4 * 4)
    margins = (6 * 4, 6 * 4)

    def __init__(self,
                 font_color: tuple[int, int, int] = (250, 250, 250),
                 n_frames: int = 1,
                 panel_bg_file: str = "Theme1/button_normal.png"):
        super().__init__()
        self.font_color = font_color
        self.thickness = 1
        self.border_color = (0, 0, 0)
        self.n_frames = n_frames
        self.frame_mod = 1  # mandatory frame_mod > 0 for animations
        self.color_variation = 0.4
        self.panel_bg_scale: int = 6
        self.panel_bg_border: int = 2
        # self.panel_bg_file: str = "nine_patch_03.png"
        self.panel_bg_file: str = panel_bg_file

    def generate_images(self, text, arrow=False):
        surfaces = []
        for i in range(self.n_frames):
            tmp = self.bck_color
            self.bck_color = (0, 0, 0, 0)

            self.bck_color = tmp
            if self.n_frames > 1:
                v =  (1. - self.color_variation) + self.color_variation * math.sin(i * math.pi / self.n_frames)
                # bck_color = [v * c for c in self.bck_color[:3]]
                tmp_font_color = [v * c for c in self.font_color[:3]]
                # bck_color.append(bck_color[3])
            else:
                # bck_color = self.bck_color
                tmp_font_color = self.font_color
                pass
            self.set_font_color(tmp_font_color)
            surface = tp.styles.TextStyle.generate_images(self, text, arrow)[0]
            w, h = surface.get_size()
            mx, my = self.margins
            # t = self.thickness
            panel_bg = NinePatch(file=self.panel_bg_file,
                                 scale=self.panel_bg_scale,
                                 border=self.panel_bg_border).get_scaled_to(w, h)
            # panel_bg = load_image(HUD_DIR / "Theme" / self.panel_bg_file).convert_alpha()
            # panel_bg = pygame.transform.scale(panel_bg, (w, h))
            surface.blit(panel_bg, (0, 0))
            # points = (0, my), (mx, 0), (w - 1, 0), (w - 1, h - my), (w - mx, h - 1), (0, h - 1)
            # inner surface
            # pygame.draw.polygon(surface, bck_color, points)
            # border
            # pygame.draw.polygon(surface, self.border_color, points, t)

            self.reblit_text(surface, text, arrow)
            surfaces.append(surface)
        return surfaces

    def copy(self):
        c =  super().copy()
        # the properties that you added should be copied
        c.thickness = self.thickness
        c.border_color = self.border_color
        c.n_frames = self.n_frames
        c.frame_mod = self.frame_mod
        c.panel_bg_scale = self.panel_bg_scale
        c.panel_bg_file = self.panel_bg_file
        return c


def get_group(group_name, box_cls="box"):

    button = tp.Button("Standard button")

    text2 = tp.Text("This is a long text written to show how auto multilines texts work.")
    text2.set_font_auto_multilines_width(200)

    ddlb = tp.DropDownListButton(("Camel", "Cat", "Dog", "Goat"), bck_func=before_gui)
    dropdownlist = tp.Labelled("Dropdown:", ddlb)

    check = tp.Labelled("Checkbox:", tp.Checkbox(True))
    radio = tp.Labelled("Radio:", tp.Radio(True))
    text_input = tp.Labelled("Text input:", tp.TextInput("", "Type text here"))
    slider = tp.SliderWithText("Value:", 10, 80, 30, 100, edit=True)  # slider is labelled by default
    toggle = tp.ToggleButton("Toggle button", value=False)
    switch = tp.SwitchButtonWithText("Switch:", ("Foo", "Bar"))  # switch is labelled by default

    if box_cls == "group":
        title_box = tp.Group([button, text_input, slider, text2, dropdownlist, check, toggle, radio, switch])
    else:
        title_box = tp.TitleBox(group_name,
                                [button, text_input, slider, text2, dropdownlist, check, toggle, radio, switch])

    return title_box


style_normal = NinePatchStyle()

tp.theme_round2()
# tp.styles.
tp.Button.style_normal = style_normal
tp.Button.style_pressed = NinePatchStyle(panel_bg_file = "Theme1/button_pressed3.png")
tp.Button.style_locked = NinePatchStyle(panel_bg_file = "Theme1/button_disabled.png")
# tp.Button.style_hover = style_normal.copy()
tp.Button.style_hover = NinePatchStyle(font_color=(255, 0, 0), n_frames=30, panel_bg_file = "Theme1/button_hover2.png")
# tp.Button.style_hover.nframes = 30
# tp.Button.style_hover.font_color = (255, 0, 0)
tp.Button.style_hover.border_color = (255, 0, 0)
tp.Button.style_hover.thickness = 5

normal_img   = load_image(HUD_DIR / "Theme" / "Theme1/button_normal.png").convert_alpha()
pressed_img  = load_image(HUD_DIR / "Theme" / "Theme1/button_pressed3.png").convert_alpha()
hover_img    = load_image(HUD_DIR / "Theme" / "Theme1/button_hover2.png").convert_alpha()
disabled_img = load_image(HUD_DIR / "Theme" / "Theme1/button_disabled.png").convert_alpha()

normal_img   = pygame.transform.scale_by(normal_img, 8)
pressed_img  = pygame.transform.scale_by(pressed_img, 8)
hover_img    = pygame.transform.scale_by(hover_img, 8)
disabled_img = pygame.transform.scale_by(disabled_img, 8)

image_button = tp.ImageButton("Press me!",
                              normal_img,
                              img_pressed=pressed_img,
                              img_hover=hover_img,
                              img_locked=disabled_img)
image_button.set_style_attr("margins", (30, 35))
# au lieu de border litteral, faire 2 polygones enchasses

# tp.TitleBox.style_normal = style_normal

button_ok = tp.Button("OK")
# button_ok.generate_shadow(fast=False)

button_bad = tp.Button("BAD")
# button_bad.generate_shadow(fast=False)
button_bad.set_locked(True)

button_close = tp.Button("Close")
button_close.generate_shadow(fast=False)

group = tp.Group([button_ok, button_bad, image_button, button_close], gap=50)
group.state

bg = NinePatch(file="nine_patch_02.png",
               scale=4,
               border=6).get_scaled_to(WIDTH, HEIGHT)


def call_close():  # dummy function for the test
    print("Clicked !")
    exit(1)


def call_ok(caller: tp.Button):  # dummy function for the test
    print("#" * 10)
    print(caller.get_current_state())
    print(caller.text)
    # print(caller)
    if caller.id == button_close.id:
        exit(1)


# defining standard 'click' function (though its technically not a click)
button_close.at_unclick = call_ok
button_close.at_unclick_params = {"caller": button_close}
button_ok.at_unclick = call_ok  # lambda _: print("OK !")
button_ok.at_unclick_params = {"caller": button_ok}
image_button.at_unclick = call_ok  # lambda _: print("OK !")
image_button.at_unclick_params = {"caller": image_button}


def before_gui():  # add here the things to do each frame before blitting gui elements
    screen.fill((250,) * 3)
    screen.blit(bg, (0, 0))


tp.call_before_gui(before_gui)  # tells thorpy to call before_gui() before drawing gui.

# For the sake of brevity, the main loop is replaced here by a shorter but blackbox-like method
player = group.get_updater(esc_quit=True).launch()
pygame.quit()
