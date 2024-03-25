import pygame
from characters import Player
from objects import Wall
from settings import *

from pytmx.util_pygame import load_pygame

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup


class State:
    def __init__(self, game) -> None:
        self.game = game
        self.prev_state: "State" | None = None

    def enter_state(self):
        if len(self.game.states) > 1:
            self.prev_state = self.game.states[-1]
        self.game.states.append(self)
        
    def exit_state(self):
        if len(self.game.states) > 1:
            self.game.states.pop()
            
    def update(self, dt: float):
        pass
        
    def draw(self, screen: pygame.Surface):
        pass
        
    def debug(self, msgs: list[str]):
        if DEBUG:
            for i, msg in enumerate(msgs):
                self.game.render_text(msg, (10, 25 * i))
    
class SplashScreen(State):
    def __init__(self, game) -> None:
        super().__init__(game)
        
    def update(self, dt: float):
        if INPUTS['select']:
            Scene(self.game).enter_state()
            self.game.reset_inputs()
            
    def draw(self, screen: pygame.Surface):
        screen.fill(COLORS["blue"])
        self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT / 2), centred=True)
            
class Scene(State):
    def __init__(self, game) -> None:
        super().__init__(game)
        
        self.update_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        
        self.player: Player = Player(self.game, self, [self.update_sprites, self.draw_sprites], (WIDTH / 2, HEIGHT / 2), "monochrome_ninja")
        
        # load data from pytmx
        tileset_map = load_pygame(MAP_PATH)

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.layers = []
        for layer in tileset_map.layers:
            self.layers.append(layer.name)
            
        # print(self.layers)
        self.walls = []
        # for obj in tileset_map.objects:
        #     self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        if "under1" in self.layers:
            for x, y, surf in tileset_map.get_layer_by_name("under1").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                # print(rect)
                Wall([self.block_sprites], (x * TILE_SIZE, y * TILE_SIZE), "blocks", surf)
                
        # print(len(self.walls))
        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            data=pyscroll.data.TiledMapData(tileset_map),
            size=self.game.screen.get_size(),
            clamp_camera=True,
        )
        self.map_layer.zoom = 3
        

        # pyscroll supports layered rendering.  our map has 3 'under'
        # layers.  layers begin with 0.  the layers are 0, 1, and 2.
        # sprites are always drawn over the tiles of the layer they are
        # on.  since we want the sprite to be on top of layer 2, we set
        # the default layer for sprites as 2.
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)        
        # put the hero in the center of the map
        # self.hero = Hero()
        # self.hero.position = self.map_layer.map_rect.center
        self.player.rect.topleft = self.map_layer.map_rect.center

        # add our hero to the group
        self.group.add(self.player)
        
        for i in range(5):
            print(i, len(self.group.get_sprites_from_layer(i)))
    
    def update(self, dt: float):
        # self.update_sprites.update(dt)
        self.group.update(dt)
        
        # self.block_sprites.update(dt)
        # for sprite in self.block_sprites.sprites():
        #     sprite.rect.topleft = self.map_layer.translate_rect(sprite.hitbox).topleft
        # check if the sprite's feet are colliding with wall
        
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        # for sprite in self.group.sprites():
        #     if sprite.rect.collidelist(self.walls) > -1:
        #         sprite.move_back(dt)
        
        # if self.player.rect.collidelist(self.walls) > -1:
        #     self.player.move_back(dt)
        
        if INPUTS['select']:
            SplashScreen(self.game).enter_state()
            self.game.reset_inputs()
        
        if INPUTS['reload']:
            self.map_layer.reload()
            
        if INPUTS['zoom_in']: # or INPUTS["scroll_up"]:
            self.map_layer.zoom += 0.25
        if INPUTS['zoom_out']: # or INPUTS["scroll_down"]:
            value = self.map_layer.zoom - 0.25
            if value > 0:
                self.map_layer.zoom = value
            
        self.group.center(self.player.rect.center)
        if self.player.rect.collidelist(self.group.get_sprites_from_layer(1)) > -1:
            self.player.move_back(dt)
        
        
    def draw(self, screen: pygame.Surface):
        screen.fill(COLORS["red"])
        
        # self.draw_sprites.draw(screen)
        self.group.draw(screen)
        # self.map_layer.draw(screen, screen.get_rect())
        # self.block_sprites.draw(screen)
        self.game.render_text(f"{self.__class__.__name__}: press space to continue", (WIDTH / 2, HEIGHT - 25), centred=True)
        msgs = [
            f"FPS: {self.game.clock.get_fps():06.02f}",
            f"vel: {self.player.vel.x:06.02f} {self.player.vel.y:06.02f}",
            f"col: {self.player.rect.collidelist(self.walls):06.02f}",
        ]
        self.debug(msgs)
    