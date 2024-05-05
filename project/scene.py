import random
from particles import ParticleImageBased
from state import State
from settings import *
import pygame
import game
from objects import Wall, Collider
from transition import Transition, TransitionCircle
from maze_generator import hunt_and_kill_maze
from maze_generator.maze_utils import get_gid_from_tmx_id, get_pyscroll_from_maze

from pytmx.util_pygame import load_pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup
import menus 
# from threading import Timer

##########################################################################################################################
#MARK: State
class Scene(State):
    def __init__(self, game: game.Game, current_scene: str, entry_point: str, is_maze: bool = False, maze_cols: int = 0, maze_rows: int = 0) -> None:
        super().__init__(game)
        self.current_scene = current_scene
        self.entry_point = entry_point
        self.new_scene: Collider = None
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows
        
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
        if self.is_maze:
            if len(self.game.states) > 1:
                self.prev_state = self.game.states[-1]
            
            if not self.prev_state:
                # pass
                self.game.is_running = False
                self.exit_state()
                quit()
            else:
                # print(f"{self.prev_state=}")
                self.maze = hunt_and_kill_maze.HuntAndKillMaze(self.maze_cols, self.maze_rows)
                self.maze.generate()
                tileset_map = load_pygame(MAZE_DIR / f"MazeTileset_clean.tmx")
                get_pyscroll_from_maze(
                    tileset_map, 
                    self.maze, 
                    to_map=self.prev_state.current_scene,
                    entry_point=self.prev_state.new_scene.return_entry_point
                )
        else:
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
            walls = tileset_map.get_layer_by_name("walls")
            walls_width = walls.width
            walls_height = walls.height
            # since NPCs hitbox (feet) is half the size of TILE, for path finding it's enough to approximate 
            # the full map with only 4 squares (one quoter of the TILE size)
            self.path_finding_grid = [[0 for _ in range(walls_width)] for _ in range(walls_height)]
            
            for x, y, surf in tileset_map.get_layer_by_name("walls").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                self.path_finding_grid[y][x] = 100
                # can be created as sprites if needed
        #         Wall([self.block_sprites], (x * TILE_SIZE, y * TILE_SIZE), "blocks", surf)
                        
        if "exits" in self.layers:
            for obj in tileset_map.get_layer_by_name("exits"):
                Collider(
                    [self.exit_sprites], 
                    (obj.x, obj.y), 
                    (obj.width, obj.height), 
                    obj.name, 
                    obj.to_map, 
                    obj.entry_point, 
                    obj.is_maze, 
                    getattr(obj, 'maze_cols', 0), 
                    getattr(obj, 'maze_rows', 0), 
                    getattr(obj, 'return_entry_point', ""), 
                )
                
        waypoints = {}
        if "waypoints" in self.layers:
            for obj in tileset_map.get_layer_by_name("waypoints"):
                # print(obj.__dict__)
                waypoints[obj.name] = (obj.points if hasattr(obj, "points") else obj.as_points)
        
        self.entry_points = {}
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)

        self.NPC : list[NPC] = []
        if "spawn_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("spawn_points"):
                waypoint = waypoints.get(obj.sprite_name, ())    
                npc = NPC(
                    self.game, 
                    self, 
                    [self.draw_sprites], 
                    self.shadow_sprites, 
                    (obj.x, obj.y), 
                    obj.sprite_name, 
                    waypoint
                )
                self.NPC.append(npc)
                    
        if self.is_maze:
            
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols - 1) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows - 1) *6)) * TILE_SIZE + 2), "Snake", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5                             ) * TILE_SIZE + 2, ((7 + (self.maze_rows - 1) *6)) * TILE_SIZE + 2), "SpiderRed", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols - 1) * 6)) * TILE_SIZE + 2, ((7                          )) * TILE_SIZE + 2), "Spirit", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols //2) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows //2) *6)) * TILE_SIZE + 2), "Slime", () ))
            
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
        self.sprites_layer = self.layers.index("sprites")
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=self.sprites_layer)        
        
        # add our player to the group
        self.group.add(self.shadow_sprites, layer=self.sprites_layer - 1)
        self.group.add(self.player)
        self.group.add(self.NPC)
                
        for x, y, surf in tileset_map.layers[0].tiles():
            
            # rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
            # self.walls.append(rect)        
            if self.path_finding_grid[y][x] == 0:
                sprites = self.group.get_sprites_at((x,y))
                # tile_0_gid = tileset_map.get_tile_gid(x, y, 0)
                # tile_1_gid = tileset_map.get_tile_gid(x, y, 1)
                tile_0_gid = tileset_map.get_tile_properties(x, y, 0)
                tile_1_gid = tileset_map.get_tile_properties(x, y, 1)
                step_cost = 100
                if tile_0_gid and "step_cost" in tile_0_gid.keys():
                    step_cost = tile_0_gid["step_cost"]
                if tile_1_gid and "step_cost" in tile_1_gid.keys():
                    step_cost = tile_1_gid["step_cost"]
                self.path_finding_grid[y][x] = -step_cost
                # if x == 28 and y in [6,7]:
                    # print(x, y, tile_0_gid, tile_1_gid, step_cost)
    
    
    def __repr__(self) -> str:
        return f"{__class__.__name__}: {self.current_scene}"
    
    def add_leafs(self):
        # move 80 pixels/seconds into south-west (down-left) +/- 30 degree, enlarge 5 x, kill after 4 seconds
        self.particle_leafs.add_particles(start_pos=pygame.mouse.get_pos(), move_speed=80, move_dir=210 + random.randint(-30, 30), scale=5, lifetime=4)

    def go_to_scene(self):
        self.transition.exiting = False
        new_scene = Scene(self.game, self.new_scene.to_map, self.new_scene.entry_point, self.new_scene.is_maze, self.new_scene.maze_cols, self.new_scene.maze_rows)
        self.exit_state(quit=False)
        new_scene.enter_state()
        
    
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
            # self.player.move_back(dt)
            self.player.slide(self.walls)

        if not self.player.is_flying:
            collided_index = self.player.feet.collidelist(self.NPC)
            if collided_index > -1:
                # self.player.move_back()
                self.player.encounter(self.NPC[collided_index])
                self.player.slide(self.NPC)
            
        colliders = self.walls
        # if self.player.is_flying:
        #     colliders = self.walls
        # else:
        #     colliders = self.walls + [self.player]
            
        for npc in self.NPC:
            if npc.feet.collidelist(colliders) > -1:
                # npc.move_back(dt)
                npc.slide(colliders)

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
                    self.group.change_layer(self.player, self.sprites_layer + 1)
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
                    self.group.change_layer(self.player, self.sprites_layer + 1)
                else:
                    # self.player.rect.y += TILE_SIZE
                    # self.group.remove(self.player)
                    # self.group.add(self.player, layer=3)
                    self.group.change_layer(self.player, self.sprites_layer)
                
                INPUTS["fly"] = False
        
        # if INPUTS['right_click']:
            # self.exit_state()
            # self.game.reset_inputs()
        
        if INPUTS['help']:
            # print("need help")
            # next_scene = None #  self # Scene(self.game, 'grasslands', 'start')
            # AboutMenuScreen(self.game, next_scene).enter_state()
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
            # self.game.reset_inputs()
            INPUTS['help'] = False
        global IS_PAUSED
        if INPUTS['pause']:
            IS_PAUSED = not IS_PAUSED
            print(f"{IS_PAUSED=}")
            INPUTS['pause'] = False

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
        rect = pygame.Rect(WIDTH - 400 - 4, -10 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING, 400 - 2, (len(show_actions) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)
        self.game.render_panel(rect, (10,10,10,150))
        # self.game.render_text(" \n"*len(show_actions), (WIDTH - 360, FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), bg_color=(10,10,10,150))
        for action in show_actions:
                self.game.render_text(f"{', '.join(action['show']):>11} - {action['msg']}", (WIDTH - 400, i * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), shadow=True) # 
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
            f"x  : {self.player.pos.x: 3.0f}   y : {self.player.pos.y: 3.0f}",
            f"g x:  {self.player.tileset_coord.x: 3.0f} g y : {self.player.tileset_coord.y: 3.0f}",
            # f"up_vel: {self.player.up_vel: 3.1f} up_acc{self.player.up_acc: 3.1f}",
            f"t x:  {self.player.target.x: 3.0f} t y : {self.player.target.y: 3.0f}",
            # f"offset: {self.player.jumping_offset: 6.1f}",
            # f"col: {self.player.rect.collidelist(self.walls):06.02f}",
            # f"bored={self.player.state.enter_time: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
            # f"next_run={self.particle_leaf.next_run: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
            # f"interval={self.particle_leaf.interval: 5.1f}",
        ]
        # print(f"up_vel: {self.player.up_vel: 6.1f} up_acc{self.player.up_acc: 6.1f} offset: {self.player.jumping_offset: 6.1f}")
        
        if SHOW_DEBUG_INFO:
            self.debug(msgs)
            
            # npc (and player) data
            for npc in self.NPC + [self.player]:
                texts = [
                    npc.name,
                    f"px={npc.pos.x // 1:3} y={(npc.pos.y - 4) // 1:3}",
                    f"gx={npc.tileset_coord.x:3} y={npc.tileset_coord.y:3}",
                    f"s ={npc.state} j={npc.is_flying}",
                    f"wc={npc.waypoints_cnt} wn={npc.current_waypoint_no}",
                    f"tx={npc.get_tileset_coord(npc.target).x:3} y={npc.get_tileset_coord(npc.target).y:3}",
                ]
                if npc.waypoints_cnt > 0:
                    curr_wp = npc.waypoints[npc.current_waypoint_no]
                    # texts.append(f"wp ={curr_wp.x//1:3} {curr_wp.y//1:3}")
                    texts.append(f"cw={npc.get_tileset_coord(curr_wp).x:3} {npc.get_tileset_coord(curr_wp).y:3}")
                    # points = [] + npc.waypoints
                    prev_point = (npc.pos.x, npc.pos.y - 4)
                    for point in list(npc.waypoints)[npc.current_waypoint_no:]:
                        from_p = self.map_layer.translate_point(vec(prev_point[0], prev_point[1]))
                        to_p = self.map_layer.translate_point(vec(point[0], point[1]))
                        pygame.draw.line(self.game.canvas, (0,0,128, 32), from_p, to_p, width=2)
                        prev_point = point
                pos = self.map_layer.translate_point(npc.pos)
                self.game.render_texts(texts, pos, font_size=FONT_SIZE_MEDIUM, centred=True)
                                
                rect = self.map_layer.translate_rect(npc.feet)
                pygame.draw.rect(self.game.canvas, "red", rect, width=2)
                
                # a={npc.acc.magnitude():4.1f}
            # walls grid
            for y, row in enumerate(self.path_finding_grid):
                for x, tile in enumerate(row):
                    if tile > 0:
                        rect_w = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        rect_s = self.map_layer.translate_rect(rect_w)
                        img = pygame.Surface(rect_s.size, pygame.SRCALPHA)
                        # img.fill((200,0,0,128))
                        pygame.draw.rect(img, (0,0,200,64), img.get_rect())
                        self.game.canvas.blit(img, rect_s)
                
        
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
