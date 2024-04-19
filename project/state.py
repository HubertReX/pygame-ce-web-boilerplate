from settings import *
import pygame
import pygame_menu
from objects import Wall, Collider
from transition import Transition
from pytmx.util_pygame import load_pygame
import game
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

ABOUT = [
    f'pygame-menu {pygame_menu.__version__}',
    f'Author: {pygame_menu.__author__}',
    f'Email: {pygame_menu.__email__}'
]

class State:
    def __init__(self, game: game.Game) -> None:
        self.game = game
        self.prev_state: "State" | None = None

    def enter_state(self):
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)
        
    def exit_state(self):
        if len(self.game.states) > 1:
            self.game.states.pop()
            
    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS['quit'] and not IS_WEB:
            self.game.running = False
            
        global SHOW_DEBUG_INFO
        if INPUTS['debug']:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()
            
        global SHOW_HELP_INFO
        if INPUTS['help']:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            self.game.reset_inputs()
            
    def draw(self, screen: pygame.Surface):
        raise NotImplementedError("Subclasses should implement this!")
        
    def debug(self, msgs: list[str]):
        if SHOW_DEBUG_INFO:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (10, 25 * i))
    
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
        
    def create_menu() -> pygame_menu.Menu:
        raise NotImplementedError("Subclasses should implement this!")
    
    def deactivate(self):
        # self.menu.disable()
        
        # Scene(self.game, 'grasslands', 'start').enter_state()
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
        if INPUTS['debug']:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()

        # if INPUTS['select']:
        #     self.deactivate()
            
        # if INPUTS['quit']:
        #     self.deactivate()
            
    def draw(self, screen: pygame.Surface):
        # screen.fill(COLORS["blue"])
        # self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
        if self.menu.is_enabled:
            self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
        msgs = [
            f"Menu   : {self.name}",
            f"Scenes : {len(self.game.states)}",
        ]
        self.debug(msgs)
            

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
            title='Main Menu',
        )

        # am = AboutMenuScreen(self.game, "AboutMenu")
        # am.create_menu()

        main_menu.add.button('Play', Scene(self.game, 'grasslands', 'start').enter_state)
        main_menu.add.button('Settings', SplashScreen(self.game, "Settings").enter_state)
        main_menu.add.button('About', AboutMenuScreen(self.game, "AboutMenu").enter_state)
        # main_menu.add.button('Close menu', self.deactivate)
        if not IS_WEB:
            main_menu.add.button('Quit', pygame_menu.events.EXIT)
    
        return main_menu

    def update(self, dt: float, events: list[pygame.event.EventType]):
        super().update(dt, events)

        if INPUTS['select']:
            # self.game.reset_inputs()
            widget = self.menu.get_current().get_selected_widget()
            if widget:
                self.game.reset_inputs()
                widget.apply()
        
        # menu = self.menu.get_current()
        # print(f"Menu : {self.name}")
                        
        if INPUTS['quit'] and not IS_WEB:
            self.game.running = False    
            self.deactivate()

        if INPUTS['screenshot']:
            self.game.save_screenshot()
    
    # def draw(self, screen: pygame.Surface):
    #     # screen.fill(COLORS["blue"])
    #     # self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
    #     if self.menu.is_enabled:
    #         self.menu.mainloop(screen, None, disable_loop=True, fps_limit=FPS_CAP)
        
    #     self.debug([f"Menu : {self.name}"])
    
class AboutMenuScreen(MenuScreen):
    
    def create_menu(self) -> pygame_menu.Menu:
        # print("AboutMenuScreen.create_menu", self.game.__class__.__name__)
        
        about_theme = pygame_menu.themes.THEME_DEFAULT.copy()
        about_theme.widget_margin = (0, 0)

        about_menu = pygame_menu.Menu(
            width = WIDTH * 0.6,
            height = HEIGHT * 0.6,
            theme = about_theme,
            title = 'About',
        )

        for m in ABOUT:
            about_menu.add.label(m, align=pygame_menu.locals.ALIGN_LEFT, font_size=20)
        about_menu.add.vertical_margin(30)
        about_menu.add.button('Back', self.deactivate)
        # about_menu.add.button('Close menu', pygame_menu.events.BACK)
        return about_menu

    def update(self, dt: float, events: list[pygame.event.EventType]):
        super().update(dt, events)

        if INPUTS['left_click']:
            # self.exit_state()
            # self.game.reset_inputs()
            self.deactivate()
            
        if INPUTS['right_click']:
            # self.exit_state()
            # self.game.reset_inputs()
            self.deactivate()
        

        if INPUTS['quit']:
            # self.menu.reset(1)
            self.deactivate()
            # self.exit_state()

        if INPUTS['select']:
            # self.exit_state()
            self.deactivate()

        if INPUTS['accept']:
            # self.exit_state()
            self.deactivate()

        if INPUTS['screenshot']:
            self.game.save_screenshot()

        # if INPUTS['help']:
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
    
    
class SplashScreen(State):
    def __init__(self, game: game.Game, name: str="") -> None:
        super().__init__(game)
        self.name = name
        
    def update(self, dt: float, events: list[pygame.event.EventType]):
        if INPUTS['left_click']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['right_click']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['quit']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['accept']:
            self.game.reset_inputs()
            self.exit_state()
            
        if INPUTS['select']:
            # Scene(self.game, 'grasslands', 'start').enter_state()
            self.game.reset_inputs()
            self.exit_state()
            
    def draw(self, screen: pygame.Surface):
        screen.fill(COLORS["blue"])
        self.game.render_text(f"{self.__class__.__name__}-{self.name}", (WIDTH / 2, HEIGHT / 2), centred=True)
        self.game.render_text(f"press space to continue", (WIDTH / 2, HEIGHT / 2 + TILE_SIZE + 10), centred=True)
            
class Scene(State):
    def __init__(self, game: game.Game, current_scene: str, entry_point: str) -> None:
        super().__init__(game)
        self.current_scene = current_scene
        self.entry_point = entry_point
        self.new_scene: str = "0"
        
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        
        self.transition = Transition(self)
        # moved here to avoid circular imports
        from characters import Player
        self.player: Player = Player(self.game, self, [self.update_sprites, self.draw_sprites], (WIDTH / 2, HEIGHT / 2), "monochrome_ninja")
        
        # load data from pytmx
        tileset_map = load_pygame(RESOURCES_DIR / f"{self.current_scene}.tmx")

        # setup level geometry with simple pygame rectangles, loaded from pytmx
        self.layers = []
        for layer in tileset_map.layers:
            self.layers.append(layer.name)
            
        self.walls = []
        # for obj in tileset_map.objects:
        #     if obj.name == "player":
        #         self.player.rect.center = [obj.x, obj.y]
        #         break
        #     self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        
        # under1 layer contains 'walls' - tiles that collide with characters
        if "walls" in self.layers:
            for x, y, surf in tileset_map.get_layer_by_name("walls").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                # can be created as sprites if needed
        #         Wall([self.block_sprites], (x * TILE_SIZE, y * TILE_SIZE), "blocks", surf)
                        
        if "exits" in self.layers:
            for obj in tileset_map.get_layer_by_name("exits"):
                Collider([self.exit_sprites], (obj.x, obj.y), (obj.width, obj.height), obj.name, obj.to_map, obj.entry_point)
        
        self.entry_points = {}
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)
                
        if self.entry_point in self.entry_points:
            ep = self.entry_points[self.entry_point]
            # print(ep)
            self.player.rect.center = [ep.x, ep.y]
        else:
            print("no entry point found")
            
        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            data=pyscroll.data.TiledMapData(tileset_map),
            size=self.game.screen.get_size(),
            clamp_camera=True, # camera stops at map borders (no black area around), player needs to be stopped separately
        )
        self.map_layer.zoom = 2
        

        # pyscroll supports layered rendering.  our map has 3 'under'
        # layers.  layers begin with 0.  the layers are 0, 1, and 2.
        # sprites are always drawn over the tiles of the layer they are
        # on.  since we want the sprite to be on top of layer 2, we set
        # the default layer for sprites as 2.
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)        
        
        # put the player in the center of the map
        # self.player.rect.topleft = self.map_layer.map_rect.center

        # add our player to the group
        self.group.add(self.player)
    
    def go_to_scene(self):
        self.exit_state()
        Scene(self.game, self.new_scene, self.entry_point).enter_state()
        
    
    def update(self, dt: float, events: list[pygame.event.EventType]):
        # self.update_sprites.update(dt)
        self.group.update(dt)
        self.transition.update(dt)
        # check if the sprite's feet are colliding with wall       
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        # for sprite in self.group.sprites():
        #     if sprite.rect.collidelist(self.walls) > -1:
        #         sprite.move_back(dt)
        if self.player.feet.collidelist(self.walls) > -1:
            self.player.move_back(dt)

        # switch to splash screen        
        if INPUTS['quit']:
            # SplashScreen(self.game).enter_state()
            # Scene(self.game, 'grasslands', 'start').enter_state()
            # MainMenuScreen(self.game, next_scene).enter_state()
            self.exit_state()
            self.game.reset_inputs()

        global SHOW_DEBUG_INFO
        if INPUTS['debug']:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            self.game.reset_inputs()

        global SHOW_HELP_INFO
        if INPUTS['help']:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            self.game.reset_inputs()
        
        if INPUTS['right_click']:
            self.exit_state()
            self.game.reset_inputs()
        
        if INPUTS['help']:
            # print("need help")
            # next_scene = None #  self # Scene(self.game, 'grasslands', 'start')
            # AboutMenuScreen(self.game, next_scene).enter_state()
            MainMenuScreen(self.game, "MainMenu").enter_state()
            self.game.reset_inputs()

        if INPUTS['screenshot']:
            self.game.save_screenshot()
            
        # live reload map
        if INPUTS['reload']:
            self.map_layer.reload()
            
        # camera zoom in/out
        if INPUTS['zoom_in']: # or INPUTS["scroll_up"]:
            self.map_layer.zoom += 0.25
            self.game.reset_inputs()
            
        if INPUTS['zoom_out']: # or INPUTS["scroll_down"]:
            value = self.map_layer.zoom - 0.25
            if value > 0:
                self.map_layer.zoom = value
            self.game.reset_inputs()
            
    def show_help(self):
        i = 0
        for definition in ACTIONS.values():
            if definition["show"]:
                self.game.render_text(f"{', '.join(definition['show'])} - {definition['msg']}", (WIDTH - 210, i * 30), shadow=True)
                i += 1
    
    def draw(self, screen: pygame.Surface):
        # screen.fill(COLORS["red"])
        self.group.center(self.player.rect.center)
        # self.draw_sprites.draw(screen)
        self.group.draw(screen)
        self.transition.draw(screen)
        if not SHOW_HELP_INFO:
            self.game.render_text(f"press [h] for help", (WIDTH / 2, HEIGHT - 25), shadow=True, centred=True)
        msgs = [
            f"FPS: {self.game.clock.get_fps():06.02f}",
            f"vel: {self.player.vel.x:06.02f} {self.player.vel.y:06.02f}",
            f"col: {self.player.rect.collidelist(self.walls):06.02f}",
        ]
        self.debug(msgs)
        
        if SHOW_HELP_INFO:
            self.show_help()
    