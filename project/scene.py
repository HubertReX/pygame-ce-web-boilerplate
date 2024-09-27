import contextlib
import random
from typing import Any, cast
from rich import print
import game
import menus
import pygame
import pyscroll
import pyscroll.data
from animation import animator
from camera import Camera
from maze_generator import hunt_and_kill_maze
from maze_generator.maze_utils import (
    TILE_SIZE,
    build_tileset_map_from_maze,
    clear_maze_cache,
    get_gid_from_tmx_id
)
from objects import ChestSprite, Collider, EmoteSprite, ItemSprite, Notification, NotificationTypeEnum
from particles import ParticleSystem
from pyscroll.group import PyscrollGroup
from pytmx import TiledMap, TiledObjectGroup, TiledTileLayer
from pytmx.util_pygame import load_pygame
from config_model.config import AttitudeEnum, RaceEnum
from rich_text import RichPanel
from sftext.style import Style
from settings import (
    # ACTIONS,
    # BG_COLOR,
    # CIRCLE_GRADIENT,
    CHEST_OPEN_DISTANCE,
    CUTSCENE_BG_COLOR,
    DAY_FILTER,
    EMOTE_SHEET_DEFINITION,
    EMOTE_SHEET_FILE,
    FONT_COLOR,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    FONT_SIZE_TINY,
    FRIENDLY_WAKE_DISTANCE,
    GAME_TIME_SPEED,
    HEIGHT,
    HUD_SHEET_DEFINITION,
    HUD_SHEET_FILE,
    INITIAL_HOUR,
    INPUTS,
    ITEMS_DIR,
    ITEMS_SHEET_DEFINITION,
    ITEMS_SHEET_FILE,
    MAPS_DIR,
    MAZE_DIR,
    MONSTER_WAKE_DISTANCE,
    NIGHT_FILTER,
    NOTIFICATION_DURATION,
    # PANEL_BG_COLOR,
    PARTICLES,
    SHADERS_NAMES,
    SHOW_DEBUG_INFO,
    TEXT_ROW_SPACING,
    USE_ALPHA_FILTER,
    USE_SHADERS,
    WAYPOINTS_LINE_COLOR,
    WIDTH,
    ZOOM_LEVEL,
    # ColorValue,
    Point,
    to_point,
    tuple_to_vector,
    # to_vector,
    # tuple_to_vector,
    vec,
    vec3,
    vector_to_tuple
)
from state import State
from transition import Transition, TransitionCircle
from ui import NOTIFICATION_TYPE_ICONS, UI


################################################################################################################
# MARK: Scene


class Scene(State):
    def __init__(
            self,
            game: game.Game,
            map_name: str,
            entry_point: str,
            is_maze: bool = False,
            maze_cols: int = 0,
            maze_rows: int = 0
    ) -> None:

        super().__init__(game)
        self.properties: list[str] = [
            "is_maze",
            "maze_cols",
            "maze_rows",
            "waypoints",
            "items",
            "zones",
            "exits",
            "chests",
            "walls",
            "label_sprites",
            "shadow_sprites",
            "chest_sprites",
            "exit_sprites",
            "item_sprites",
            "animations",
            "NPCs",
            "loaded_NPCs",
            "outdoor",
            "layers",
            "path_finding_grid",
            "entry_points",
            "map_view",
            "sprites_layer",
            "group",
            "particles",
        ]

        self.notifications: list[Notification] = []
        self.game.time_elapsed = 0.0
        self.current_map = map_name
        self.loaded_maps: dict[str, Any] = {}
        self.entry_point = entry_point
        self.new_scene: Collider | None = None
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows
        self.waypoints: dict[str, tuple[Point, ...]] = {}
        self.items: list[ItemSprite] = []
        # self.items_defs: dict[str, pygame.Surface] = {}
        self.exits: list[Collider] = []
        self.zones: dict[str, list[pygame.Rect]] = {}
        self.chests: list[ChestSprite] = []
        self.walls: list[pygame.Rect] = []

        self.label_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.shadow_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.chest_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.exit_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.item_sprites: pygame.sprite.Group = pygame.sprite.Group()
        self.animations: pygame.sprite.Group = pygame.sprite.Group()

        # self.transition = Transition(self)
        self.transition = TransitionCircle(self)

        self.icons: dict[str, list[pygame.Surface]] = self.import_sheet(
            str(EMOTE_SHEET_FILE), EMOTE_SHEET_DEFINITION, width=14, height=13)
        self.icons.update(self.import_sheet(
            str(HUD_SHEET_FILE), HUD_SHEET_DEFINITION, width=16, height=16, scale=2)
        )
        self.generate_icons()
        # self.import_emote_sheet(str(EMOTE_SHEET_FILE))
        self.items_sheet: dict[str, list[pygame.Surface]] = self.import_sheet(
            str(ITEMS_SHEET_FILE), ITEMS_SHEET_DEFINITION, width=16, height=16)

        # moved here to avoid circular imports
        from characters import Player
        self.player: Player = Player(
            self.game,
            self,
            self.shadow_sprites,
            self.label_sprites,
            (WIDTH // 2, HEIGHT // 2),
            name="Malachi",
            model_name="Player",
            emotes=self.icons,
        )
        # moved here to avoid circular imports
        from characters import NPC

        self.NPCs: list[NPC] = []
        self.loaded_NPCs: dict[str, NPC] = {}
        # pyscroll renderer (camera)
        self.map_view: pyscroll.BufferedRenderer
        # view target for camera
        self.camera = Camera(self)
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
        self.layers: list[str] = []
        self.path_finding_grid: list[list[int]] = []
        self.entry_points: dict[str, vec] = {}
        self.sprites_layer: int = 0
        self.group: PyscrollGroup
        self.particles: list[ParticleSystem] = []
        # self.circle_gradient: pygame.Surface = (CIRCLE_GRADIENT).convert_alpha()
        self.ui = UI(self, tiny_font=self.game.fonts[FONT_SIZE_SMALL], medium_font=self.game.fonts[FONT_SIZE_MEDIUM])
        # self.load_items_def()
        self.load_map()
        self.start_particles()
        # self.set_camera_on_player()

    #############################################################################################################

    def generate_icons(self) -> None:
        icons = self.icons
        small_font = self.game.fonts[FONT_SIZE_SMALL]
        tiny_font = self.game.fonts[FONT_SIZE_TINY]

        # generate keys with letter buttons (A-Z)
        center = icons["key"][0].get_rect().center
        for letter in range(ord("A"), ord("Z") + 1):
            text_surf = small_font.render(chr(letter), False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -1)
            bg = icons["key"][0].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{chr(letter)}"] = [bg]

        # 0 to 9

        for digit in range(0, 9):
            text_surf = tiny_font.render(str(digit), False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -2)
            bg = icons["key"][0].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{str(digit)}"] = [bg]

        # F1 to F12
        # tiny_font = self.game.fonts[FONT_SIZE_TINY]
        for letter in range(1, 13):
            text_surf = tiny_font.render(f"F{str(letter)}", False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -2)
            bg = icons["key"][0].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_F{str(letter)}"] = [bg]

        # other keys
        for sign in "<>`[]+-":
            text_surf = small_font.render(sign, False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -1)
            bg = icons["key"][0].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{sign}"] = [bg]

    #############################################################################################################

    def add_notification(self, text: str, type: NotificationTypeEnum = NotificationTypeEnum.info) -> None:
        icon = NOTIFICATION_TYPE_ICONS[type]
        label = f":{icon}: {text}"
        parsed_label = RichPanel._parse_text(label)
        label_text, _ = Style.split(parsed_label)
        label_text = label_text.replace("{style}", "")
        # print(label_text)
        label_w, label_h = self.ui.font.size(label_text)
        notification = Notification(type, parsed_label, label_text, label_w, label_h, self.game.time_elapsed)
        self.notifications.append(notification)

    #############################################################################################################
    def remove_old_notifications(self) -> None:
        self.notifications = [n for n in self.notifications
                              if n.create_time  + NOTIFICATION_DURATION  > self.game.time_elapsed]

    #############################################################################################################
    def create_item(self, name: str, x: int, y: int, show: bool = True) -> ItemSprite:
        group = self.item_sprites if show else None
        return ItemSprite(
            group,
            (x, y),
            name,  # tile.item_name,
            image=self.items_sheet[name],
            model=self.game.conf.items[name]
        )

    #############################################################################################################

    # def load_items_def(self) -> None:
    #     items_map = load_pygame(str(ITEMS_DIR / "Items.tmx"))
    #     items_layer = cast(TiledTileLayer, items_map.get_layer_by_name("Items"))

    #     self.items_defs = {}
    #     for x, y, tile in items_layer.tiles():
    #         gid = items_layer.data[y][x]
    #         # skip item defs that don't have item_name property set
    #         if gid not in items_map.tile_properties:
    #             continue

    #         name = items_map.tile_properties[gid]["item_name"]
    #         if name in self.game.conf.items:
    #             self.items_defs[name] = tile
    #         else:
    #             if name:
    #                 print(f"[red]ERROR![/] '{name}' item has no definition in '[b][u]config.json[/u][/b]'")
    #                 self.add_notification(f"[error]ERROR[/error] :red_exclamation: '[item]{name}[/item]'"
    #                                       f"item has no definition in '[b][u]config.json[/u][/b]'",
    #                                       NotificationTypeEnum.debug)

    #############################################################################################################

    def load_map(self) -> None:
        # MARK: load_map

        tileset_map = self.load_tileset_map()

        # setup level geometry with simple pygame rectangles, loaded from pytmx
        self.layers = []
        for layer in tileset_map.layers:
            self.layers.append(layer.name)

        self.outdoor = tileset_map.properties.get("outdoor", False)

        self.load_walls(cast(TiledTileLayer, tileset_map.get_layer_by_name("walls")))

        self.load_items(cast(TiledTileLayer, tileset_map.get_layer_by_name("items")), tileset_map)

        self.load_interactions(cast(TiledTileLayer, tileset_map.get_layer_by_name("interactions")))

        if "zones" in self.layers:
            self.load_zones(cast(TiledTileLayer, tileset_map.get_layer_by_name("zones")))

        self.waypoints = {}
        # layer of invisible objects consisting of points that layout a list waypoints to follow by NPCs
        if "waypoints" in self.layers:
            for obj in cast(TiledObjectGroup, tileset_map.get_layer_by_name("waypoints")):
                self.waypoints[obj.name] = tuple(to_point(point) for point in obj.points)

        self.entry_points = {}
        # layer of invisible objects being single points on map where NPCs show up coming from linked map
        if "entry_points" in self.layers:
            for obj in cast(TiledObjectGroup, tileset_map.get_layer_by_name("entry_points")):
                self.entry_points[obj.name] = vec(obj.x, obj.y)

        # load NPCs only once
        if self.current_map not in self.loaded_maps:
            self.load_NPCs(cast(TiledObjectGroup, tileset_map.get_layer_by_name("spawn_points")))

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

        self.set_entry_point()

        # Pyscroll supports layered rendering.
        # Our map has several 'under' layers and 'over' layers in relations to Sprites.
        # Sprites (NPCs) are always drawn over the tiles of the layer they are on.
        self.sprites_layer = self.layers.index("sprites")

        self.group = PyscrollGroup(map_layer=self.map_view, default_layer=self.sprites_layer)

        # main SpritesGroup holding whole tiled map with all layers and NPCs
        self.populate_sprite_groups()

        self.load_step_cost(tileset_map)

        self.set_camera_on_player()
        # self.group.center(self.camera.target)
        self.group.center(self.player.pos)

        self.load_particles(tileset_map)

        # mark map as loaded
        if self.current_map not in self.loaded_maps:
            self.store_map()

    #############################################################################################################

    def populate_sprite_groups(self) -> None:
        for item in self.items:
            if item not in self.item_sprites:
                self.item_sprites.add(item)

        for exit in self.exits:
            if exit not in self.exit_sprites:
                self.exit_sprites.add(exit)

        for chest in self.chests:
            if chest not in self.chest_sprites:
                self.chest_sprites.add(chest)

        # add all NPCs from current map to the group
        self.NPCs = []
        for npc in self.loaded_NPCs.values():
            if npc.current_map == self.current_map and not npc.is_dead:
                self.NPCs.append(npc)
                self.shadow_sprites.add(npc.shadow)
                self.label_sprites.add(npc.health_bar)
                self.label_sprites.add(npc.emote)
                npc.register_custom_event()

        self.group.add(self.shadow_sprites, layer=self.sprites_layer - 2)
        self.group.add(self.item_sprites,   layer=self.sprites_layer - 1)
        self.group.add(self.label_sprites,  layer=self.sprites_layer + 1)
        self.group.add(self.chest_sprites,  layer=self.sprites_layer - 1)
        # add Player to the group
        self.group.add(self.player, layer=self.sprites_layer)

        self.group.add(self.NPCs, layer=self.sprites_layer)

    #############################################################################################################

    def load_particles(self, tileset_map: TiledMap) -> None:
        map_particles = tileset_map.properties.get("particles", "").replace(" ", "").strip().lower().split(",")
        # string with coma separated names of particle systems active in this map
        self.particles = []
        # init particle systems relevant for this scene
        for particle in map_particles:
            if particle in PARTICLES:
                particle_class = PARTICLES[particle]
                self.particles.append(particle_class(self.game.canvas, self.group, self.camera))

    #############################################################################################################

    def start_particles(self) -> None:
        for particle in self.particles:
            # self.game.unregister_custom_event()
            self.game.register_custom_event(particle.custom_event_id, particle.add)

    #############################################################################################################

    def load_step_cost(self, tileset_map: TiledMap) -> None:
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
                if tile_0_gid and "step_cost" in tile_0_gid:  # .keys():
                    step_cost = tile_0_gid["step_cost"]
                if tile_1_gid and "step_cost" in tile_1_gid:  # .keys():
                    step_cost = tile_1_gid["step_cost"]
                self.path_finding_grid[y][x] = -step_cost

    #############################################################################################################

    def load_interactions(self, exits_layer: TiledTileLayer) -> None:
        self.exits = []
        self.chests = []
        if "interactions" in self.layers:
            for obj in exits_layer:
                if getattr(obj, "obj_type", "") == "exit":
                    exit = Collider(
                        self.exit_sprites,
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
                    self.exits.append(exit)
                elif getattr(obj, "obj_type", "") == "chest":
                    rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    self.walls.append(rect)

                    # blocked from walking (wall)
                    self.path_finding_grid[int(obj.y // TILE_SIZE)][int(obj.x // TILE_SIZE)] = 100

                    # chest = ChestSprite(self.chest_sprites, rect.center,
                    chest = ChestSprite(self.chest_sprites, (obj.x, obj.y),
                                        self.game.conf.chests[obj.name], self.items_sheet,)
                    self.chests.append(chest)

    #############################################################################################################

    def load_zones(self, zones_layer: TiledTileLayer) -> None:
        self.zones = {}
        if "zones" in self.layers:
            for obj in zones_layer:
                if obj.name not in self.zones:
                    self.zones[obj.name] = []
                zone = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                self.zones[obj.name].append(zone)

        # print("[light_green]Zones")
        # for zone_name in self.zones:
        #     print(f"[magenta]{zone_name}[/]", self.zones[zone_name])

    #############################################################################################################

    def load_items(self, items_layer: TiledTileLayer, tileset_map: TiledMap) -> None:
        self.items = []
        self.item_sprites.empty()
        if "items" in self.layers:

            for x, y, tile in items_layer.tiles():
                gid = items_layer.data[y][x]
                name = tileset_map.tile_properties[gid]["item_name"]

                item = self.create_item(name, x * TILE_SIZE, y * TILE_SIZE)
                self.items.append(item)
            items_layer.visible = False

    #############################################################################################################

    def load_walls(self, walls_layer: TiledTileLayer) -> None:
        self.walls = []
        if "walls" in self.layers:
            walls_width = walls_layer.width
            walls_height = walls_layer.height
            # path finding uses only grid build of tiles and not world coordinates in pixels
            # 0   => floor (later zeros will be replaced with negative numbers representing actual cost)
            # 100 => wall (not walkable)
            self.path_finding_grid = [[0 for _ in range(walls_width)] for _ in range(walls_height)]

            for x, y, surf in cast(TiledTileLayer, walls_layer).tiles():
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, surf.get_width(), surf.get_height())
                self.walls.append(rect)
                # blocked from walking (wall)
                self.path_finding_grid[y][x] = 100

    #############################################################################################################

    def load_tileset_map(self) -> TiledMap:
        if self.is_maze:
            # check from which scene we came here
            if len(self.game.states) > 0:
                self.prev_state = self.game.states[-1]

            if self.current_map not in self.loaded_maps:
                # generate new maze
                self.maze = hunt_and_kill_maze.HuntAndKillMaze(self.maze_cols, self.maze_rows)
                self.maze.generate()

            tileset_map: TiledMap = load_pygame(str(MAZE_DIR / "MazeTileset_clean.tmx"))
            # combine tileset clean template with maze grid into final map
            build_tileset_map_from_maze(
                tileset_map,
                self.maze,
                to_map = self.return_map,
                entry_point = self.return_entry_point
            )
        else:
            # load data from pytmx
            tileset_map = load_pygame(str(MAPS_DIR / f"{self.current_map}.tmx"))

        return tileset_map

    #############################################################################################################

    def set_entry_point(self) -> None:
        default = tuple_to_vector(self.map_view.map_rect.center)
        result = self.player.set_entry_point(self.entry_point, default)
        if not result:
            print("\n[red]ERROR![/] no entry point found!\n")
            self.add_notification("[error]ERROR[/error]:red_exclamation: no entry point found",
                                  NotificationTypeEnum.debug)

    #############################################################################################################

    def store_map(self) -> None:
        map: dict[str, Any] = {}
        for property in self.properties:
            # if hasattr(self, property):
            map[property] = getattr(self, property)
        self.loaded_maps[self.current_map] = map

    #############################################################################################################

    def restore_map(self) -> None:
        map = self.loaded_maps[self.current_map]
        for property in map:
            setattr(self, property, map[property])

        # check from which scene we came here
        if len(self.game.states) > 0:
            self.prev_state = self.game.states[-1]

        clear_maze_cache()

        self.set_camera_on_player()
        # self.group.center(self.camera.target)
        self.group.center(self.player.pos)

    #############################################################################################################

    def load_NPCs(self, spawn_points: TiledObjectGroup) -> None:
        # moved here to avoid circular imports
        from characters import NPC

        # layer of invisible objects being single points determining where NPCs will spawn
        if "spawn_points" in self.layers:
            for obj in spawn_points:
                if obj.name not in self.loaded_NPCs:
                    # model = self.game.conf.characters[obj.model_name]
                    # if model.race == RaceEnum.animal and not obj.name.startswith("Chicken"):
                    # if obj.name.startswith("Fish"):
                    #     continue
                    # list of waypoints attached by NPCs name
                    waypoint = self.waypoints.get(obj.name, ())
                    npc = NPC(
                        self.game,
                        self,
                        self.shadow_sprites,
                        self.label_sprites,
                        (obj.x, obj.y),
                        obj.name,
                        self.icons,
                        waypoint,
                        model_name=obj.model_name,
                    )
                    self.loaded_NPCs[obj.name] = npc

        if self.is_maze and self.current_map not in self.loaded_maps:
            # spawning 4 random NPCs in upper right, lower right, lower left corners and in the middle of the map
            spawn_positions: list[tuple[int, int]] = [
                ((5 + ((self.maze_cols  - 1) * 6)) * TILE_SIZE + 2,
                    ((7 + (self.maze_rows  - 1) * 6)) * TILE_SIZE + 2),

                ((5)                               * TILE_SIZE + 2,
                    ((7 + (self.maze_rows  - 1) * 6)) * TILE_SIZE + 2),

                ((5 + ((self.maze_cols  - 1) * 6)) * TILE_SIZE + 2,
                    ((7))                             * TILE_SIZE + 2),

                ((5 + ((self.maze_cols // 2) * 6)) * TILE_SIZE + 2,
                    ((7 + (self.maze_rows // 2) * 6)) * TILE_SIZE + 2),
            ]
            id: int = 0
            for pos in spawn_positions:
                model_name = random.choice(["Snake_01", "Spider_01", "Spirit_01", "Slime_01",])
                id += 1
                name = f"{model_name}_{id:03}"
                npc = NPC(
                    self.game,
                    self,
                    self.shadow_sprites,
                    self.label_sprites,
                    pos,
                    name,
                    self.icons,
                    (),
                    model_name=model_name,
                )
                self.loaded_NPCs[name] = npc

            for _ in range(4):
                repeat: bool = True
                while repeat:
                    x_r: int = random.randint(1, 5)
                    y_r: int = random.randint(1, 5)
                    pos_r: tuple[int, int] = ((5 + (x_r * 6)) * TILE_SIZE + 2, (7 + y_r * 6) * TILE_SIZE + 2)
                    if pos_r not in spawn_points:
                        spawn_points.append(pos_r)
                        repeat = False

                model_name = random.choice(["Snake_01", "Spider_01", "Spirit_01", "Slime_01",])
                id += 1
                name = f"{model_name}_{id:03}"

                npc = NPC(
                    self.game,
                    self,
                    self.shadow_sprites,
                    self.label_sprites,
                    pos_r,
                    name,
                    self.icons,
                    (),
                    model_name=model_name,
                )
                self.loaded_NPCs[name] = npc

    #############################################################################################################

    @staticmethod
    def import_sheet(
        sheet_path: str,
        sheet_definition: dict[str, list[tuple[int, int]]],
        width: int, height: int,
        scale: int = 1,
    ) -> dict[str, list[pygame.Surface]]:
        """
        Load sprite sheet and cut it into animation names and frames using EMOTE_SHEET_DEFINITION dict.
        """
        result: dict[str, list[pygame.Surface]] = {}
        img = pygame.image.load(sheet_path).convert_alpha()
        if scale != 1:
            img = pygame.transform.scale_by(img, scale)
        img_rect = img.get_rect()

        for key, definition in sheet_definition.items():
            anim = []
            for coord in definition:
                x, y = coord
                rec = pygame.Rect(x * width * scale, y * height * scale, width * scale, height * scale)
                if rec.colliderect(img_rect):
                    img_part = img.subsurface(rec)
                    anim.append(img_part)
                else:
                    print(
                        f"[red]ERROR![/] coordinate {x}x{y} "
                        f"not inside sprite sheet for '{key}' animation")
                    # self.add_notification(
                    #     f"[error]ERROR[/error]:red_exclamation: {self.current_map}: coordinate {
                    #         x}x{y} not inside sprite sheet for '{key}' animation",
                    #     NotificationTypeEnum.debug)
                    continue
            if anim:
                result[key] = anim

        return result

    #############################################################################################################

    def __repr__(self) -> str:
        # MARK: __repr__
        return f"{self.__class__.__name__}: {self.current_map}"

    #############################################################################################################
    def start_intro(self) -> None:
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

    #############################################################################################################
    def set_camera_on_player(self) -> None:
        self.camera.target = self.player.pos
        self.camera.zoom = ZOOM_LEVEL
        # TODO fix zoom
        # self.map_view.zoom = self.camera.zoom

    #############################################################################################################
    def set_camera_free(self) -> None:
        # release reference to self.player.pos by coping only value
        self.camera.target = self.camera.target.copy()

    #############################################################################################################
    # def go_to_scene(self) -> None:
    #     if not self.new_scene:
    #         return

    #     self.transition.exiting = False
    #     new_scene = Scene(
    #         self.game,
    #         self.new_scene.to_map,
    #         self.new_scene.entry_point,
    #         self.new_scene.is_maze,
    #         self.new_scene.maze_cols,
    #         self.new_scene.maze_rows
    #     )
    #     self.exit_state(quit=False)
    #     new_scene.enter_state()

    #############################################################################################################
    def go_to_map(self) -> None:
        if not self.new_scene:
            return

        self.return_map = self.current_map
        self.return_entry_point = self.new_scene.return_entry_point

        self.current_map = self.new_scene.to_map
        # print(f"{self.entry_point=} {self.new_scene.entry_point}")
        self.entry_point = self.new_scene.entry_point
        self.is_maze = self.new_scene.is_maze
        self.maze_cols = self.new_scene.maze_cols
        self.maze_rows = self.new_scene.maze_rows

        if self.current_map not in self.loaded_maps:
            self.reset_sprite_groups()
            self.player.shadow = self.player.create_shadow()
            self.player.emote = self.player.create_emote()
            self.player.health_bar = self.player.create_health_bar()
            self.load_map()
        else:
            self.reset_sprite_groups()

            self.restore_map()
            self.set_entry_point()

            self.player.shadow = self.player.create_shadow()
            self.player.emote = self.player.create_emote()
            self.player.health_bar = self.player.create_health_bar()

            self.game.unregister_custom_events()
            self.populate_sprite_groups()

        self.start_particles()
        self.transition.exiting = False

    #############################################################################################################
    def update(self, dt: float, events: list[pygame.event.EventType]) -> None:
        # MARK: update
        global INPUTS

        self.remove_old_notifications()
        self.ui.update(events)

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
            # collision with body of NPC
            collided_index = self.player.feet.collidelist(self.NPCs)  # type: ignore[type-var]
            if collided_index > -1 and not self.player.is_stunned:
                oponent = self.NPCs[collided_index]
                # if self.player.mask.overlap(
                #     oponent.mask,
                #     (oponent.rect.x - self.player.rect.x, oponent.rect.y - self.player.rect.y)
                # ):

                # engage fight with enemy or push back friendly NPC
                self.player.encounter(oponent)
                # slide along wall or do a step_back
                self.player.slide(self.NPCs)

            # collision of weapon with other NPC
            if self.player.is_attacking and self.player.selected_weapon:
                collided_index = self.player.selected_weapon.rect.collidelist(self.NPCs)  # type: ignore[type-var]
                # collided with weapon rect
                if collided_index > -1:
                    oponent = self.NPCs[collided_index]
                    # weapon rect is big, check if it collides with the mask of weapon
                    if self.player.selected_weapon.mask.overlap(
                        oponent.mask,
                        (oponent.rect.x - self.player.selected_weapon.rect.x,  # type: ignore[union-attr]
                         oponent.rect.y - self.player.selected_weapon.rect.y)  # type: ignore[union-attr]
                    ):
                        # deal damage with weapon to enemy or nothing if friendly NPC
                        self.player.hit(self.NPCs[collided_index])

        colliders = self.walls
        # if self.player.is_flying:
        #     colliders = self.walls
        # else:
        #     colliders = self.walls + [self.player]

        self.player.chest_in_range = None
        for chest in self.chests:
            # if self.player.feet.colliderect(chest.rect):
            distance_from_player = (chest.rect.center - self.player.pos).magnitude_squared()
            # chest_model = self.game.conf.chests[chest]
            if distance_from_player < CHEST_OPEN_DISTANCE**2 and chest.model.is_closed:
                self.player.chest_in_range = chest
                break

        self.player.npc_met = None
        for npc in self.NPCs:
            npc.npc_met = None
            if npc.feet.collidelist(colliders) > -1:
                # npc.move_back(dt)
                npc.slide(colliders)

            distance_from_player = (npc.pos - self.player.pos).magnitude_squared()
            # enable talk to npc when player is near
            if npc.model.attitude == AttitudeEnum.friendly:
                if distance_from_player < FRIENDLY_WAKE_DISTANCE**2:
                    npc.health_bar.show()

                    if npc.has_dialog and npc.dialogs:
                        self.player.npc_met = npc
                        npc.npc_met = self.player
                        break
                else:
                    npc.health_bar.hide()

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

        # global USE_ALPHA_FILTER
        # if INPUTS["alpha"]:
        #     USE_ALPHA_FILTER = not USE_ALPHA_FILTER
        #     INPUTS["alpha"] = False

        if INPUTS["intro"]:
            self.start_intro()
            INPUTS["intro"] = False

        if INPUTS["help"]:
            self.ui.show_help_info = not self.ui.show_help_info
            INPUTS["help"] = False

        if INPUTS["use_item"]:
            self.player.use_item()
            INPUTS["use_item"] = False

        for idx in range(1, 7):
            if INPUTS[f"item_{idx}"]:
                if idx - 1 < len(self.player.items):
                    self.player.selected_item_idx = idx - 1
                INPUTS[f"item_{idx}"] = False

        if INPUTS["next_item"]:
            if len(self.player.items) > 0:
                self.player.selected_item_idx += 1
                if self.player.selected_item_idx >= len(self.player.items):
                    self.player.selected_item_idx = 0
            INPUTS["next_item"] = False

        if INPUTS["prev_item"]:
            if len(self.player.items) > 0:
                self.player.selected_item_idx -= 1
                if self.player.selected_item_idx < 0:
                    self.player.selected_item_idx = len(self.player.items) - 1
            INPUTS["prev_item"] = False

        if INPUTS["drop"]:
            # drop item from inventory to ground
            if len(self.player.items) > 0 and not self.player.is_attacking and not self.player.is_stunned:
                if item := self.player.drop_item():
                    self.items.append(item)
                    self.item_sprites.add(item)
                    self.group.add(item, layer=self.sprites_layer - 1)

                    # print(f"Dropped '[item]{item.name}[/item]' [[magenta]{item.model.type}[/magenta]]")
                    self.add_notification(
                        f"Dropped '[item]{item.name}[/item]'", NotificationTypeEnum.info)
                else:
                    print("[red]ERROR![/red] No item to drop!")
            INPUTS["drop"] = False

        if INPUTS["pick_up"]:
            if not self.player.is_flying and not self.player.is_attacking and not self.player.is_stunned:
                items: list[ItemSprite] = self.item_sprites.sprites()
                collided_index = self.player.feet.collidelist(items)   # type: ignore[type-var]
                if collided_index > -1:
                    item = items[collided_index]
                    if self.player.pick_up(item):
                        self.add_notification(f"Picked up '[item]{item.name}[/item]'", NotificationTypeEnum.success)
                        with contextlib.suppress(KeyError):
                            # if self.group.has(item):
                            self.group.remove(item)
                            if item in self.items:
                                self.items.remove(item)
                            if item in self.item_sprites:
                                self.item_sprites.remove(item)
                    # else:
                    #     print(f"You can't pick up '{item.model.name}' - it's too heavy.")
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
            if not self.player.is_flying and not self.player.is_attacking and \
                not self.player.is_stunned and not self.player.is_jumping and \
                    not self.player.is_talking:
                self.player.is_jumping = True
                self.player.jump()
                # when airborn move one layer above so it's not colliding with obstacles on the ground
                self.group.change_layer(self.player, self.sprites_layer + 1)

            INPUTS["jump"] = False

        if INPUTS["fly"]:
            # toggle flying mode
            if not self.player.is_jumping and not self.player.is_attacking and not self.player.is_stunned:
                self.player.is_flying = not self.player.is_flying
                if self.player.is_flying:
                    # when airborn move one layer above so it's not colliding with obstacles on the ground
                    self.group.change_layer(self.player, self.sprites_layer + 1)
                else:
                    self.group.change_layer(self.player, self.sprites_layer)

            INPUTS["fly"] = False

        if INPUTS["menu"]:
            # next_scene = None #  self # Scene(self.game, "grasslands", "start")
            # AboutMenuScreen(self.game, next_scene).enter_state()
            menus.MainMenuScreen(self.game, "MainMenu").enter_state()
            # self.game.reset_inputs()
            INPUTS["menu"] = False

        # live reload map
        if INPUTS["reload"]:
            self.reload_map()
            self.ui.reset()
            INPUTS["reload"] = False

        # camera zoom in/out
        if INPUTS["zoom_in"]:
            self.camera.zoom += 0.25
            # self.map_view.zoom = self.camera.zoom
            INPUTS["zoom_in"] = False

        if INPUTS["zoom_out"]:
            self.camera.zoom -= 0.25
            self.camera.zoom = max(self.camera.zoom, 0.25)
            # self.map_view.zoom = self.camera.zoom
            INPUTS["zoom_out"] = False

    # TODO Rename this here and in `update`
    def reload_map(self) -> None:
        self.game.time_elapsed = 0.0
        self.hour = INITIAL_HOUR
        self.minute = 0
        self.minute_f = 0.0

        # shadow = self.player.shadow
        self.reset_sprite_groups()
        # self.map_view.reload()
        self.player.reset()
        self.load_map()
        self.start_particles()

    def reset_sprite_groups(self) -> None:
        self.label_sprites.empty()
        self.exit_sprites.empty()
        self.item_sprites.empty()
        self.chest_sprites.empty()
        self.shadow_sprites.empty()
        self.group.empty()

    #############################################################################################################

    def draw(self, screen: pygame.Surface, dt: float) -> None:
        # MARK: draw
        # center map on player
        self.group.center(self.player.pos)
        # self.map_view.center(self.camera.target)
        # self.map_view.zoom = self.camera.zoom
        # self.group.center(self.camera.target)

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
        # else:
        #     pass
            # fps = f"FPS: {self.game.fps: 6.1f}"
            # # 3s: {self.game.avg_fps_3s: 6.1f} 10s: {self.game.avg_fps_10s: 6.1f}"
            # stats = f"Health: {
            #     self.player.model.health}/{self.player.model.max_health} Money: {self.player.model.money}"

            # inventory_list = []
            # for idx, item in enumerate(self.player.items):
            #     label = f"{item.model.name}[{item.model.type.value[0].upper()}][{item.model.count}]"
            #     if idx == self.player.selected_item_idx:
            #         label = f"-->{label}<--"
            #     inventory_list.append(label)

            # weight = f"{self.player.total_items_weight:4.2f}/{self.player.model.max_carry_weight:4.2f}"
            # inventory = ", ".join(inventory_list)
            # weapon = f"{self.player.selected_weapon.model.name}[{
            #     self.player.selected_weapon.model.damage}]" if self.player.selected_weapon else "n/a"

            # self.debug([fps, stats, f"Items[{weight}]: {inventory}", f"Weapon: {weapon}"])

        self.ui.display_ui(self.game.time_elapsed)

    #############################################################################################################

    # def apply_time_of_day_filter(self, screen: pygame.Surface) -> None:
    #     # MARK: apply_time_of_day_filter
    #     # do not apply night and day filter indoors
    #     if not self.outdoor and not self.is_maze:
    #         return

    #     filter_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    #     filter: pygame._common.ColorValue = BG_COLOR
    #     hour: float = self.hour + (self.minute / 60)

    #     if self.is_maze:
    #         filter = NIGHT_FILTER
    #     else:
    #         if hour < 6 or hour >= 20:
    #             filter = NIGHT_FILTER
    #         elif 6 <= hour < 9:
    #             weight = (hour - 6) / (9 - 6)
    #             for i in range(4):
    #                 filter[i] = pygame.math.lerp(NIGHT_FILTER[i], DAY_FILTER[i], weight)
    #         elif 9 <= hour < 17:
    #             filter = DAY_FILTER
    #         elif 17 <= hour < 20:
    #             weight = (hour - 17) / (20 - 17)
    #             for i in range(4):
    #                 filter[i] = pygame.math.lerp(DAY_FILTER[i], NIGHT_FILTER[i], weight)

    #     filter_surf.fill(filter)

    #     if filter == NIGHT_FILTER or self.is_maze:
    #         for npc in self.NPC + [self.player]:
    #             pos = self.map_view.translate_point(npc.pos + vec(0, -8))
    #             pygame.draw.circle(filter_surf, DAY_FILTER, pos, 196)
    #         if "intro" in self.waypoints:
    #             village_pos = self.waypoints["intro"][0]
    #             pos = self.map_view.translate_point(village_pos + vec(0, 0))
    #             pygame.draw.circle(filter_surf, DAY_FILTER, pos, 256)

    #############################################################################################################

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
                else:
                    ratio = (hour - 17.00) / (20.00 - 17.00)
            # if it's not full day add light sources
            if ratio > 0.0:
                for npc in self.NPCs + [self.player]:
                    pos = self.map_view.translate_point(npc.pos + vec(0, -8))
                    # pos_list = scene.map_view.translate_point(npc.pos + vec(0, -8))
                    light = vec3(pos[0], HEIGHT - pos[1], 64.0)
                    light_sources.append(light)
                    # pygame.draw.circle(filter_surf, DAY_FILTER, pos, 196)
                if "intro" in self.waypoints:
                    self.get_light_from_intro(light_sources)
                    # pygame.draw.circle(filter_surf, DAY_FILTER, pos, 256)

        return (light_sources, ratio)

    #############################################################################################################
    def get_light_from_intro(self, light_sources: list[vec3]) -> None:
        village_pos = self.waypoints["intro"][0].as_vector
        pos = self.map_view.translate_point(village_pos + vec(0, 0))
        light = vec3(pos[0], HEIGHT - pos[1], 64.0)
        light_sources.append(light)

        village_pos = self.waypoints["intro"][-1].as_vector
        pos = self.map_view.translate_point(village_pos + vec(0, 0))
        light = vec3(pos[0], HEIGHT - pos[1], 64.0)
        light_sources.append(light)

    #############################################################################################################
    def apply_alpha_filter(self, screen: pygame.Surface) -> None:
        # MARK: apply_alpha_filter
        h = HEIGHT // 2
        self.game.render_text("Day",   (0, int(h - FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)))
        self.game.render_text("Night", (0, int(h +                    TEXT_ROW_SPACING)))

        # sunny, warm yellow light during daytime
        half_screen = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
        half_screen.fill(DAY_FILTER)
        screen.blit(half_screen, (0, 0))

        # cold, dark and bluish light at night
        half_screen.fill(NIGHT_FILTER)
        screen.blit(half_screen, (0, h))

    #############################################################################################################
    def apply_cutscene_framing(self, screen: pygame.Surface, percentage: float) -> None:
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

    #############################################################################################################
    def show_debug(self) -> None:
        # MARK: show_debug
        # prepare shader info

        # shader_index = SHADERS_NAMES.index(self.game.shader.shader_name)
        # shader_index = max(shader_index, 0)
        # shader_name = SHADERS_NAMES[shader_index] if USE_SHADERS else "n/a"
        # prepare debug messages displayed in upper left corner
        # msgs = [
        #     f"FPS: {self.game.fps: 5.1f} Shader: {shader_name}",
        #     # f"Eye: x:{self.camera.target.x:6.2f} y:{self.camera.target.y:6.2f}",
        #     f"Time: {self.hour}:{self.minute:02}",
        #     # f"vel: {self.player.vel.x: 6.1f} {self.player.vel.y: 6.1f}",
        #     # f"x  : {self.player.pos.x: 3.0f}   y : {self.player.pos.y: 3.0f}",
        #     # f"g x:  {self.player.tileset_coord.x: 3.0f} g y : {self.player.tileset_coord.y: 3.0f}",
        #     # f"up_vel: {self.player.up_vel: 3.1f} up_acc{self.player.up_acc: 3.1f}",
        #     # f"t x:  {self.player.target.x: 3.0f} t y : {self.player.target.y: 3.0f}",
        #     # f"offset: {self.player.jumping_offset: 6.1f}",
        #     # f"col: {self.player.rect.collidelist(self.walls):06.02f}",
        #     # f"bored={self.player.state.enter_time: 5.1f} time_elapsed={self.game.time_elapsed: 5.1f}",
        # ]
        # self.debug(msgs)

        # display npc (and players) debug messages
        for npc in self.NPCs + [self.player]:
            # prepare text displayed under NPC
            texts = [
                npc.name,
                f"px={npc.pos.x // 1:3} y={(npc.pos.y - 4) // 1:3}",
                # f"gx={npc.tileset_coord.x:3} y={npc.tileset_coord.y:3}",
                # f"s ={npc.state} j={npc.is_flying}",
                f"st ={npc.state} sp = {npc.speed}",
                # f"wc={npc.waypoints_cnt} wn={npc.current_waypoint_no}",
                # f"tx={npc.get_tileset_coord(npc.target).x:3} y={npc.get_tileset_coord(npc.target).y:3}",
            ]
            # draw lines connecting waypoints
            if npc.waypoints_cnt > 0:
                # curr_wp = npc.waypoints[npc.current_waypoint_no]
                # add current waypoint as text under NPC
                # texts.append(f"cw={npc.get_tileset_coord(curr_wp).x:3} {npc.get_tileset_coord(curr_wp).y:3}")
                prev_point = Point(int(npc.pos.x), int(npc.pos.y - 4))
                for point in list(npc.waypoints)[npc.current_waypoint_no:]:
                    from_p = self.map_view.translate_point(vec(prev_point.x, prev_point.y))
                    to_p = self.map_view.translate_point(vec(point.x, point.y))
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
