import random
from particles import ParticleImageBased
from state import State
from settings import *
import pygame
import game
from objects import Wall, Collider
from transition import Transition, TransitionCircle
from pytmx.util_pygame import load_pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup
import menus 
# from threading import Timer

##########################################################################################################################
#MARK: State
class Scene(State):
    def __init__(self, game: game.Game, current_scene: str, entry_point: str) -> None:
        super().__init__(game)
        self.current_scene = current_scene
        self.entry_point = entry_point
        self.new_scene: str = "0"
        
        spawn_rect = pygame.Rect(0, 0, WIDTH, HEIGHT // 2)
        leaf_img = pygame.image.load(PARTICLES_DIR / "Leaf_single.png").convert_alpha()
        self.particle_leafs = ParticleImageBased(screen=self.game.canvas, img=leaf_img, rate=0.5, scale_speed=0.25, alpha_speed=0.1, rotation_speed=0.0, spawn_rect=spawn_rect)
        self.particle_leafs.next_run = self.game.time_elapsed + self.particle_leafs.interval
        # self.game.register_custom_event(self.particle_leaf.custom_event_id, self.add_leafs)
        # Timer(self.particle_leaf.interval, self.add_leafs).start()

        
        self.shadow_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        
        # self.transition = Transition(self)
        self.transition = TransitionCircle(self)
        # moved here to avoid circular imports
        from characters import Player, NPC
        self.player: Player = Player(self.game, self, [self.draw_sprites], self.shadow_sprites, (WIDTH / 2, HEIGHT / 2), "GreenNinja") # Woman, GreenNinja, monochrome_ninja

        # self.shadow_surf = pygame.Surface((TILE_SIZE-2, 6))
        # rect = self.shadow_surf.get_rect()
        # self.shadow_surf.set_colorkey("black")
        # pygame.draw.ellipse(self.shadow_surf, (10,10,10), rect)
        
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
        
        # string with coma separated names of particle systems active in this map
        self.map_particles = tileset_map.properties.get("particles", "")
        
        if "walls" in self.layers:
            for x, y, surf in tileset_map.get_layer_by_name("walls").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                # can be created as sprites if needed
        #         Wall([self.block_sprites], (x * TILE_SIZE, y * TILE_SIZE), "blocks", surf)
                        
        if "exits" in self.layers:
            for obj in tileset_map.get_layer_by_name("exits"):
                Collider([self.exit_sprites], (obj.x, obj.y), (obj.width, obj.height), obj.name, obj.to_map, obj.entry_point)
                
        waypoints = {}
        if "waypoints" in self.layers:
            for obj in tileset_map.get_layer_by_name("waypoints"):
                # print(obj.__dict__)
                waypoints[obj.name] = (obj.points if hasattr(obj, "points") else obj.as_points)
        
        self.entry_points = {}
        self.NPC : list[NPC] = []
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)
                waypoint = waypoints.get(obj.name, ())
                
                if obj.sprite_name != "null":
                    self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, (obj.x, obj.y), obj.name, waypoint))
                
        if self.entry_point in self.entry_points:
            ep = self.entry_points[self.entry_point]
            # print(ep)
            self.player.pos = vec(ep.x, ep.y)
            self.player.adjust_rect()
        else:
            print("[red]no entry point found!")
            # put the player in the center of the map
            self.player.pos = self.map_layer.map_rect.center
            
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
        
        # add our player to the group
        self.group.add(self.shadow_sprites, layer=2)
        self.group.add(self.player)
        self.group.add(self.NPC)        
    
    def add_leafs(self):
        # move 80 pixels/seconds into south-west (down-left) +/- 30 degree, enlarge 5 x, kill after 4 seconds
        self.particle_leafs.add_particles(start_pos=pygame.mouse.get_pos(), move_speed=80, move_dir=210 + random.randint(-30, 30), scale=5, lifetime=4)

    def go_to_scene(self):
        self.exit_state()
        Scene(self.game, self.new_scene, self.entry_point).enter_state()
        
    
    def update(self, dt: float, events: list[pygame.event.EventType]):
        global INPUTS
        # self.update_sprites.update(dt)
        self.group.update(dt)
        self.transition.update(dt)
        
        if "leafs" in self.map_particles:
            if self.game.time_elapsed >= self.particle_leafs.next_run:
                self.particle_leafs.next_run = self.game.time_elapsed + self.particle_leafs.interval
                self.add_leafs()

        # check if the sprite's feet are colliding with wall       
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        # for sprite in self.group.sprites():
        #     if sprite.rect.collidelist(self.walls) > -1:
        #         sprite.move_back(dt)
        if self.player.feet.collidelist(self.walls) > -1:
            self.player.move_back(dt)

        if not self.player.is_flying:
            if self.player.feet.collidelist(self.NPC) > -1:
                self.player.move_back(dt)
            
        if self.player.is_flying:
            colliders = self.walls
        else:
            colliders = self.walls + [self.player]
            
        for npc in self.NPC:
            if npc.feet.collidelist(colliders) > -1:
                npc.move_back(dt)

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
            # print(f"{SHOW_DEBUG_INFO=}")
            # self.game.reset_inputs()
            INPUTS['debug'] = False            

        global USE_ALPHA_FILTER
        if INPUTS['alpha']:
            USE_ALPHA_FILTER = not USE_ALPHA_FILTER
            INPUTS['alpha'] = False            

        global SHOW_HELP_INFO
        if INPUTS['help']:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            # self.game.reset_inputs()
            INPUTS['help'] = False
            
        if INPUTS['run']:
            if self.player.speed == self.player.speed_run:
                self.player.speed = self.player.speed_walk
            else:
                self.player.speed = self.player.speed_run
            INPUTS['run'] = False
            # self.game.reset_inputs()
        
        if INPUTS["jump"]:
            # self.player.is_jumping = not self.player.is_jumping
            if not self.player.is_flying:
                if not self.player.is_jumping:
                    self.player.is_jumping = True
                    # move sprite up (in character physics shadow is offset down to the ground)
                    # self.player.rect.y -= TILE_SIZE
                    self.player.jump()
                    # when airborn move one layer above so it's not colliding with obstacles on ground 
                    # self.group.remove(self.player)
                    # self.group.add(self.player, layer=4)
                    self.group.change_layer(self.player, 4)
                # else:
                #     self.player.rect.y += TILE_SIZE
                #     self.group.remove(self.player)
                #     self.group.add(self.player, layer=3)
            
            INPUTS["jump"] = False
            
        if INPUTS["fly"]:
            if not self.player.is_jumping:            
                self.player.is_flying = not self.player.is_flying
                if self.player.is_flying:
                    # move sprite up (in character physics shadow is offset down to the ground)
                    # self.player.rect.y -= TILE_SIZE
                    # when airborn move one layer above so it's not colliding with obstacles on ground 
                    # self.group.remove(self.player)
                    # self.group.add(self.player, layer=4)
                    self.group.change_layer(self.player, 4)
                else:
                    # self.player.rect.y += TILE_SIZE
                    # self.group.remove(self.player)
                    # self.group.add(self.player, layer=3)
                    self.group.change_layer(self.player, 3)
                
                INPUTS["fly"] = False
        
        if INPUTS['right_click']:
            self.exit_state()
            self.game.reset_inputs()
        
        if INPUTS['help']:
            # print("need help")
            # next_scene = None #  self # Scene(self.game, 'grasslands', 'start')
            # AboutMenuScreen(self.game, next_scene).enter_state()
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
            # self.game.reset_inputs()
            INPUTS['help'] = False

        if INPUTS['screenshot']:
            self.game.save_screenshot()
            INPUTS['screenshot'] = False
            
        # live reload map
        if INPUTS['reload']:
            self.map_layer.reload()
            INPUTS['reload'] = False
            
        # camera zoom in/out
        if INPUTS['zoom_in']: # or INPUTS["scroll_up"]:
            self.map_layer.zoom += 0.25
            # self.game.reset_inputs()
            INPUTS['zoom_in'] = False
            
        if INPUTS['zoom_out']: # or INPUTS["scroll_down"]:
            value = self.map_layer.zoom - 0.25
            if value > 0:
                self.map_layer.zoom = value
            # self.game.reset_inputs()
            INPUTS['zoom_out'] = False
            
    def show_help(self):
        i = 1
        show_actions = [action for action in ACTIONS.values() if action["show"]]
        rect = pygame.Rect(WIDTH - 360 - 4, -10 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING, 358, (len(show_actions) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)
        self.game.render_panel(rect, (10,10,10,150))
        # self.game.render_text(" \n"*len(show_actions), (WIDTH - 360, FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), bg_color=(10,10,10,150))
        for action in show_actions:
                self.game.render_text(f"{', '.join(action['show']):>9} - {action['msg']}", (WIDTH - 360, i * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), shadow=True) # 
                i += 1
    
    def draw(self, screen: pygame.Surface, dt: float):
        # screen.fill(COLORS["red"])
        self.group.center(self.player.pos)
        # self.draw_sprites.draw(screen)

        # for npc in self.NPC + [self.player]:
        #     offset_x, offset_y = self.map_layer.get_center_offset()
        #     zoom = self.map_layer.zoom
        #     pos = [(npc.rect.centerx + offset_x)*zoom, (npc.rect.bottom + offset_y)*zoom + 3]
        #     # self.game.render_text(npc.name, pos, font_size=FONT_SIZE_SMALL, centred=True)
        #     screen.blit(self.shadow_surf, pos)
        
        self.group.draw(screen)
        if "leafs" in self.map_particles:
            self.particle_leafs.emit(dt)
        
        self.transition.draw(screen)
        
        if not SHOW_HELP_INFO:
            self.game.render_text(f"press [h] for help", (WIDTH // 2, HEIGHT - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), shadow=True, centred=True)
        
        msgs = [
            f"FPS: {self.game.clock.get_fps(): 6.1f}",
            f"vel: {self.player.vel.x: 6.1f} {self.player.vel.y: 6.1f}",
            f"up_vel: {self.player.up_vel: 6.1f} up_acc{self.player.up_acc: 6.1f}",
            f"offset: {self.player.jumping_offset: 6.1f}",
            # f"col: {self.player.rect.collidelist(self.walls):06.02f}",
            # f"bored={self.player.state.enter_time: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
            # f"next_run={self.particle_leaf.next_run: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
            # f"interval={self.particle_leaf.interval: 5.1f}",
        ]
        # print(f"up_vel: {self.player.up_vel: 6.1f} up_acc{self.player.up_acc: 6.1f} offset: {self.player.jumping_offset: 6.1f}")
        
        if SHOW_DEBUG_INFO:
            self.debug(msgs)
            for npc in self.NPC + [self.player]:
                # offset_x, offset_y = self.map_layer.get_center_offset()
                # zoom = self.map_layer.zoom
                # pos = [(npc.pos.x + offset_x)*zoom, (npc.pos.y + offset_y)*zoom]
                pos = self.map_layer.translate_point(npc.pos)
                self.game.render_text(npc.name, pos, font_size=FONT_SIZE_SMALL, centred=True)
                
                pos = self.map_layer.translate_point((npc.pos.x, npc.pos.y + (8 * 1)))
                self.game.render_text(f"s={npc.state} j={npc.is_flying}", pos, font_size=FONT_SIZE_SMALL, centred=True)

                pos = self.map_layer.translate_point((npc.pos.x, npc.pos.y + (8 * 2)))
                self.game.render_text(f"v={npc.vel.magnitude():04.1f} vp={npc.current_waypoint_no}", pos, font_size=FONT_SIZE_SMALL, centred=True) 
                
                rect = self.map_layer.translate_rect(npc.feet)
                pygame.draw.rect(self.game.canvas, "red", rect, width=2)
                # a={npc.acc.magnitude():4.1f}
                
        
        if SHOW_HELP_INFO:
            self.show_help()
            
        # alpha filter demo
        if USE_ALPHA_FILTER: 
            # radius = 300
            # circle = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)   
            # pygame.draw.rect(circle, (192, 192, 0, 128), (radius, radius), radius)
            # screen.blit(circle, (radius, radius))
            h = HEIGHT // 2
            self.game.render_text("Day",   (0, h - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING))
            self.game.render_text("Night", (0, h +                    TEXT_ROW_SPACING))
            half_screen = pygame.Surface((WIDTH, h), pygame.SRCALPHA)   
            # pygame.draw.rect(half_screen, (192, 192, 0, 128), (radius, radius), radius)
            half_screen.fill((152, 152, 0, 70))
            screen.blit(half_screen, (0, 0))    
            half_screen.fill((0, 0, 102, 120))
            screen.blit(half_screen, (0, h))    
