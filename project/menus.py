from state import State
from settings import *
import pygame
import pygame_menu
import game
import splash_screen
import scene

##########################################################################################################################
#MARK: MenuScreen
class MenuScreen(State):
    def __init__(self, game: game.Game, name: str) -> None:
        super().__init__(game)
        self.name = name
        # print("MenuScreen.__init__", game.__class__.__name__)
        
        self.menu = self.create_menu()
        self.menu.enable()
        self.menu.full_reset()
        # self.msgs = []
        
    # def debug(self, msgs: list[str]):
    #     return super().debug(msgs)
        
    def __repr__(self) -> str:
        return f"{__class__.__name__}: {self.name}"
        
    def create_menu() -> pygame_menu.Menu:
        raise NotImplementedError("Subclasses should implement this!")
    
    def deactivate(self):
        # self.menu.disable()
        
        # Scene(self.game, "grasslands", "start").enter_state()
        self.game.reset_inputs()
        self.exit_state()
        
    def update(self, dt: float, events: list[pygame.event.EventType]):
        # .get_inputs()
        # events = pygame.event.get()
        
        if self.menu.is_enabled:            
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
            
    def draw(self, screen: pygame.Surface, dt: float):
        # screen.fill(COLORS["blue"])
        # self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
        if self.menu.is_enabled:
            self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
        msgs = [
            f"Menu   : {self.name}",
            f"Scenes : {len(self.game.states)}",
        ]
        if SHOW_DEBUG_INFO:
            self.debug(msgs)
            
##########################################################################################################################
#MARK: MainMenuScreen
class MainMenuScreen(MenuScreen):
    
    # def about_menu(self):
    #     am = AboutMenuScreen(self.game)
    #     am.create_menu()
    #     return am.menu
        
    def create_menu(self) -> pygame_menu.Menu:
        # print("AboutMenuScreen.create_menu", self.game.__class__.__name__)
        
        main_theme = pygame_menu.themes.THEME_BLUE.copy()

        main_menu = pygame_menu.Menu(
            width=WIDTH * 0.6,
            height=HEIGHT * 0.6,
            theme=main_theme,
            title="Main Menu",
        )

        # am = AboutMenuScreen(self.game, "AboutMenu")
        # am.create_menu()

        # main_menu.add.button("Play", Scene(self.game, "grasslands", "start").enter_state)
        main_menu.add.button("Play", scene.Scene(self.game, "Village", "start").enter_state)
        main_menu.add.button("Settings", splash_screen.SplashScreen(self.game, "Settings").enter_state)
        main_menu.add.button("About", AboutMenuScreen(self.game, "AboutMenu").enter_state)
        # main_menu.add.button("Close menu", self.deactivate)
        if not IS_WEB:
            main_menu.add.button("Quit", pygame_menu.events.EXIT)
    
        return main_menu

    def update(self, dt: float, events: list[pygame.event.EventType]):
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
            self.game.save_screenshot()
    
    # def draw(self, screen: pygame.Surface):
    #     # screen.fill(COLORS["blue"])
    #     # self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
    #     if self.menu.is_enabled:
    #         self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
        
    #     self.debug([f"Menu : {self.name}"])
    
##########################################################################################################################
#MARK: AboutMenuScreen
class AboutMenuScreen(MenuScreen):
    
    def create_menu(self) -> pygame_menu.Menu:
        # print("AboutMenuScreen.create_menu", self.game.__class__.__name__)
        
        about_theme = pygame_menu.themes.THEME_DEFAULT.copy()
        about_theme.widget_margin = (0, 0)

        about_menu = pygame_menu.Menu(
            width = WIDTH * 0.6,
            height = HEIGHT * 0.6,
            theme = about_theme,
            title = "About",
        )

        for m in ABOUT:
            about_menu.add.label(m, align=pygame_menu.locals.ALIGN_LEFT, font_size=20)
        about_menu.add.vertical_margin(30)
        about_menu.add.button("Back", self.deactivate)
        # about_menu.add.button("Close menu", pygame_menu.events.BACK)
        return about_menu

    def update(self, dt: float, events: list[pygame.event.EventType]):
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
            self.game.save_screenshot()

        # if INPUTS["help"]:
        #     self.deactivate()            
        
    # def draw(self, screen: pygame.Surface):
    #     # screen.fill(COLORS["blue"])
    #     # self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
    #     if self.menu.is_enabled:
    #         self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
        
    #     msgs = [
    #         f"Menu : {self.name}",
    #     ]
    #     self.debug(msgs)
    
