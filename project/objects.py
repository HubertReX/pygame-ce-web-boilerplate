import pygame
from settings import BLACK_COLOR, FONT_SIZE_TINY, HUD_DIR, TILE_SIZE, TRANSPARENT_COLOR, load_image, IS_WEB
if IS_WEB:
    from config_model.config import AttitudeEnum, Character, Item
else:
    from config_model.config_pydantic import AttitudeEnum, Character, Item

#######################################################################################################################


class Collider(pygame.sprite.Sprite):
    def __init__(
        self,
        groups: list[pygame.sprite.Group],
        pos: list[int],
        size: list[int],
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

#######################################################################################################################


class Shadow(pygame.sprite.Sprite):
    def __init__(self, groups: list[pygame.sprite.Group], pos: list[int], size: list[int]):
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size)).convert_alpha()
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        self.image.fill(TRANSPARENT_COLOR)
        # self.image.set_colorkey("black")
        pygame.draw.ellipse(self.image, BLACK_COLOR, self.rect)

#######################################################################################################################


class HealthBar(pygame.sprite.Sprite):
    def __init__(self, model: Character, groups: list[pygame.sprite.Group], pos: list[int]):
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

    ###################################################################################################################
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

#######################################################################################################################


class Object(pygame.sprite.Sprite):
    def __init__(
        self,
        groups: list[pygame.sprite.Group],
        pos: list[int],
        image=pygame.Surface((TILE_SIZE, TILE_SIZE)),
        # z: str = "blocks",
    ) -> None:

        super().__init__(groups)

        self.image = image
        self.rect: pygame.FRect = self.image.get_frect(topleft = pos)
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, 0)
        # self.z = z

#######################################################################################################################


class ItemSprite(Object):
    def __init__(
        self,
        groups: list[pygame.sprite.Group],
        gid: int,
        pos: list[int],
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
#######################################################################################################################
