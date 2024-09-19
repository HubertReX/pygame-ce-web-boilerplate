import game
import pygame
import pygame_menu
import scene
import splash_screen
from settings import ABOUT, FPS_CAP, HEIGHT, HUD_DIR, INPUTS, IS_WEB, MENU_FONT, PANEL_BG_COLOR, SHOW_DEBUG_INFO, WIDTH
from state import State

#######################################################################################################################
# MARK: MenuScreen


class MenuScreen(State):
    def __init__(self, game: game.Game, name: str, bg_image: pygame.Surface | None = None) -> None:
        super().__init__(game)
        self.name = name
        self.bg_image = bg_image
        # print("MenuScreen.__init__", game.__class__.__name__)

        self.menu = self.create_menu()
        self.menu.enable()
        self.menu.full_reset()
        # self.msgs = []

    #############################################################################################################
    # def debug(self, msgs: list[str]) -> None:
    #     return super().debug(msgs)

    #############################################################################################################
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    #############################################################################################################
    def create_menu(self) -> pygame_menu.Menu:
        raise NotImplementedError("Subclasses should implement this!")

    #############################################################################################################
    def deactivate(self) -> None:
        # self.menu.disable()

        # Scene(self.game, "grasslands", "start").enter_state()
        self.game.reset_inputs()
        self.exit_state()

    #############################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]) -> None:
        # .get_inputs()
        # events = pygame.event.get()

        if self.menu.is_enabled():
            is_updated = self.menu.update(events)
            if is_updated:
                self.game.reset_inputs()

        global SHOW_DEBUG_INFO
        if INPUTS["debug"]:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()

        # if INPUTS["select"]:
        #     self.deactivate()

        # if INPUTS["quit"]:
        #     self.deactivate()

    #############################################################################################################
    def draw(self, screen: pygame.Surface, dt: float) -> None:
        screen.fill((85, 99, 77))
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        # self.game.render_text(f"{self.__class__.__name__}: # press space to continue",
        #   (WIDTH / 2, 32), centred=True)
        if self.menu.is_enabled():
            # self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)  # fps_limit=FPS_CAP
            self.menu.draw(screen)

        if SHOW_DEBUG_INFO:
            msgs = [
                f"Menu   : {self.name}",
                f"Scenes : {len(self.game.states)}",
            ]
            self.debug(msgs)

#######################################################################################################################
# MARK: MainMenuScreen


class MainMenuScreen(MenuScreen):

    # def about_menu(self):
    #     am = AboutMenuScreen(self.game)
    #     am.create_menu()
    #     return am.menu

    #############################################################################################################
    def create_menu(self) -> pygame_menu.Menu:
        # print("AboutMenuScreen.create_menu", self.game.__class__.__name__)

        main_theme = pygame_menu.themes.THEME_DARK.copy()

        self.border_image = pygame_menu.baseimage.BaseImage(
            # image_path=pygame_menu.baseimage.IMAGE_EXAMPLE_GRAY_LINES,
            # image_path="dark_panel.png",
            image_path=str(HUD_DIR / "Theme" / "nine_patch_06b.png"),
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_REPEAT_XY,
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_CENTER,

            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL,
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_SIMPLE,
            # drawing_offset=(0, 0)
        ).scale(4, 4, smooth=False)  # resize(18 * 4, 18 * 4, smooth=False)
        # my_image.set_alpha(64)
        # my_image.set_at((0, 0), (0, 0, 0, 0))

        # main_theme.background_color = (0, 0, 0, 0)
        i_w, i_h = self.border_image.get_size()
        main_theme.background_color = self.border_image.get_at((i_w // 2, i_h // 2))
        main_theme.border_color = self.border_image
        # main_theme.border_width = 20
        # main_theme.scrollarea_outer_margin = (6, 6)
        # main_theme.widget_border_inflate = (4, 4)
        # main_theme.widget_border_width = 5

        # main_theme.widget_margin = (24, 24)
        # main_theme.widget_box_margin = (24, 24)

        # main_theme.widget_padding = (24, 24)

        # font_name = pygame_menu.font.FONT_MUNRO  # FONT_MUNRO FONT_DIGITAL FONT_8BIT
        main_theme.title_font = MENU_FONT
        main_theme.widget_font = MENU_FONT

        main_theme.title_font_size = 48
        main_theme.widget_font_size = 36

        # MENUBAR_STYLE_UNDERLINE MENUBAR_STYLE_UNDERLINE_TITLE
        main_theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE

        main_menu = pygame_menu.Menu(
            width=WIDTH * 0.2,
            height=HEIGHT * 0.4,
            # position = (2 * WIDTH // 3, 50, False),
            position=(50, HEIGHT // 2, False),
            theme=main_theme,
            title="Main Menu",
            mouse_visible=False,
        )

        # am = AboutMenuScreen(self.game, "AboutMenu")
        # am.create_menu()

        # main_menu.add.button("Play", Scene(self.game, "grasslands", "start").enter_state)
        main_menu.add.button("Play",     scene.Scene(self.game, "Village", "start").enter_state)
        main_menu.add.button("Settings", splash_screen.SplashScreen(self.game, "Settings").enter_state)
        main_menu.add.button("About",    AboutMenuScreen(self.game, "AboutMenu", self.bg_image).enter_state)
        # main_menu.add.button("Close menu", self.deactivate)
        if not IS_WEB:
            main_menu.add.button("Quit", pygame_menu.events.EXIT)

        return main_menu

    #############################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]) -> None:
        super().update(dt, events)

        if INPUTS["select"]:
            # self.game.reset_inputs()
            widget = self.menu.get_current().get_selected_widget()
            if widget:
                self.game.reset_inputs()
                widget.apply()

        # menu = self.menu.get_current()
        # print(f"Menu : {self.name}")

        if INPUTS["quit"] and not IS_WEB:
            self.game.is_running = False
            self.deactivate()

        if INPUTS["screenshot"]:
            self.game.save_screenshot(self.game.add_notification_dummy)

    #############################################################################################################
    # def draw(self, screen: pygame.Surface, dt: float) -> None:
    #     super().draw(screen, dt)

    #     screen.blit(self.bg_image.get_surface(new=False), (WIDTH - 300, HEIGHT // 4))
    #     s = self.menu._scrollarea._border_tiles[2]
    #     screen.blit(s, (WIDTH - 300, 3 * HEIGHT // 4))
    #     # screen.fill(COLORS["blue"])
    #     # self.game.render_text(f"{self.__class__.__name__}:
    # press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
    #     if self.menu.is_enabled:
    #         self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
    #     self.debug([f"Menu : {self.name}"])

#######################################################################################################################
# MARK: AboutMenuScreen


class AboutMenuScreen(MenuScreen):

    #############################################################################################################
    def create_menu(self) -> pygame_menu.Menu:
        # print("AboutMenuScreen.create_menu", self.game.__class__.__name__)

        about_theme = pygame_menu.themes.THEME_DARK.copy()

        self.border_image = pygame_menu.baseimage.BaseImage(
            # image_path=pygame_menu.baseimage.IMAGE_EXAMPLE_GRAY_LINES,
            # image_path="dark_panel.png",
            image_path=str(HUD_DIR / "Theme" / "nine_patch_12b.png"),
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_REPEAT_XY,
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_CENTER,

            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_FILL,
            # drawing_mode=pygame_menu.baseimage.IMAGE_MODE_SIMPLE,
            # drawing_offset=(0, 0)
        ).scale(4, 4, smooth=False)  # resize(18 * 4, 18 * 4, smooth=False)
        # self.bg_image.set_alpha(64)
        # self.bg_image.set_at((0, 0), (0, 0, 0, 0))

        # about_theme.background_color = (0, 0, 0, 0)
        i_w, i_h = self.border_image.get_size()
        about_theme.background_color = self.border_image.get_at((i_w // 2, i_h // 2))
        about_theme.border_color = self.border_image

        about_theme.widget_margin = (0, 0)
        # font_name = pygame_menu.font.FONT_MUNRO  # FONT_MUNRO FONT_DIGITAL FONT_8BIT
        about_theme.title_font = MENU_FONT
        about_theme.widget_font = MENU_FONT

        about_theme.title_font_size = 48
        about_theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_NONE

        about_menu = pygame_menu.Menu(
            width = WIDTH * 0.2,
            height = HEIGHT * 0.4,
            position=(50, HEIGHT // 2, False),
            theme = about_theme,
            title = "About",
        )

        for m in ABOUT:
            about_menu.add.label(m, align=pygame_menu.locals.ALIGN_LEFT, font_size=20)
        about_menu.add.vertical_margin(30)
        about_menu.add.button("Back", self.deactivate)
        # about_menu.add.button("Close menu", pygame_menu.events.BACK)
        return about_menu

    #############################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]) -> None:
        super().update(dt, events)

        if INPUTS["left_click"]:
            # self.exit_state()
            # self.game.reset_inputs()
            self.deactivate()

        if INPUTS["right_click"]:
            # self.exit_state()
            # self.game.reset_inputs()
            self.deactivate()

        if INPUTS["quit"]:
            # self.menu.reset(1)
            self.deactivate()
            # self.exit_state()

        if INPUTS["select"]:
            # self.exit_state()
            self.deactivate()

        if INPUTS["accept"]:
            # self.exit_state()
            self.deactivate()

        if INPUTS["screenshot"]:
            self.game.save_screenshot(self.game.add_notification_dummy)

        # if INPUTS["help"]:
        #     self.deactivate()

    #############################################################################################################
    # def draw(self, screen: pygame.Surface):
    #     # screen.fill(COLORS["blue"])
    #     # self.game.render_text(f"{self.__class__.__name__}:
    # press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
    #     if self.menu.is_enabled:
    #         self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)

    #     msgs = [
    #         f"Menu : {self.name}",
    #     ]
    #     self.debug(msgs)
