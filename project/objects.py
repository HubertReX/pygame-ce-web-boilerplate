import pygame
from settings import BLACK_COLOR, FONT_SIZE_TINY, HUD_DIR, PANEL_BG_COLOR, \
    TILE_SIZE, TRANSPARENT_COLOR, load_image, IS_WEB

if IS_WEB:
    from config_model.config import AttitudeEnum, Character, Item, ItemTypeEnum
else:
    from config_model.config_pydantic import AttitudeEnum, Character, Item, ItemTypeEnum

#################################################################################################################


class Collider(pygame.sprite.Sprite):
    def __init__(
        self,
        groups: pygame.sprite.Group,
        pos: tuple[int, int],
        size: tuple[int, int],
        name: str,
        to_map: str,
        entry_point: str,
        is_maze: bool,
        maze_cols: int,
        maze_rows: int,
        return_entry_point: str = ""
    ) -> None:

        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size))
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.name = name
        self.to_map = to_map
        self.entry_point = entry_point
        self.is_maze = is_maze
        self.maze_cols = maze_cols
        self.maze_rows = maze_rows
        self.return_entry_point = return_entry_point

#################################################################################################################


class Shadow(pygame.sprite.Sprite):
    def __init__(self, groups: pygame.sprite.Group, pos: tuple[int, int], size: tuple[int, int]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size)).convert_alpha()
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.image.fill(TRANSPARENT_COLOR)
        # self.image.set_colorkey("black")
        pygame.draw.ellipse(self.image, BLACK_COLOR, self.rect)

#################################################################################################################


class HealthBarUI(pygame.sprite.Sprite):
    def __init__(self, model: Character, groups: pygame.sprite.Group, pos: tuple[int, int], scale: int) -> None:
        super().__init__(groups)
        # self.image: pygame.Surface = pygame.Surface((70 * scale * TILE_SIZE, 16 * scale * TILE_SIZE)).convert_alpha()
        self.model = model

        self.image_full: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniProgress.png").convert_alpha()
        self.image_empty: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniUnder.png").convert_alpha()
        # self.image = pygame.transform.scale(self.image, (scale * TILE_SIZE, scale * TILE_SIZE))
        self.image_full = pygame.transform.scale(
            self.image_full, (scale * self.image_full.get_width(), scale * self.image_full.get_height()))
        self.image_empty = pygame.transform.scale(
            self.image_empty, (scale * self.image_empty.get_width(), scale * self.image_empty.get_height()))
        self.image: pygame.Surface = pygame.Surface(self.image_full.get_size()).convert_alpha()
        # self.image: pygame.Surface = pygame.Surface((700, 200)).convert_alpha()
        self.image.fill(TRANSPARENT_COLOR)

        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.rect_full: pygame.FRect = self.image_full.get_frect(topleft = pos)
        # self.rect_full.x = self.rect.left
        # self.rect_full.y += 1
        if self.model.attitude == AttitudeEnum.enemy.value:
            self.color = "red"
        elif self.model.attitude == AttitudeEnum.friendly.value:
            self.color = "blue"
        elif self.model.attitude == AttitudeEnum.afraid.value:
            self.color = "green"
        else:
            self.color = "pink"

    #############################################################################################################
    def set_bar(self, percentage: float, pos: tuple[int, int]) -> None:
        self.rect.topleft = pos
        self.rect_full.topleft = pos
        # self.rect_full.left += 50
        # draw empty bar
        self.image.fill(TRANSPARENT_COLOR)  # TRANSPARENT_COLOR) PANEL_BG_COLOR

        # # leave image fully transparent (hide labels)
        # if percentage < 0.0:
        #     return

        # self.image.blit(self.image_full, self.rect_full.topleft)
        self.image.blit(self.image_full, (0, 0))

        percentage = min(1.0, percentage)
        percentage = max(0.0, percentage)
        width = int(self.rect_full.width * percentage)
        rect = pygame.Rect(width, 0, self.rect_full.width - width, self.image_full.get_height())
        tmp_img = self.image_empty.subsurface(rect)

        self.image.blit(tmp_img, (self.rect_full.left + width, 0))

#################################################################################################################


class HealthBar(pygame.sprite.Sprite):
    def __init__(self, model: Character, groups: pygame.sprite.Group, pos: tuple[int, int]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((70, 16)).convert_alpha()
        self.image.fill(TRANSPARENT_COLOR)
        self.model = model
        self.image_full: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniProgress.png").convert_alpha()
        self.image_empty: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniUnder.png").convert_alpha()
        self.rect: pygame.FRect = self.image.get_frect(midtop = pos)
        self.rect_full: pygame.FRect = self.image_full.get_frect()
        self.rect_full.x = self.rect.width // 2 - self.rect_full.width // 2
        self.rect_full.y += 1
        if self.model.attitude == AttitudeEnum.enemy.value:
            self.color = "red"
        elif self.model.attitude == AttitudeEnum.friendly.value:
            self.color = "blue"
        elif self.model.attitude == AttitudeEnum.afraid.value:
            self.color = "green"
        else:
            self.color = "pink"

    #############################################################################################################
    def set_bar(self, percentage: float, game) -> None:
        self.image.fill(TRANSPARENT_COLOR)

        # leave image fully transparent (hide labels)
        if percentage < 0.0:
            return

        self.image.blit(self.image_full, self.rect_full.topleft)

        percentage = min(1.0, percentage)
        percentage = max(0.0, percentage)
        width = int(self.rect_full.width * percentage)
        rect = pygame.Rect(width, 0, self.rect_full.width - width, self.image_full.get_height())
        tmp_img = self.image_empty.subsurface(rect)

        self.image.blit(tmp_img, (self.rect_full.left + width, 1))

        game.render_text(
            self.model.name,
            (self.rect.width // 2, 10),
            self.color,
            font_size=FONT_SIZE_TINY,
            shadow=True,
            centred=True,
            surface=self.image
        )

#################################################################################################################


class Object(pygame.sprite.Sprite):
    def __init__(
        self,
        groups: pygame.sprite.Group,
        pos: tuple[int, int],
        image=pygame.Surface((TILE_SIZE, TILE_SIZE)),
        # z: str = "blocks",
    ) -> None:

        super().__init__(groups)

        self.image = image
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, 0)
        # self.z = z

#################################################################################################################


class ItemSprite(Object):
    def __init__(
        self,
        groups: pygame.sprite.Group,
        gid: int,
        pos: tuple[int, int],
        # z: str = "blocks",
        name: str,
        model: Item,
        image=pygame.Surface((TILE_SIZE, TILE_SIZE)),
    ) -> None:

        super().__init__(groups, pos, image)
        # decrease the size of rectangle for collisions aka. hitbox
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, -self.rect.height / 2)
        self.gid = gid
        self.name = name
        self.model = model
        if model.type == ItemTypeEnum.weapon:
            self.image_directions: dict[str, pygame.Surface] = {}
            self.image_directions["down"] = image
            self.image_directions["up"] = pygame.transform.flip(image, False, True)
            self.image_directions["left"] = pygame.transform.rotate(image, -90)
            self.image_directions["right"] = pygame.transform.rotate(image, 90)

#################################################################################################################
