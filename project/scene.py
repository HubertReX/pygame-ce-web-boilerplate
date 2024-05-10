from state import State
from settings import *
import pygame
import game
from objects import Wall, Collider
from transition import Transition, TransitionCircle
from maze_generator import hunt_and_kill_maze
from maze_generator.maze_utils import get_gid_from_tmx_id, build_tileset_map_from_maze

from pytmx.util_pygame import load_pygame
import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup
import menus

##########################################################################################################################
#MARK: Scene
class Scene(State):
    def __init__(
            self, 
            game: game.Game, 
            current_scene: str, 
            entry_point: str, 
            is_maze: bool = False, 
            maze_cols: int = 0, 
            maze_rows: int = 0
        ) -> None:
        
        super().__init__(game)
        self.current_scene = current_scene
        self.entry_point = entry_point
        self.new_scene: Collider = None
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows
        
        self.shadow_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        
        # self.transition = Transition(self)
        self.transition = TransitionCircle(self)
        
        # moved here to avoid circular imports
        from characters import Player, NPC
        self.player: Player = Player(
            self.game, 
            self, 
            [self.draw_sprites], 
            self.shadow_sprites, 
            (WIDTH / 2, HEIGHT / 2), 
            "GreenNinja"
        ) # Woman, GreenNinja, monochrome_ninja
        
        if self.is_maze:
            # check from which scene we came here
            if len(self.game.states) > 1:
                self.prev_state = self.game.states[-1]
            
            # if we returned from last scene on the stack, it's actually time to exit
            if not self.prev_state:
                # pass
                self.game.is_running = False
                self.exit_state()
                quit()
            else:
                # generate new maze
                self.maze = hunt_and_kill_maze.HuntAndKillMaze(self.maze_cols, self.maze_rows)
                self.maze.generate()
                tileset_map = load_pygame(MAZE_DIR / f"MazeTileset_clean.tmx")
                build_tileset_map_from_maze(
                    tileset_map, 
                    self.maze, 
                    to_map = self.prev_state.current_scene,
                    entry_point = self.prev_state.new_scene.return_entry_point
                )
        else:
            # load data from pytmx
            tileset_map = load_pygame(MAPS_DIR / f"{self.current_scene}.tmx")

        # setup level geometry with simple pygame rectangles, loaded from pytmx
        self.layers = []
        for layer in tileset_map.layers:
            self.layers.append(layer.name)
            
        # string with coma separated names of particle systems active in this map
        map_particles = tileset_map.properties.get("particles", "").replace(" ", "").strip().lower().split(",")
        self.particles = []
        # init particle systems relevant for this scene
        for particle in map_particles:
            if particle in PARTICLES:
                particle_class = PARTICLES[particle]
                self.particles.append(particle_class(self.game.canvas))
                self.game.register_custom_event(self.particles[-1].custom_event_id, self.particles[-1].add)
        
        self.walls = []
        if "walls" in self.layers:
            walls = tileset_map.get_layer_by_name("walls")
            walls_width = walls.width
            walls_height = walls.height
            # path finding uses only grid build of tiles and not world coordinates in pixels
            self.path_finding_grid = [[0 for _ in range(walls_width)] for _ in range(walls_height)]
            
            for x, y, surf in tileset_map.get_layer_by_name("walls").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                self.path_finding_grid[y][x] = 100
                        
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
                    getattr(obj, "maze_cols", 0), 
                    getattr(obj, "maze_rows", 0), 
                    getattr(obj, "return_entry_point", ""), 
                )
                
        waypoints = {}
        # layer of invisible objects consisting of points that layout a list waypoints to follow by NPCs
        if "waypoints" in self.layers:
            for obj in tileset_map.get_layer_by_name("waypoints"):
                waypoints[obj.name] = (obj.points if hasattr(obj, "points") else obj.as_points)
        
        self.entry_points = {}
        # layer of invisible objects being single points on map where NPCs show up coming from linked map
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)

        self.NPC : list[NPC] = []
        # layer of invisible objects being single points determining where NPCs will spawn
        if "spawn_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("spawn_points"):
                # list of waypoints attached by NPCs sprite_name
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
            # spawning 4 NPCs in upper right, lower right, lower left corners and in the map middle (TODO: remove HARDCODED positions)
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols - 1) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows - 1) *6)) * TILE_SIZE + 2), "Snake", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5                             ) * TILE_SIZE + 2, ((7 + (self.maze_rows - 1) *6)) * TILE_SIZE + 2), "SpiderRed", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols - 1) * 6)) * TILE_SIZE + 2, ((7                          )) * TILE_SIZE + 2), "Spirit", () ))
            self.NPC.append(NPC(self.game, self, [self.draw_sprites], self.shadow_sprites, ( (5 + ((self.maze_cols //2) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows //2) *6)) * TILE_SIZE + 2), "Slime", () ))
            
        if self.entry_point in self.entry_points:
            # set first start position for the Player
            ep = self.entry_points[self.entry_point]
            self.player.pos = vec(ep.x, ep.y)
            self.player.adjust_rect()
        else:
            print("[red]no entry point found!")
            # fallback - put the player in the center of the map
            self.player.pos = self.map_layer.map_rect.center
            
        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            data = pyscroll.data.TiledMapData(tileset_map),
            size = self.game.screen.get_size(),
            clamp_camera = True, # camera stops at map borders (no black area around), player blocked to be stopped separately
        )
        self.map_layer.zoom = ZOOM_LEVEL
        

        # Pyscroll supports layered rendering. 
        # Our map has several 'under' layers and 'over' layers.
        # Sprites (NPCs) are always drawn over the tiles of the layer they are on.
        self.sprites_layer = self.layers.index("sprites")
        # main SpritesGroup holding whole tiled map with all layers and NPCs
        self.group = PyscrollGroup(map_layer = self.map_layer, default_layer = self.sprites_layer)        
        
        # add our player to the group
        self.group.add(self.shadow_sprites, layer = self.sprites_layer - 1)
        self.group.add(self.player)
        self.group.add(self.NPC)
                
        for x, y, surf in tileset_map.layers[0].tiles():
            
            # get step cost for all walkable tiles
            # stored as negative number to distinguish from walls (positive numbers)
            # this is used in A*
            if self.path_finding_grid[y][x] == 0:
                # check the 'under' layers one by one - the top most cost prevails
                tile_0_gid = tileset_map.get_tile_properties(x, y, 0)
                tile_1_gid = tileset_map.get_tile_properties(x, y, 1)
                # base step cost
                step_cost = 100
                if tile_0_gid and "step_cost" in tile_0_gid.keys():
                    step_cost = tile_0_gid["step_cost"]
                if tile_1_gid and "step_cost" in tile_1_gid.keys():
                    step_cost = tile_1_gid["step_cost"]
                self.path_finding_grid[y][x] = -step_cost
    
    
    def __repr__(self) -> str:
        return f"{__class__.__name__}: {self.current_scene}"
    
    
    def go_to_scene(self):
        self.transition.exiting = False
        new_scene = Scene(
            self.game, 
            self.new_scene.to_map, 
            self.new_scene.entry_point, 
            self.new_scene.is_maze, 
            self.new_scene.maze_cols, 
            self.new_scene.maze_rows
        )
        self.exit_state(quit=False)
        new_scene.enter_state()
        
    
    #MARK: update
    def update(self, dt: float, events: list[pygame.event.EventType]):
        global INPUTS
        
        self.group.update(dt)
        self.transition.update(dt)
        
        # check if the sprite's feet are colliding with wall       
        # sprite must have a rect called feet, and slide and move_back methods,
        # otherwise this will fail
        if self.player.feet.collidelist(self.walls) > -1:
            # slide along wall or do a step_back
            self.player.slide(self.walls)

        if not self.player.is_flying:
            collided_index = self.player.feet.collidelist(self.NPC)
            if collided_index > -1:
                # engage fight with enemy or push back friendly NPC
                self.player.encounter(self.NPC[collided_index])
                # slide along wall or do a step_back
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

        # exit from current state and go back to previous
        if INPUTS["quit"]:
            # SplashScreen(self.game).enter_state()
            # Scene(self.game, "grasslands", "start").enter_state()
            # MainMenuScreen(self.game, next_scene).enter_state()
            self.exit_state()
            self.game.reset_inputs()

        global SHOW_DEBUG_INFO
        if INPUTS["debug"]:
            SHOW_DEBUG_INFO = not SHOW_DEBUG_INFO
            INPUTS["debug"] = False            

        global USE_ALPHA_FILTER
        if INPUTS["alpha"]:
            USE_ALPHA_FILTER = not USE_ALPHA_FILTER
            INPUTS["alpha"] = False            

        global SHOW_HELP_INFO
        if INPUTS["help"]:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            INPUTS["help"] = False
            
        if INPUTS["run"]:
            # toggle between run and walk
            if self.player.speed == self.player.speed_run:
                self.player.speed = self.player.speed_walk
            else:
                self.player.speed = self.player.speed_run
            INPUTS["run"] = False
        
        if INPUTS["jump"]:
            # self.player.is_jumping = not self.player.is_jumping
            if not self.player.is_flying:
                if not self.player.is_jumping:
                    self.player.is_jumping = True
                    self.player.jump()
                    # when airborn move one layer above so it's not colliding with obstacles on the ground
                    self.group.change_layer(self.player, self.sprites_layer + 1)
            
            INPUTS["jump"] = False
            
        if INPUTS["fly"]:
            # toggle flying mode
            if not self.player.is_jumping:            
                self.player.is_flying = not self.player.is_flying
                if self.player.is_flying:
                    # when airborn move one layer above so it's not colliding with obstacles on the ground 
                    self.group.change_layer(self.player, self.sprites_layer + 1)
                else:
                    self.group.change_layer(self.player, self.sprites_layer)
                
            INPUTS["fly"] = False
        
        # handled in characters module
        # if INPUTS["right_click"]:
            # self.exit_state()
            # self.game.reset_inputs()
        
        if INPUTS["help"]:
            # next_scene = None #  self # Scene(self.game, "grasslands", "start")
            # AboutMenuScreen(self.game, next_scene).enter_state()
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
            # self.game.reset_inputs()
            INPUTS["help"] = False
        
        global IS_PAUSED
        if INPUTS["pause"]:
            IS_PAUSED = not IS_PAUSED
            print(f"{IS_PAUSED=}")
            INPUTS["pause"] = False

        if INPUTS["screenshot"]:
            self.game.save_screenshot()
            INPUTS["screenshot"] = False
            
        # live reload map
        if INPUTS["reload"]:
            self.map_layer.reload()
            INPUTS["reload"] = False
            
        # camera zoom in/out
        if INPUTS["zoom_in"]:
            self.map_layer.zoom += 0.25
            INPUTS["zoom_in"] = False
            
        if INPUTS["zoom_out"]:
            value = self.map_layer.zoom - 0.25
            if value > 0:
                self.map_layer.zoom = value
            INPUTS["zoom_out"] = False
            
    def show_help(self):
        # list actions to be displayed by the property "show"
        show_actions = [action for action in ACTIONS.values() if action["show"]]
        # render semitransparent panel in background
        rect = pygame.Rect(
            WIDTH - 400 - 4, 
            -10 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING, 
            400 - 2, 
            (len(show_actions) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING
        )
        self.game.render_panel(rect, (10,10,10,150))
        
        for i, action in enumerate(show_actions, start=1):
                self.game.render_text(
                    f"{', '.join(action['show']):>11} - {action['msg']}", 
                    (WIDTH - 400, i * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), 
                    shadow = True
                )
    
    #MARK: draw
    def draw(self, screen: pygame.Surface, dt: float):
        # center map on player
        self.group.center(self.player.pos)
        
        self.group.draw(screen)
        
        for particle in self.particles:
            particle.emit(dt)
        
        self.transition.draw(screen)
        
        if SHOW_DEBUG_INFO:
            self.show_debug()
        
        if SHOW_HELP_INFO:
            self.show_help()
        else:
            self.game.render_text(
                f"press [h] for help", 
                (WIDTH // 2, HEIGHT - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING), 
                shadow = True, 
                centred = True
            )
            
        # alpha filter demo
        if USE_ALPHA_FILTER: 
            self.apply_alpha_filter(screen) 


    def apply_alpha_filter(self, screen):
        h = HEIGHT // 2
        self.game.render_text("Day",   (0, h - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING))
        self.game.render_text("Night", (0, h +                    TEXT_ROW_SPACING))
            
            # sunny, warm yellow light during daytime
        half_screen = pygame.Surface((WIDTH, h), pygame.SRCALPHA)   
        half_screen.fill((152, 152, 0, 70))
        screen.blit(half_screen, (0, 0))    
            
            # cold, dark and bluish light at night
        half_screen.fill((0, 0, 102, 120))
        screen.blit(half_screen, (0, h))   


    #MARK: show_debug
    def show_debug(self):
            # prepare shader info
            shader_index = SHADERS_NAMES.index(self.game.shader.shader_name)
            if shader_index < 0:
                shader_index = 0
            if USE_SHADERS:
                shader_name = SHADERS_NAMES[shader_index]
            else:
                shader_name = "n/a"
            
            # prepare debug messages displayed in upper left corner
            msgs = [
                f"FPS: {self.game.clock.get_fps(): 6.1f} Shader: {shader_name}",
                # f"vel: {self.player.vel.x: 6.1f} {self.player.vel.y: 6.1f}",
                f"x  : {self.player.pos.x: 3.0f}   y : {self.player.pos.y: 3.0f}",
                f"g x:  {self.player.tileset_coord.x: 3.0f} g y : {self.player.tileset_coord.y: 3.0f}",
                # f"up_vel: {self.player.up_vel: 3.1f} up_acc{self.player.up_acc: 3.1f}",
                f"t x:  {self.player.target.x: 3.0f} t y : {self.player.target.y: 3.0f}",
                # f"offset: {self.player.jumping_offset: 6.1f}",
                # f"col: {self.player.rect.collidelist(self.walls):06.02f}",
                # f"bored={self.player.state.enter_time: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
            ]
            self.debug(msgs)
            
            # display npc (and players) debug messages
            for npc in self.NPC + [self.player]:
                # prepare text displayed under NPC
                texts = [
                    npc.name,
                    f"px={npc.pos.x // 1:3} y={(npc.pos.y - 4) // 1:3}",
                    f"gx={npc.tileset_coord.x:3} y={npc.tileset_coord.y:3}",
                    f"s ={npc.state} j={npc.is_flying}",
                    f"wc={npc.waypoints_cnt} wn={npc.current_waypoint_no}",
                    f"tx={npc.get_tileset_coord(npc.target).x:3} y={npc.get_tileset_coord(npc.target).y:3}",
                ]
                # draw lines connecting waypoints
                if npc.waypoints_cnt > 0:
                    curr_wp = npc.waypoints[npc.current_waypoint_no]
                    # add current waypoint as text under NPC
                    texts.append(f"cw={npc.get_tileset_coord(curr_wp).x:3} {npc.get_tileset_coord(curr_wp).y:3}")
                    prev_point = (npc.pos.x, npc.pos.y - 4)
                    for point in list(npc.waypoints)[npc.current_waypoint_no:]:
                        from_p = self.map_layer.translate_point(vec(prev_point[0], prev_point[1]))
                        to_p = self.map_layer.translate_point(vec(point[0], point[1]))
                        pygame.draw.line(self.game.canvas, (0,0,128, 32), from_p, to_p, width=2)
                        prev_point = point
                
                pos = self.map_layer.translate_point(npc.pos)
                self.game.render_texts(texts, pos, font_size=FONT_SIZE_MEDIUM, centred=True)
                
                # render red square indicating hitbox
                rect = self.map_layer.translate_rect(npc.feet)
                pygame.draw.rect(self.game.canvas, "red", rect, width=2)
                
            # draw walls (colliders)
            for y, row in enumerate(self.path_finding_grid):
                for x, tile in enumerate(row):
                    if tile > 0:
                        rect_w = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        rect_s = self.map_layer.translate_rect(rect_w)
                        img = pygame.Surface(rect_s.size, pygame.SRCALPHA)
                        pygame.draw.rect(img, (0,0,200,64), img.get_rect())
                        self.game.canvas.blit(img, rect_s)
        