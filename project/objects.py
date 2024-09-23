from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Callable
import pygame

from settings import (
    BLACK_COLOR,
    CHAR_NAME_COLOR,
    FONT_SIZE_HUGE,
    FONT_SIZE_TINY,
    HUD_DIR,
    IS_WEB,
    PANEL_BG_COLOR,
    TILE_SIZE,
    TRANSPARENT_COLOR,
    load_image,
)

import game
if IS_WEB:
    from config_model.config import AttitudeEnum, Character, Item, ItemTypeEnum, Chest
else:
    from config_model.config_pydantic import AttitudeEnum, Character, Item  # type: ignore[assignment]
    from config_model.config_pydantic import ItemTypeEnum, Chest  # type: ignore[assignment]

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
class InventorySlot(pygame.sprite.Sprite):
    def __init__(self, item_model: Item | None, pos: tuple[int, int], scale: int) -> None:
        super().__init__()
        # self.image: pygame.Surface = pygame.Surface((70 * scale * TILE_SIZE, 16 * scale * TILE_SIZE)).convert_alpha()
        self.item_model = item_model

        self.image_full: pygame.Surface = load_image(HUD_DIR / "inventorySlot.png").convert_alpha()
        self.image_selector: pygame.Surface = load_image(HUD_DIR / "hotbar_selector.png").convert_alpha()

        if scale != 1:
            self.image_full = pygame.transform.scale(
                self.image_full, (scale * self.image_full.get_width(),
                                  scale * self.image_full.get_height()))

            self.image_selector = pygame.transform.scale(
                self.image_selector, (scale * self.image_selector.get_width(),
                                      scale * self.image_selector.get_height()))

        self.rect_full: pygame.Rect = self.image_full.get_rect(topleft = pos)

        self.image: pygame.Surface = self.image_full.subsurface(0, 0, self.rect_full.width, self.rect_full.width)
        self.image_selected: pygame.Surface = self.image_full.subsurface(
            0, self.rect_full.width, self.rect_full.width, self.rect_full.width)
        # self.image: pygame.Surface = pygame.Surface(self.image.get_size()).convert_alpha()
        # self.image.fill(TRANSPARENT_COLOR)

        self.rect: pygame.Rect = self.image.get_rect(topleft = pos)
        self.rect_selected: pygame.Rect = self.image_selected.get_rect(topleft = pos)
        self.rect_selector: pygame.Rect = self.image_selector.get_rect(topleft = pos)
        # self.rect_full: pygame.FRect = self.image.get_frect(topleft = pos)

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
        self.color: pygame._common.ColorValue = "white"
        if self.model.attitude == AttitudeEnum.enemy.value:
            self.color = "red"
        elif self.model.attitude == AttitudeEnum.friendly.value:
            self.color = CHAR_NAME_COLOR
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

        self.image.blit(tmp_img, (width, 0))

#################################################################################################################


class HealthBar(pygame.sprite.Sprite):
    def __init__(self,
                 model: Character,
                 groups: pygame.sprite.Group,
                 pos: tuple[int, int],
                 #  translate_pos: Callable
                 ) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((100, 20)).convert_alpha()
        self.image.fill(TRANSPARENT_COLOR)
        self.model = model
        self.translate_pos: Callable = lambda pos:  pos
        self.image_full: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniProgress.png").convert_alpha()
        self.image_empty: pygame.Surface = load_image(HUD_DIR / "LifeBarMiniUnder.png").convert_alpha()
        self.rect: pygame.FRect = self.image.get_frect(midtop = pos)
        self.rect_full: pygame.FRect = self.image_full.get_frect()
        self.rect_full.x = self.rect.width // 2 - self.rect_full.width // 2
        self.rect_full.y += 1
        self.color: pygame._common.ColorValue = "white"
        if self.model.attitude == AttitudeEnum.enemy.value:
            self.color = "red"
        elif self.model.attitude == AttitudeEnum.friendly.value:
            self.color = CHAR_NAME_COLOR
        elif self.model.attitude == AttitudeEnum.afraid.value:
            self.color = "green"
        else:
            self.color = "pink"

    #############################################################################################################
    def set_bar(self, percentage: float, game: "game.Game") -> None:
        self.image.fill(TRANSPARENT_COLOR)

        # leave image fully transparent (hide labels)
        if percentage < 0.0:
            return
        y: int = 8
        # show health bar only for enemies
        if self.model.attitude == AttitudeEnum.enemy.value:
            self.image.blit(self.image_full, self.rect_full.topleft)

            percentage = min(1.0, percentage)
            percentage = max(0.0, percentage)
            width = int(self.rect_full.width * percentage)
            rect = pygame.Rect(width, 0, self.rect_full.width - width, self.image_full.get_height())
            tmp_img = self.image_empty.subsurface(rect)

            self.image.blit(tmp_img, (self.rect_full.left + width, 1))

            y += 5

        # render name of the character
        game.render_text(
            self.model.name,
            # self.translate_pos((int(self.rect.width // 2), 10)),
            (int(self.rect.width // 2), y),
            self.color,
            font_size=FONT_SIZE_TINY,
            thin_fonts=True,
            # shadow=(20, 27, 27),
            shadow=(84, 135, 137),
            centred=True,
            surface=self.image
        )

#################################################################################################################


class Object(pygame.sprite.Sprite):
    def __init__(
        self,
        group: pygame.sprite.Group | None,
        pos: tuple[int, int],
        image: pygame.Surface  = pygame.Surface((TILE_SIZE, TILE_SIZE)),
        # z: str = "blocks",
    ) -> None:
        if group is not None:
            super().__init__(group)
        else:
            super().__init__()

        self.image = image
        self.rect: pygame.FRect = image.get_frect(topleft = pos)
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, 0)
        # self.z = z
#################################################################################################################


class EmoteSprite(Object):
    def __init__(
        self,
        group: pygame.sprite.Group,
        pos: tuple[int, int],
        emotes: dict[str, list[pygame.Surface]],
        # emote: pygame.Surface  = pygame.Surface((TILE_SIZE, TILE_SIZE)),
        # z: str = "blocks",
    ) -> None:

        self.emotes = emotes
        self.emote: str = ""
        self.temporary_emote: str = ""
        self.temporary_emote_counter: float = 0.0
        self.frame_index: float = 0.0
        self.image: pygame.Surface = self.emotes["clear"][0]
        self.set_emote("clear")
        super().__init__(group, pos, self.image)

        self.rect: pygame.FRect = self.image.get_frect(midbottom = pos)

    def set_emote(self, emote: str) -> None:
        # if self.temporary_emote_counter > 0.0:
        #     print("set_emote", emote)

        if self.emote != emote:
            # if emote == "clear" and self.emote == "red_exclamation_anim":
            #     return

            self.emote = emote
            if not self.temporary_emote:
                self.frame_index = 0.0
                # self.image = self.emotes[self.emote][int(self.frame_index)]
                # self.image = self.emotes[self.emote][0]
                self.animate(0.0, forced=True)

    def clear_temporary_emote(self) -> None:
        self.temporary_emote = ""
        self.temporary_emote_counter = 0.0
        self.frame_index = 0.0
        self.animate(0.0, forced=True)

    def set_temporary_emote(self, emote: str, duration: float) -> None:
        # print("set_temporary_emote", emote)

        # if not self.temporary_emote:
        self.temporary_emote = emote
        self.temporary_emote_counter = duration
        self.frame_index = 0.0
        self.animate(0.0, forced=True)

    def animate(self, dt: float, forced: bool = False) -> None:
        # if self.temporary_emote_counter > 0.0:
        #             print(f"""before e={self.emote}
        # te={self.temporary_emote}
        # tec={self.temporary_emote_counter}
        # dt={dt:5.2f}
        # delta={(self.temporary_emote_counter - dt):5.2f}
        # fi={self.frame_index}""".replace("\n", " "))
        # skip if not animated and not forced
        # if "_anim" not in self.emote and forced == False:
        #     return

        self.frame_index += dt

        #         if self.temporary_emote_counter > 0.0:
        #             print(f"""after  e={self.emote}
        # te={self.temporary_emote}
        # tec={self.temporary_emote_counter}
        # dt={dt:5.2f}
        # delta={(self.temporary_emote_counter - dt):5.2f}
        # fi={self.frame_index}""".replace("\n", " "))

        if self.temporary_emote:
            self.temporary_emote_counter -= dt
            if self.temporary_emote_counter < 0.0:
                self.temporary_emote = ""

        active_emote = self.emote if not self.temporary_emote else self.temporary_emote

        if self.frame_index >= len(self.emotes[active_emote]):
            self.frame_index = 0.0  # if loop else len(self.emotes[self.emote]) - 1.0

        self.image = self.emotes[active_emote][int(self.frame_index)]  # .copy()

#################################################################################################################


class ItemSprite(Object):
    def __init__(
        self,
        group: pygame.sprite.Group | None,
        # gid: int,
        pos: tuple[int, int],
        # z: str = "blocks",
        name: str,
        model: Item,
        image: pygame.Surface = pygame.Surface((TILE_SIZE, TILE_SIZE)),
    ) -> None:

        super().__init__(group, pos, image)
        # decrease the size of rectangle for collisions aka. hitbox
        # self.hitbox: pygame.FRect = self.rect.copy().inflate(0, -self.rect.height / 2)
        # self.gid = gid
        self.name = name
        self.model = model
        if model.type == ItemTypeEnum.weapon:
            self.image_directions: dict[str, pygame.Surface] = {
                "down": image,
                "up": pygame.transform.flip(image, False, True),
            }
            self.image_directions["left"] = pygame.transform.rotate(image, -90)
            self.image_directions["right"] = pygame.transform.rotate(image, 90)

            # self.weapon_mask = pygame.mask.from_surface(self.image)
            self.masks: dict[str, pygame.mask.Mask] = {}
            for direction in self.image_directions:
                self.masks[direction] = pygame.mask.from_surface(self.image_directions[direction])

            self.mask: pygame.mask.Mask = self.masks["up"]

#################################################################################################################


class ChestSprite(Object):
    def __init__(
        self,
        group: pygame.sprite.Group | None,
        pos: tuple[int, int],
        # name: str,
        model: Chest,
        chests_sprites: dict[str, list[pygame.Surface]]
        # image_open: pygame.Surface = pygame.Surface((TILE_SIZE, TILE_SIZE)),
        # image_closed: pygame.Surface = pygame.Surface((TILE_SIZE, TILE_SIZE)),
    ) -> None:

        self.image_closed = chests_sprites["small_chest"][0] if model.is_small else chests_sprites["big_chest"][0]
        self.image_open = chests_sprites["small_chest"][1] if model.is_small else chests_sprites["big_chest"][1]
        image = self.image_closed if model.is_closed else self.image_open
        super().__init__(group, pos, image)
        # self.rect.center = pos
        self.model = model
        self.name = model.name
        # self.is_closed = True
        # self.items: list[Item] = []

#################################################################################################################
    def open(self) -> None:
        self.image = self.image_open
        self.model.is_closed = False

#################################################################################################################
    def close(self) -> None:
        self.image = self.image_closed
        self.model.is_closed = True

#################################################################################################################


class NotificationTypeEnum(StrEnum):
    debug = auto()
    info = auto()
    warning = auto()
    error = auto()
    success = auto()
    failure = auto()

################################################################################################################


@dataclass(slots=True)
class Notification():
    type: NotificationTypeEnum
    message: str
    message_text: str
    width: int
    height: int
    create_time: float
