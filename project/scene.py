import random

import game
import menus
import pygame
import pyscroll
import pyscroll.data
from animation import animator
from maze_generator import hunt_and_kill_maze
from maze_generator.maze_utils import (
    TILE_SIZE, build_tileset_map_from_maze,
    clear_maze_cache, get_gid_from_tmx_id
)
from camera import Camera
from objects import Collider, ItemSprite
from pyscroll.group import PyscrollGroup
from pytmx.util_pygame import load_pygame
from particles import ParticleSystem
from state import State
from transition import Transition, TransitionCircle

from settings import (
    ACTIONS, BG_COLOR, CIRCLE_GRADIENT, CUTSCENE_BG_COLOR,
    DAY_FILTER, FONT_SIZE_MEDIUM, GAME_TIME_SPEED,
    HEIGHT, INITIAL_HOUR, MAPS_DIR, MAZE_DIR,
    NIGHT_FILTER, PANEL_BG_COLOR, PARTICLES,
    SHADERS_NAMES, TEXT_ROW_SPACING, USE_SHADERS,
    WAYPOINTS_LINE_COLOR, WIDTH, ZOOM_LEVEL,
    ColorValue, vec, vec3, INPUTS, SHOW_DEBUG_INFO, SHOW_HELP_INFO, USE_ALPHA_FILTER
)


#######################################################################################################################
# MARK: Scene
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
        self.game.time_elapsed = 0.0
        self.current_scene = current_scene
        self.entry_point = entry_point
        self.new_scene: Collider = None
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows

        self.label_sprites = pygame.sprite.Group()
        self.shadow_sprites = pygame.sprite.Group()
        self.draw_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.animations = pygame.sprite.Group()

        # self.transition = Transition(self)
        self.transition = TransitionCircle(self)

        # moved here to avoid circular imports
        from characters import Player
        self.player: Player = Player(
            self.game,
            self,
            [self.draw_sprites],
            self.shadow_sprites,
            self.label_sprites,
            (WIDTH / 2, HEIGHT / 2),
            "Player"
        )
        # view target for camera
        self.camera = Camera()
        self.camera.scene = self
        # self.camera.target = vec(1 * TILE_SIZE, 1 * TILE_SIZE)
        # self.camera.zoom   = ZOOM_LEVEL
        # self.map_view.zoom = self.camera.zoom

        # percentage of black bars shown during cutscene
        self.cutscene_framing: float = 0.0
        # it's high noon
        self.hour: int = INITIAL_HOUR
        self.minute: int = 0
        self.minute_f: float = 0.0
        # are we outdoors? shell there be night and day cycle?
        self.outdoor: bool = False
        # self.circle_gradient: pygame.Surface = (CIRCLE_GRADIENT).convert_alpha()

        self.load_map()

        # self.set_camera_on_player()

    ###################################################################################################################

    def load_map(self) -> None:
        # MARK: load_map
        if self.is_maze:
            # check from which scene we came here
            if len(self.game.states) > 0:
                self.prev_state = self.game.states[-1]

            # if we returned from last scene on the stack, it's actually time to exit
            # if not self.prev_state:
            #     pass
            # self.game.is_running = False
            # self.exit_state()
            # quit()
            # else:
            # generate new maze
            self.maze = hunt_and_kill_maze.HuntAndKillMaze(self.maze_cols, self.maze_rows)
            self.maze.generate()
            tileset_map = load_pygame(MAZE_DIR / "MazeTileset_clean.tmx")
            # combine tileset clean template with maze grid into final map
            build_tileset_map_from_maze(
                tileset_map,
                self.maze,
                to_map = self.return_scene,
                entry_point = self.return_entry_point
            )
        else:
            # load data from pytmx
            tileset_map = load_pygame(MAPS_DIR / f"{self.current_scene}.tmx")

        # setup level geometry with simple pygame rectangles, loaded from pytmx
        self.layers = []
        for layer in tileset_map.layers:
            self.layers.append(layer.name)

        self.outdoor = tileset_map.properties.get("outdoor", False)

        self.walls = []
        if "walls" in self.layers:
            walls = tileset_map.get_layer_by_name("walls")
            walls_width = walls.width
            walls_height = walls.height
            # path finding uses only grid build of tiles and not world coordinates in pixels
            # 0   => floor (later zeros will be replaced with negative numbers representing actual cost)
            # 100 => wall (not walkable)
            self.path_finding_grid = [[0 for _ in range(walls_width)] for _ in range(walls_height)]

            for x, y, surf in tileset_map.get_layer_by_name("walls").tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                # blocked from walking (wall)
                self.path_finding_grid[y][x] = 100

        # for tileset in tileset_map.tilesets:
        #     if tileset.name == "items":
        #         print(tileset)
        #         from pytmx import TiledTileset
        #         t = TiledTileset()
        #         t.
        self.items = []
        if "items" in self.layers:
            items_layer = tileset_map.get_layer_by_name("items")

            for x, y, tile in items_layer.tiles():
                gid = items_layer.data[y][x]
                name = tileset_map.tile_properties[gid]["item_name"]
                item = ItemSprite(
                    [self.item_sprites],
                    gid,
                    (x * TILE_SIZE, y * TILE_SIZE),
                    # (tile.width, tile.height),
                    name,  # tile.item_name,
                    image=tile,
                    model=self.game.conf.items[name]
                )
                self.items.append(item)
                print(item.model)
            items_layer.visible = False

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

        self.waypoints = {}
        # layer of invisible objects consisting of points that layout a list waypoints to follow by NPCs
        if "waypoints" in self.layers:
            for obj in tileset_map.get_layer_by_name("waypoints"):
                self.waypoints[obj.name] = (obj.points if hasattr(obj, "points") else obj.as_points)

        self.entry_points = {}
        # layer of invisible objects being single points on map where NPCs show up coming from linked map
        if "entry_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("entry_points"):
                self.entry_points[obj.name] = vec(obj.x, obj.y)

        # moved here to avoid circular imports
        from characters import NPC
        # self.notify_npc_event_id  = pygame.event.custom_type()
        self.NPC: list[NPC] = []
        # layer of invisible objects being single points determining where NPCs will spawn
        if "spawn_points" in self.layers:
            for obj in tileset_map.get_layer_by_name("spawn_points"):
                # list of waypoints attached by NPCs name
                waypoint = self.waypoints.get(obj.name, ())
                npc = NPC(
                    self.game,
                    self,
                    [self.draw_sprites],
                    self.shadow_sprites,
                    self.label_sprites,
                    (obj.x, obj.y),
                    obj.name,
                    waypoint
                )
                self.NPC.append(npc)

        if self.is_maze:
            # spawning 4 random NPCs in upper right, lower right, lower left corners and in the middle of the map
            spawn_positions = [
                ((5 + ((self.maze_cols  - 1) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows  - 1) * 6)) * TILE_SIZE + 2),
                ((5)                               * TILE_SIZE + 2, ((7 + (self.maze_rows  - 1) * 6)) * TILE_SIZE + 2),
                ((5 + ((self.maze_cols  - 1) * 6)) * TILE_SIZE + 2, ((7))                             * TILE_SIZE + 2),
                ((5 + ((self.maze_cols // 2) * 6)) * TILE_SIZE + 2, ((7 + (self.maze_rows // 2) * 6)) * TILE_SIZE + 2),
            ]
            for pos in spawn_positions:
                monster_name = random.choice(["Snake_01", "Spider_01", "Spirit_01", "Slime_01",])
                npc = NPC(
                    self.game,
                    self,
                    [self.draw_sprites],
                    self.shadow_sprites,
                    self.label_sprites,
                    pos,
                    monster_name,
                    ()
                )
                self.NPC.append(npc)

            # uncomment to test path finding (A*) performance
            # self.player.waypoints = [
            #     ((5) * TILE_SIZE, (6) * TILE_SIZE),
            #     ((5) * TILE_SIZE, (12) * TILE_SIZE),
            #     ((7) * TILE_SIZE, (12) * TILE_SIZE),
            #     ((7) * TILE_SIZE, (8) * TILE_SIZE),
            #     ((30) * TILE_SIZE, (8) * TILE_SIZE),
            #     ((30) * TILE_SIZE, (12) * TILE_SIZE),
            #     ((23) * TILE_SIZE, (12) * TILE_SIZE),
            #     ((23) * TILE_SIZE, (18) * TILE_SIZE),
            # ]
            # self.player.waypoints_cnt = len(self.player.waypoints)
            # self.player.target = vec(100,100)

        clear_maze_cache()

        # create new renderer (camera)
        self.map_view = pyscroll.BufferedRenderer(
            data = pyscroll.data.TiledMapData(tileset_map),
            size = self.game.screen.get_size(),
            # camera stops at map borders (no black area around), player blocked to be stopped separately
            clamp_camera = True,
        )
        # TODO fix zoom
        # self.map_view.zoom = self.camera.zoom

        if self.entry_point in self.entry_points:
            # set first start position for the Player
            ep = self.entry_points[self.entry_point]
            self.player.pos = vec(ep.x, ep.y)
            self.player.adjust_rect()
        else:
            print("[red]no entry point found!")
            # fallback - put the player in the center of the map
            self.player.pos = self.map_view.map_rect.center

        # Pyscroll supports layered rendering.
        # Our map has several 'under' layers and 'over' layers in relations to Sprites.
        # Sprites (NPCs) are always drawn over the tiles of the layer they are on.
        self.sprites_layer = self.layers.index("sprites")
        # main SpritesGroup holding whole tiled map with all layers and NPCs
        self.group: PyscrollGroup = PyscrollGroup(map_layer = self.map_view, default_layer = self.sprites_layer)

        self.group.add(self.shadow_sprites, layer = self.sprites_layer - 2)
        self.group.add(self.item_sprites,   layer = self.sprites_layer - 1)
        self.group.add(self.label_sprites,  layer = self.sprites_layer + 1)
        # add Player to the group
        self.group.add(self.player, layer=self.sprites_layer)
        # add all NPCs to the group
        self.group.add(self.NPC, layer=self.sprites_layer)

        for x, y, surf in tileset_map.layers[0].tiles():

            # get step cost for all walkable tiles
            # 100 => road, pavement - low cost
            # 150 => grass, dirt - moderate cost
            # 200 => long grass, corn field - high cost
            # 300 => water - high cost
            # stored as negative number to distinguish from walls (positive numbers == 100)
            # this is used in A*
            # path_finding_grid = 0 => floor
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

        self.set_camera_on_player()
        self.group.center(self.camera.target)

        # string with coma separated names of particle systems active in this map
        map_particles = tileset_map.properties.get("particles", "").replace(" ", "").strip().lower().split(",")
        self.particles: list[ParticleSystem] = []
        # init particle systems relevant for this scene
        for particle in map_particles:
            if particle in PARTICLES:
                particle_class = PARTICLES[particle]
                self.particles.append(particle_class(self.game.canvas, self.group, self.camera))
                self.game.register_custom_event(self.particles[-1].custom_event_id, self.particles[-1].add)

    ###################################################################################################################
    def __repr__(self) -> str:
        # MARK: __repr__
        return f"{__class__.__name__}: {self.current_scene}"

    ###################################################################################################################
    def start_intro(self):
        # MARK: start_intro

        self.set_camera_free()
        # ZOOM_ORG     = ZOOM_LEVEL
        ZOOM_WIDE    = 3.10
        ZOOM_CLOSEUP = 3.9
        # in_out_quad out_sine # in_out_elastic - anticipate and overshoot
        # in_out_back - anticipate # in_out_bounce - well, bouncy
        CAMERA_TRANSITION = "out_sine"

        waypoints = self.waypoints["intro"]

        self.intro_cutscene = {
            "steps": [
                # ########## INITIAL SETUP #######################
                {
                    "name": "step_01",
                    "description": "move camera the big tree",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": waypoints[0].x,  "y": waypoints[0].y},
                    "duration": 0.1,
                    "transition": CAMERA_TRANSITION,
                    "from": "<root>",
                    "trigger": "<begin>"
                },
                {
                    "name": "step_01a",
                    "description": "night time",
                    "type": "animation",
                    "target": self,
                    "args": {"hour": 3},
                    "round_values": True,
                    "duration": 0.1,
                    "transition": "linear",
                    "from": "step_01",
                    "trigger": "on finish"
                },
                {
                    "name": "step_02",
                    "description": "show cutscene bars",
                    "type": "animation",
                    "target": self,
                    "args": {"cutscene_framing": 1.00},
                    "duration": 2.0,
                    "transition": "linear",
                    "from": "step_01",
                    "trigger": "on finish"
                },
                {
                    "name": "step_03",
                    "description": "camera zoom out",
                    "type": "animation",
                    "target": self.camera,
                    "args": {"zoom": ZOOM_WIDE},
                    "duration": 2.0,
                    "transition": "linear",
                    "from": "step_01",
                    "trigger": "on finish"
                },
                # ################# START #################
                {
                    "name": "step_04",
                    "description": "move camera to waypoint 1",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": waypoints[1].x,  "y": waypoints[1].y},
                    "duration": 2.0,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_03",
                    "trigger": "on finish"
                },
                {
                    "name": "step_05",
                    "description": "move camera to waypoint 3",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": waypoints[3].x,  "y": waypoints[3].y},
                    "duration": 2.5,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_04",
                    "trigger": "on finish"
                },
                {
                    "name": "step_05a",
                    "description": "move camera to waypoint 7",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": waypoints[7].x,  "y": waypoints[7].y},
                    "duration": 2.5,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_05",
                    "trigger": "on finish"
                },
                {
                    "name": "step_05b",
                    "description": "move camera to waypoint 10 (house)",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": waypoints[10].x,  "y": waypoints[10].y},
                    "duration": 2.5,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_05a",
                    "trigger": "on finish"
                },
                {
                    "name": "step_06",
                    "description": "camera zoom in on village house",
                    "type": "animation",
                    "target": self.camera,
                    "args": {"zoom": ZOOM_CLOSEUP},
                    "duration": 3.0,
                    "transition": "linear",
                    "from": "step_05b",
                    "trigger": "on finish"
                },
                {
                    "name": "step_07",
                    "description": "steady take",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": self.camera.target.x,  "y": self.camera.target.y},
                    "duration": 1.0,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_06",
                    "trigger": "on finish"
                },
                # ############# CLEAN UP ############################
                {
                    "name": "step_08",
                    "description": "move camera back to player pos",
                    "type": "animation",
                    "target": self.camera.target,
                    "args": {"x": self.player.pos.x,  "y": self.player.pos.y},
                    "duration": 1.0,
                    "transition": CAMERA_TRANSITION,
                    "from": "step_07",
                    "trigger": "on finish"
                },
                {
                    "name": "step_08a",
                    "description": "day time",
                    "type": "animation",
                    "target": self,
                    "args": {"hour": 12},
                    "round_values": True,
                    "duration": .250,
                    "transition": "linear",
                    "from": "step_07",
                    "trigger": "on finish"
                },
                {
                    "name": "step_09",
                    "description": "revert camera target to the player",
                    "type": "task",
                    "target": self.set_camera_on_player,
                    "args": {},
                    "interval": 0.1,
                    "times": 1,
                    "from": "step_08",
                    "trigger": "on finish"
                },
                {
                    "name": "step_10",
                    "description": "hide cutscene framing",
                    "type": "animation",
                    "target": self,
                    "args": {"cutscene_framing": 0.0},
                    "duration": 3.0,
                    "transition": "out_quad",
                    "from": "step_08",
                    "trigger": "on finish"
                },
            ]
        }
        animator(self.intro_cutscene, self.animations)

    ###################################################################################################################
    def set_camera_on_player(self):
        self.camera.target = self.player.pos
        self.camera.zoom = ZOOM_LEVEL
        # TODO fix zoom
        # self.map_view.zoom = self.camera.zoom

    ###################################################################################################################
    def set_camera_free(self):
        # release reference to self.player.pos by coping only value
        self.camera.target = self.camera.target.copy()

    ###################################################################################################################
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

    ###################################################################################################################
    def go_to_map(self):
        self.transition.exiting = False
        self.return_scene = self.current_scene
        self.return_entry_point = self.new_scene.return_entry_point

        self.current_scene = self.new_scene.to_map
        # print(f"{self.entry_point=} {self.new_scene.entry_point}")
        self.entry_point = self.new_scene.entry_point
        self.is_maze = self.new_scene.is_maze
        self.maze_cols = self.new_scene.maze_cols
        self.maze_rows = self.new_scene.maze_rows
        self.shadow_sprites.empty()
        self.label_sprites.empty()
        # self.map_view.reload()
        self.player.shadow = self.player.create_shadow(self.shadow_sprites)
        self.player.health_bar = self.player.create_health_bar(self.label_sprites, self.player.pos)

        self.load_map()
        # new_scene = Scene(
        #     self.game,
        #     self.new_scene.to_map,
        #     self.new_scene.entry_point,
        #     self.new_scene.is_maze,
        #     self.new_scene.maze_cols,
        #     self.new_scene.maze_rows
        # )
        # self.exit_state(quit=False)
        # new_scene.enter_state()

    ###################################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]):
        # MARK: update
        global INPUTS

        self.group.update(dt)
        self.animations.update(dt)
        self.transition.update(dt)

        # absolute time calculation
        # self.hour   = int((self.game.time_elapsed + INITIAL_HOUR) % 24)
        # self.minute = int((self.game.time_elapsed + INITIAL_HOUR) % 1 * 60)

        # relative time calculation
        self.minute_f += dt * 60 * GAME_TIME_SPEED
        self.minute = int(self.minute_f)
        if self.minute >= 60:
            self.hour   += 1
            self.minute  = 0
            self.minute_f  -= 60.0
            if self.hour >= 24:
                self.hour = 0

        # check if the Player's feet are colliding with wall
        # Player must have a rect called feet, slide and move_back methods,
        # otherwise this will fail
        if self.player.feet.collidelist(self.walls) > -1:
            # slide along wall or do a step_back
            self.player.slide(self.walls)

        # check if the Player is colliding with an NPC
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

        if INPUTS["intro"]:
            self.start_intro()
            INPUTS["intro"] = False

        global SHOW_HELP_INFO
        if INPUTS["help"]:
            SHOW_HELP_INFO = not SHOW_HELP_INFO
            INPUTS["help"] = False

        if INPUTS["drop"]:
            # drop item from inventory to ground
            if len(self.player.items) > 0:
                item = self.player.drop_item()
                item.pos = self.player.pos
                item.rect.center = self.player.pos
                self.item_sprites.add(item)
                self.group.add(item, layer=self.sprites_layer - 1)
                print(f"Dropped {item.name}[{item.model.type.value}]")
            INPUTS["drop"] = False

        if INPUTS["pick_up"]:
            if not self.player.is_flying:
                items = self.item_sprites.sprites()
                collided_index = self.player.feet.collidelist(items)
                if collided_index > -1:
                    # try to pick up item
                    self.player.pick_up(items[collided_index])
                    self.group.remove(items[collided_index])
                    self.item_sprites.remove(items[collided_index])

            INPUTS["pick_up"] = False

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

        if INPUTS["menu"]:
            # next_scene = None #  self # Scene(self.game, "grasslands", "start")
            # AboutMenuScreen(self.game, next_scene).enter_state()
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
            # self.game.reset_inputs()
            INPUTS["menu"] = False

        if INPUTS["screenshot"]:
            INPUTS["screenshot"] = not self.game.save_screenshot()

        # live reload map
        if INPUTS["reload"]:
            # shadow = self.player.shadow
            self.label_sprites.empty()
            self.draw_sprites.empty()
            self.exit_sprites.empty()
            self.item_sprites.empty()
            self.block_sprites.empty()
            self.shadow_sprites.empty()
            self.group.empty()
            # self.map_view.reload()
            self.player.shadow = self.player.create_shadow(self.shadow_sprites)
            self.player.health_bar = self.player.create_health_bar(self.label_sprites, self.player.pos)
            self.load_map()

            INPUTS["reload"] = False

        # camera zoom in/out
        if INPUTS["zoom_in"]:
            self.camera.zoom += 0.25
            # self.map_view.zoom = self.camera.zoom
            INPUTS["zoom_in"] = False

        if INPUTS["zoom_out"]:
            self.camera.zoom -= 0.25
            if self.camera.zoom < 0.25:
                self.camera.zoom = 0.25
            # self.map_view.zoom = self.camera.zoom
            INPUTS["zoom_out"] = False

    ###################################################################################################################
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

        self.game.render_panel(rect, PANEL_BG_COLOR)

        for i, action in enumerate(show_actions, start=1):
            self.game.render_text(
                f"{', '.join(action['show']):>11} - {action['msg']}",
                (WIDTH - 400, i * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING),
                shadow = True
            )

    ###################################################################################################################
    def draw(self, screen: pygame.Surface, dt: float):
        # MARK: draw
        # center map on player
        # self.group.center(self.player.pos)
        # self.map_view.center(self.camera.target)
        # self.map_view.zoom = self.camera.zoom
        self.group.center(self.camera.target)

        self.group.draw(screen)

        for particle in self.particles:
            particle.emit(dt)

        self.transition.draw(screen)

        # alpha filter demo
        if USE_ALPHA_FILTER:
            self.apply_alpha_filter(screen)

        # draw black bars at the top and bottom when during cutscene
        self.apply_cutscene_framing(screen, self.cutscene_framing)

        if SHOW_DEBUG_INFO:
            self.show_debug()
        else:
            fps = f"FPS: {self.game.fps: 6.1f} 3s: {self.game.avg_fps_3s: 6.1f} 10s: {self.game.avg_fps_10s: 6.1f}"
            self.debug([fps])

        if SHOW_HELP_INFO:
            self.show_help()
        else:
            self.game.render_text(
                "press [h] for help",
                (WIDTH // 2, HEIGHT - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING),
                shadow = True,
                centred = True
            )

    ###################################################################################################################
    def apply_time_of_day_filter(self, screen: pygame.Surface):
        # MARK: apply_time_of_day_filter
        # do not apply night and day filter indoors
        if not self.outdoor and not self.is_maze:
            return

        filter_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        filter: ColorValue = BG_COLOR
        hour: float = self.hour + (self.minute / 60)

        if self.is_maze:
            filter = NIGHT_FILTER
        else:
            if hour < 6 or hour >= 20:
                filter = NIGHT_FILTER
            elif 6 <= hour < 9:
                weight = (hour - 6) / (9 - 6)
                for i in range(4):
                    filter[i] = pygame.math.lerp(NIGHT_FILTER[i], DAY_FILTER[i], weight)
            elif 9 <= hour < 17:
                filter = DAY_FILTER
            elif 17 <= hour < 20:
                weight = (hour - 17) / (20 - 17)
                for i in range(4):
                    filter[i] = pygame.math.lerp(DAY_FILTER[i], NIGHT_FILTER[i], weight)

        filter_surf.fill(filter)

        if filter == NIGHT_FILTER or self.is_maze:
            for npc in self.NPC + [self.player]:
                pos = self.map_view.translate_point(npc.pos + vec(0, -8))
                pygame.draw.circle(filter_surf, DAY_FILTER, pos, 196)
            if "intro" in self.waypoints:
                village_pos = self.waypoints["intro"][0]
                pos = self.map_view.translate_point(village_pos + vec(0, 0))
                pygame.draw.circle(filter_surf, DAY_FILTER, pos, 256)

        #         village_pos = self.waypoints["intro"][-1]
        #         pos = self.map_view.translate_point(village_pos + vec(0, 0))
        #         pygame.draw.circle(filter_surf, DAY_FILTER, pos, 256)

        # rect = self.circle_gradient.get_frect(center = pos)

        # light_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        # light_surf.fill(f)
        # self.circle_gradient.set_alpha(128)
        # light_surf.blit(self.circle_gradient, (0,0))
        # filter_surf.blit(self.circle_gradient, rect)

        # screen.blit(filter_surf, (0, 0))

        # screen.blit(self.circle_gradient, rect)
        # screen.blit(light_surf, rect)

    ###################################################################################################################
    def get_lights(self) -> tuple[list[vec3], float]:
        # return list of light source coordinates with sizes and day/night ratio as float
        # in range [0.0, 1.0] (0.0 ==> day)
        light_sources: list[vec3] = []
        ratio: float = 0.0

        # indoors it's always day except mazes
        # no light sources
        if not self.outdoor and not self.is_maze:
            ratio = 0.0
        else:
            # in maze it's always night
            if self.is_maze:
                ratio = 1.0
            else:
                hour: float = self.hour + (self.minute / 60)
                if hour < 6.00 or hour >= 20.00:
                    ratio = 1.0
                elif 6.00 <= hour < 9.00:
                    ratio = 1.0 - ((hour - 6.00) / (9.00 - 6.00))
                    # for i in range(4):
                    #     filter[i] = pygame.math.lerp(NIGHT_FILTER[i], DAY_FILTER[i], weight)
                elif 9.00 <= hour < 17.00:
                    ratio = 0.0
                elif 17.00 <= hour < 20.00:
                    ratio = (hour - 17.00) / (20.00 - 17.00)
                    # for i in range(4):
                    #     filter[i] = pygame.math.lerp(DAY_FILTER[i], NIGHT_FILTER[i], weight)

            # if it's not full day add light sources
            if ratio > 0.0:
                for npc in self.NPC + [self.player]:
                    pos = self.map_view.translate_point(npc.pos + vec(0, -8))
                    # pos_list = scene.map_view.translate_point(npc.pos + vec(0, -8))
                    light = vec3(pos[0], HEIGHT - pos[1], 64.0)
                    light_sources.append(light)
                    # pygame.draw.circle(filter_surf, DAY_FILTER, pos, 196)
                if "intro" in self.waypoints:
                    village_pos = self.waypoints["intro"][0]
                    pos = self.map_view.translate_point(village_pos + vec(0, 0))
                    light = vec3(pos[0], HEIGHT - pos[1], 64.0)
                    light_sources.append(light)

                    village_pos = self.waypoints["intro"][-1]
                    pos = self.map_view.translate_point(village_pos + vec(0, 0))
                    light = vec3(pos[0], HEIGHT - pos[1], 64.0)
                    light_sources.append(light)
                    # pygame.draw.circle(filter_surf, DAY_FILTER, pos, 256)

        return (light_sources, ratio)

    ###################################################################################################################
    def apply_alpha_filter(self, screen: pygame.Surface):
        # MARK: apply_alpha_filter
        h = HEIGHT // 2
        self.game.render_text("Day",   (0, h - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING))
        self.game.render_text("Night", (0, h +                    TEXT_ROW_SPACING))

        # sunny, warm yellow light during daytime
        half_screen = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
        half_screen.fill(DAY_FILTER)
        screen.blit(half_screen, (0, 0))

        # cold, dark and bluish light at night
        half_screen.fill(NIGHT_FILTER)
        screen.blit(half_screen, (0, h))

    ###################################################################################################################
    def apply_cutscene_framing(self, screen: pygame.Surface, percentage: float):
        # MARK: apply_cutscene_framing
        if percentage <= 0.001:
            return

        surface_h = HEIGHT // 2
        framing_h = int(HEIGHT * 0.1)
        framing_offset = int(framing_h * percentage)
        half_screen = pygame.Surface((WIDTH, surface_h), pygame.SRCALPHA)
        half_screen.fill(CUTSCENE_BG_COLOR)
        # blit a black rect at the top of the screen
        screen.blit(half_screen, (0, -surface_h + framing_offset))
        # blit a black rect at the bottom of the screen
        screen.blit(half_screen, (0, HEIGHT - framing_offset))

    ###################################################################################################################
    def show_debug(self):
        # MARK: show_debug
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
            f"FPS: {self.game.fps: 6.1f} Shader: {shader_name}",
            # f"Eye: x:{self.camera.target.x:6.2f} y:{self.camera.target.y:6.2f}",
            f"Time: {self.hour}:{self.minute:02}",
            # f"vel: {self.player.vel.x: 6.1f} {self.player.vel.y: 6.1f}",
            # f"x  : {self.player.pos.x: 3.0f}   y : {self.player.pos.y: 3.0f}",
            # f"g x:  {self.player.tileset_coord.x: 3.0f} g y : {self.player.tileset_coord.y: 3.0f}",
            # f"up_vel: {self.player.up_vel: 3.1f} up_acc{self.player.up_acc: 3.1f}",
            # f"t x:  {self.player.target.x: 3.0f} t y : {self.player.target.y: 3.0f}",
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
                # f"gx={npc.tileset_coord.x:3} y={npc.tileset_coord.y:3}",
                # f"s ={npc.state} j={npc.is_flying}",
                # f"wc={npc.waypoints_cnt} wn={npc.current_waypoint_no}",
                # f"tx={npc.get_tileset_coord(npc.target).x:3} y={npc.get_tileset_coord(npc.target).y:3}",
            ]
            # draw lines connecting waypoints
            if npc.waypoints_cnt > 0:
                curr_wp = npc.waypoints[npc.current_waypoint_no]
                # add current waypoint as text under NPC
                texts.append(f"cw={npc.get_tileset_coord(curr_wp).x:3} {npc.get_tileset_coord(curr_wp).y:3}")
                prev_point = (npc.pos.x, npc.pos.y - 4)
                for point in list(npc.waypoints)[npc.current_waypoint_no:]:
                    from_p = self.map_view.translate_point(vec(prev_point[0], prev_point[1]))
                    to_p = self.map_view.translate_point(vec(point[0], point[1]))
                    pygame.draw.line(self.game.canvas, WAYPOINTS_LINE_COLOR, from_p, to_p, width=2)
                    prev_point = point

            pos = self.map_view.translate_point(npc.pos)
            self.game.render_texts(texts, pos, font_size=FONT_SIZE_MEDIUM, centred=True)

            # render red square indicating hitbox
            rect = self.map_view.translate_rect(npc.feet)
            pygame.draw.rect(self.game.canvas, "red", rect, width=2)

        # # draw walls (colliders)
        # for y, row in enumerate(self.path_finding_grid):
        #     for x, tile in enumerate(row):
        #         if tile > 0:
        #             rect_w = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        #             rect_s = self.map_view.translate_rect(rect_w)
        #             img = pygame.Surface(rect_s.size, pygame.SRCALPHA)
        #             pygame.draw.rect(img, (0,0,200,64), img.get_rect())
        #             self.game.canvas.blit(img, rect_s)
