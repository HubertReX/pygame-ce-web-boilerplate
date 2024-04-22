from state import State
from settings import *
import pygame
import game
from objects import Wall, Collider
from transition import Transition
from pytmx.util_pygame import load_pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup
import menus 

##########################################################################################################################
#MARK: State
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
        from characters import Player, NPC
        self.player: Player = Player(self.game, self, [self.update_sprites, self.draw_sprites], (WIDTH / 2, HEIGHT / 2), "GreenNinja") # Woman, GreenNinja, monochrome_ninja
        
        # load data from pytmx
        tileset_map = load_pygame(MAPS_DIR / f"{self.current_scene}.tmx")

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
        self.NPC = []
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)
                if obj.name != "start":
                    self.NPC.append(NPC(self.game, self, [self.update_sprites, self.draw_sprites], (obj.x, obj.y), obj.name))
                
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
        self.map_layer.zoom = ZOOM_LEVEL
        

        # pyscroll supports layered rendering.  our map has 3 'under'
        # layers.  layers begin with 0.  the layers are 0, 1, and 2.
        # sprites are always drawn over the tiles of the layer they are
        # on.  since we want the sprite to be on top of layer 2, we set
        # the default layer for sprites as 2.
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=3)        
        
        # put the player in the center of the map
        # self.player.rect.topleft = self.map_layer.map_rect.center

        # add our player to the group
        self.group.add(self.player)
        self.group.add(self.NPC)
    
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
        if self.player.feet.collidelist(self.walls + self.NPC) > -1:
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
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
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
