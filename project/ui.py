from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from rich import print
import pygame
from objects import ItemSprite, InventorySlot, Notification, NotificationTypeEnum
from animation.transitions import AnimationTransition
from maze_generator.maze_utils import timeit
from sftext.style import Style
from sftext.sftext import SFText


if TYPE_CHECKING:
    from characters import Player, NPC
    from game import Game
    from scene import Scene


from nine_patch import NinePatch
from rich_text import RichPanel
from settings import (
    ACTIONS,
    AVATAR_SCALE,
    CHAR_NAME_COLOR,
    DIALOGS_DIR,
    FONT_COLOR,
    FONT_SIZE_HUGE,
    FONT_SIZE_LARGE,
    FONT_SIZE_SMALL,
    FONT_SIZE_TINY,
    FONT_SIZE_MEDIUM,
    FONTS_PATH,
    HEIGHT,
    INVENTORY_ITEM_SCALE,
    INVENTORY_ITEM_WIDTH,
    IS_WEB,
    MAX_HOTBAR_ITEMS,
    PANEL_BG_COLOR,
    SHOW_HELP_INFO,
    TEXT_ROW_SPACING,
    TILE_SIZE,
    TRANSPARENT_COLOR,
    UI_BORDER_COLOR,
    UI_BORDER_COLOR_ACTIVE,
    UI_BORDER_WIDTH,
    UI_COOL_OFF_COLOR,
    WIDTH,
    INPUTS,
    load_image
)

if IS_WEB:
    from config_model.config import ItemTypeEnum
else:
    from config_model.config_pydantic import ItemTypeEnum  # type: ignore[assignment]


NOTIFICATION_TYPE_ICONS: dict[str, str] = {
    NotificationTypeEnum.debug.value:   "human",
    NotificationTypeEnum.info.value:    "dots_anim",
    NotificationTypeEnum.warning.value: "exclamation",
    NotificationTypeEnum.error.value:   "red_exclamation_anim",
    NotificationTypeEnum.success.value: "blessed_anim",
    NotificationTypeEnum.failure.value: "shocked_anim",
}


class UI:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.game: Game = self.scene.game
        self.display_surface = self.game.HUD
        self.font = self.game.fonts[FONT_SIZE_MEDIUM]
        self.tiny_font = self.game.fonts[FONT_SIZE_SMALL]
        self.inventory_slot: InventorySlot = InventorySlot(
            None,
            (WIDTH // 2 - (INVENTORY_ITEM_WIDTH * MAX_HOTBAR_ITEMS // 2),
             HEIGHT - INVENTORY_ITEM_WIDTH - TILE_SIZE),
            INVENTORY_ITEM_SCALE
        )

        self.show_help_info: bool = SHOW_HELP_INFO

        m = "This is a very long, long messages to be displayed in the box."
        text_surf = self.tiny_font.render(m, False, FONT_COLOR)
        border = 6 * 4
        self.modal_panel_bg = NinePatch(file="nine_patch_03c.png", scale=4).get_scaled_to(WIDTH - 200, HEIGHT - 100)
        self.dialog_panel_bg = NinePatch(file="nine_patch_01c.png", scale=4).get_scaled_to(WIDTH - 200, HEIGHT // 3)
        self.name_panel_bg = NinePatch(file="nine_patch_13.png", scale=4).get_scaled_to(26 * TILE_SIZE, 1 * TILE_SIZE)
        self.available_action_bg = NinePatch(file="panel_brown.png", scale=4, border=3).get_scaled_to(200, 36)
        # self.notification_bg = NinePatch(file="panel_brown.png", scale=4, border=3)
        self.notification_bg = NinePatch(file="nine_patch_04c.png", scale=4, border=3)

        weapon_s = 24 + TILE_SIZE * 8
        self.weapon_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(weapon_s, weapon_s)
        self.stats_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(300, 190)

        self.inventory_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(800, 320)
        self.inventory_bg_rect = self.inventory_bg.get_rect()
        top_left = (WIDTH // 2 - (self.inventory_bg_rect.width // 2), HEIGHT - 320)
        self.inventory_bg_rect.topleft = top_left
        # topleft=top_left
        pygame.draw.line(self.inventory_bg, (70, 64, 46),
                         (self.inventory_bg_rect.width // 2, 70),
                         (self.inventory_bg_rect.width // 2, 160),
                         4)
        pygame.draw.line(self.inventory_bg, (70, 64, 46),
                         (40, 180),
                         (self.inventory_bg_rect.width - 40, 180),
                         4)

        self.trader_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(800, 520)
        self.trader_bg_rect = self.trader_bg.get_rect()
        top_left = (WIDTH // 2 - (self.trader_bg_rect.width // 2), 50)
        self.trader_bg_rect.topleft = top_left
        # topleft=top_left
        pygame.draw.line(self.trader_bg, (70, 64, 46),
                         (self.trader_bg_rect.width // 2, self.trader_bg_rect.height - 40 - 100),
                         (self.trader_bg_rect.width // 2, self.trader_bg_rect.height - 40),
                         4)
        pygame.draw.line(self.trader_bg, (70, 64, 46),
                         (40, 330),
                         (self.trader_bg_rect.width - 40, 330),
                         4)

        self.trader_small_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(800, 340)
        self.trader_small_bg_rect = self.trader_small_bg.get_rect()
        top_left = (WIDTH // 2 - (self.trader_small_bg_rect.width // 2), 50)
        self.trader_small_bg_rect.topleft = top_left

        show_actions = [action for action in ACTIONS.values() if action["show"]]
        help_w = int((len(show_actions) + 2) * FONT_SIZE_MEDIUM * 2.1)
        self.help_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(300, help_w)

        # self.panel_border_size = self.panel_border.get_size()
        # self.factor = 6 * 4
        # self.panel_background = pygame.Surface(
        #     (self.panel_border_size[0] - self.factor * 2,
        #      self.panel_border_size[1] - self.factor * 2)).convert_alpha()
        # self.panel_background.fill((0, 0, 0, 0))

        self.show_inventory_panel_flag: bool = False
        self.show_modal_panel_flag: bool = False
        self.show_dialog_panel_flag: bool = False
        self.show_trade_panel_flag: bool = False
        self.is_buying: bool = True
        self.show_nine_patch_test: bool = False

        if self.show_nine_patch_test:
            self.np_01 = NinePatch(file="nine_patch_01.png", scale=4).get_scaled_to_image(text_surf)
            self.np_02 = NinePatch(file="nine_patch_02.png", scale=4).get_scaled_to_image(text_surf)
            self.np_03 = NinePatch(file="nine_patch_03.png", scale=4).get_scaled_to_image(text_surf)
            self.np_04 = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to_image(text_surf)
            self.np_05 = NinePatch(file="nine_patch_05.png", scale=4).get_scaled_to_image(text_surf)
            self.np_06 = NinePatch(file="nine_patch_06.png", scale=4).get_scaled_to_image(text_surf)
            self.np_07 = NinePatch(file="nine_patch_07.png", scale=4).get_scaled_to_image(text_surf)
            self.np_08 = NinePatch(file="nine_patch_08.png", scale=4).get_scaled_to_image(text_surf)
            self.np_09 = NinePatch(file="nine_patch_09.png", scale=4).get_scaled_to_image(text_surf)
            self.np_10 = NinePatch(file="nine_patch_10.png", scale=4).get_scaled_to_image(text_surf)
            self.np_11 = NinePatch(file="nine_patch_11.png", scale=4).get_scaled_to_image(text_surf)
            self.np_12 = NinePatch(file="nine_patch_12.png", scale=4).get_scaled_to_image(text_surf)

        # self.modal_panel: RichPanel | None = None
        modal_panel_file = DIALOGS_DIR / "welcome_message.md"
        modal_panel_text = modal_panel_file.read_text()
        modal_panel_tooltip = """[h3][act]This is a tooltip[/act][/h3]\n\n[bold]%s[/bold]"""
        self.modal_panel_offset = (100, 50)
        self.modal_panel = RichPanel(
            modal_panel_text,
            modal_panel_tooltip,
            self.modal_panel_bg,
            self.modal_panel_offset,
            self.scene.icons,
            border_size=(border, border),
            tooltip_offset=self.game.cursor_img.get_size(),
        )

        # self.dialog_panel: RichPanel | None = None
        # if self.show_dialog_panel:
        # dialog_panel_file = Path("rich_text_dialog.md")
        # dialog_panel_text = dialog_panel_file.read_text()
        dialog_panel_tooltip = """[h3][act]Hint[/act][/h3]\n\n[bold]%s[/bold]"""
        self.dialog_panel_offset = (100, HEIGHT - self.dialog_panel_bg.get_rect().height - 10)
        self.dialog_panel = RichPanel(
            "<blank>",
            dialog_panel_tooltip,
            self.dialog_panel_bg,
            self.dialog_panel_offset,
            self.scene.icons,
            border_size=(border, border),
            tooltip_offset=self.game.cursor_img.get_size(),
        )

        self.icons_dict: dict[str, list[pygame.Surface]] = self.scene.icons

    #############################################################################################################
    @lru_cache(maxsize = 128)
    def create_rich_text(self, text: str, size: tuple[int, int]) -> SFText:
        default_font_color: tuple[int, int, int] = (0, 197, 199)
        shadow_color: tuple[int, int, int] = (130, 32, 32)
        shadow_offset: tuple[int, int] = (4, 4)
        border_size: tuple[int, int] = (0, 0)

        # processed_text = RichPanel._parse_text(text)
        # print(processed_text)

        pixel_art_style = Style().get_default("")
        pixel_art_style["size"] = 14
        pixel_art_style["font"] = "font_pixel.ttf"
        # s["font"] = "Homespun.ttf"
        pixel_art_style["separate_italic"] = None
        pixel_art_style["separate_bold"] = None
        pixel_art_style["separate_bolditalic"] = None
        # pixel_art_style["indent"] = 10 # indent is actually not implemented in sftext
        # default text color
        pixel_art_style["color"] = default_font_color
        # default text shadow color
        pixel_art_style["shadow_color"] = shadow_color
        # direction of the shadow offset, needs to be aligned with the font size
        pixel_art_style["shadow_offset"] = shadow_offset

        # background_canvas_size = background_canvas.get_size()

        text_canvas = pygame.Surface(
            (size[0] - border_size[0] * 2,
             size[1] - border_size[1] * 2)).convert_alpha()
        text_canvas.fill((0, 0, 0, 0))

        formatted_text = SFText(
            text=text,
            images=self.icons_dict,
            canvas=text_canvas,
            # font_path=os.path.join(".", "sftext", "resources"),
            font_path=str(FONTS_PATH),
            style=pixel_art_style,
            debug=False
        )
        # in order to detect mouse hover over a link,
        # sftext object needs to know it's offset relative to the main screen
        # formatted_text.canvas_offset = (
        #     screen_offset[0] + border_size[0],
        #     screen_offset[1] + border_size[0])
        formatted_text.show_scrollbar = False
        formatted_text.MARGIN_HORIZONTAL = 0
        formatted_text.MARGIN_VERTICAL = 0
        formatted_text.on_update(0.0)

        return formatted_text
    #############################################################################################################

    def reset(self) -> None:
        self.show_modal_panel_flag = False
        self.show_dialog_panel_flag = False
        self.show_trade_panel_flag = False

        self.modal_panel.formatted_text.scroll_top()

        self.dialog_panel.formatted_text.scroll_top()

    #############################################################################################################

    def display_text(
        self,
        text: str,
        pos: tuple[int, int],
        font: pygame.font.Font | None = None,
        align: str = "left",
        color: pygame._common.ColorValue | None = None,
        shadow: bool = True,
        border: pygame._common.ColorValue = PANEL_BG_COLOR
    ) -> None:
        if not font:
            font = self.font

        if not color:
            color = FONT_COLOR

        text_surf = font.render(str(text), False, color)

        if align == "left":
            text_rect = text_surf.get_rect(topleft = pos)
        elif align == "centred":
            text_rect = text_surf.get_rect(center = pos)
        else:
            text_rect = text_surf.get_rect(topright = pos)

        if border:
            border_surf = font.render(str(text), False, border)
            # self.display_surface.blit(border_surf, text_rect.move(2, 2))

            offset = 2 if shadow else 3
            self.display_surface.blit(border_surf, (text_rect.x + offset, text_rect.y + offset))

            if not shadow:
                self.display_surface.blit(border_surf, (text_rect.x - offset, text_rect.y))
                self.display_surface.blit(border_surf, (text_rect.x + offset, text_rect.y))
                self.display_surface.blit(border_surf, (text_rect.x,          text_rect.y - offset))
                self.display_surface.blit(border_surf, (text_rect.x,          text_rect.y + offset))

                self.display_surface.blit(border_surf, (text_rect.x - offset, text_rect.y - offset))
                self.display_surface.blit(border_surf, (text_rect.x + offset, text_rect.y - offset))
                self.display_surface.blit(border_surf, (text_rect.x - offset, text_rect.y + offset))

        self.display_surface.blit(text_surf, text_rect)

    #############################################################################################################
    def box(self, left: int, top: int, width: int, height: int) -> None:

        bg_rect = pygame.Rect(left, top, width, height)

        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA).convert_alpha()
        bg_surface.fill(PANEL_BG_COLOR)
        surface = self.display_surface
        surface.blit(bg_surface, bg_rect.topleft)

        pygame.draw.rect(surface, UI_BORDER_COLOR, bg_rect, UI_BORDER_WIDTH)

    # #############################################################################################################
    # def display_image(self, left: int, top: int, width: int, height: int) -> None:

    #     bg_rect = pygame.Rect(left, top, width, height)

    #     bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA).convert_alpha()
    #     bg_surface.fill(PANEL_BG_COLOR)
    #     surface = self.display_surface
    #     surface.blit(bg_surface, bg_rect.topleft)

    #     pygame.draw.rect(surface, UI_BORDER_COLOR, bg_rect, UI_BORDER_WIDTH)

    #############################################################################################################
    def show_hotbar(self, npc: NPC, top_left: tuple[int, int], show_shortcuts: bool) -> None:

        # npc: Player = self.scene.player
        # top_left = self.inventory_slot.rect.topleft
        for i in range(MAX_HOTBAR_ITEMS):

            item_model = npc.items[i].model if i < len(npc.items) else None

            if npc.selected_weapon and npc.selected_weapon.model == item_model:
                image = self.inventory_slot.image_selected
            else:
                image = self.inventory_slot.image
            # background of slot
            self.display_surface.blit(image, (top_left[0] + i * INVENTORY_ITEM_WIDTH, top_left[1]))
            if i < len(npc.items):
                # selector
                if i == npc.selected_item_idx and show_shortcuts:
                    self.display_surface.blit(self.inventory_slot.image_selector,
                                              (top_left[0] + i * INVENTORY_ITEM_WIDTH, top_left[1]))

                item: ItemSprite = npc.items[i]
                if item.model.type == ItemTypeEnum.weapon:
                    image = item.image_directions["up"]
                else:
                    image = item.image or pygame.Surface((TILE_SIZE, TILE_SIZE))
                image = pygame.transform.scale_by(image, INVENTORY_ITEM_SCALE)

                x_offset = 10  # size[0] // 2
                y_offset = 12
                # item image
                self.display_surface.blit(
                    image, (x_offset + (top_left[0] + i * INVENTORY_ITEM_WIDTH), y_offset + top_left[1]))

                self.display_text(str(item.model.count),
                                  (12 + top_left[0] + i * INVENTORY_ITEM_WIDTH, 16 + top_left[1]),
                                  font=self.tiny_font,
                                  )

            # key shortcut
            if show_shortcuts:
                if i <= len(npc.items) - 1:
                    self.display_surface.blit(
                        self.icons_dict[f"key_{i + 1}"][0],
                        (top_left[0] + 2 + i * INVENTORY_ITEM_WIDTH + INVENTORY_ITEM_WIDTH // 4,
                         top_left[1] - 22))

        # left/right hotbar selection key shortcut
        if show_shortcuts:
            h = 24
            self.display_surface.blit(self.icons_dict["key_<"][0], ((top_left[0] - 24), top_left[1] + h))
            self.display_surface.blit(self.icons_dict["key_>"][0], (
                (top_left[0] + MAX_HOTBAR_ITEMS * INVENTORY_ITEM_WIDTH - 16), top_left[1] + h))

    #############################################################################################################

    def selection_box(self, left: int, top: int, has_switched: bool, cooldown: int = 100) -> pygame.Rect:
        item_box_size = TILE_SIZE * 8

        c = 1 - max(0, cooldown / 100)
        h = int(item_box_size * c)
        bg_cool_off_rect = pygame.Rect(left, top + item_box_size - h, item_box_size, h)
        bg_rect = pygame.Rect(left, top, item_box_size, item_box_size)

        surface = self.display_surface

        # nine patch panel
        surface.blit(self.weapon_bg, bg_rect.move(-12, -12).topleft)
        # semi-transparent background panel
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA).convert_alpha()
        # bg_surface.fill(PANEL_BG_COLOR)
        # pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_cool_rect)
        surface.blit(bg_surface, bg_rect.topleft)
        # red rectangle to show cooldown
        pygame.draw.rect(surface, UI_COOL_OFF_COLOR, bg_cool_off_rect)

        # golden border if weapon has been switched
        if has_switched:
            pygame.draw.rect(surface, UI_BORDER_COLOR_ACTIVE, bg_rect, UI_BORDER_WIDTH)
        # else:
        #     pygame.draw.rect(surface, UI_BORDER_COLOR, bg_rect, UI_BORDER_WIDTH)
        return bg_rect

    #############################################################################################################
    def show_weapon_panel(self, weapon: ItemSprite | None, has_switched: bool, elapsed_time: float) -> None:
        player = self.scene.player
        if player.is_attacking:
            now = elapsed_time - player.attack_time
            weapon_cooldown = player.selected_weapon.model.cooldown_time if player.selected_weapon else 0.0
            limit = (player.attack_cooldown / 1000.0) + weapon_cooldown
            cooldown = int(now / limit * 100)
            cooldown = min(100, cooldown)
        else:
            cooldown = 100

        bg_rect = self.selection_box(TILE_SIZE, HEIGHT - (TILE_SIZE * 9), has_switched, cooldown)
        if weapon:
            weapon_surf = pygame.transform.scale(weapon.image_directions["up"], (TILE_SIZE * 7, TILE_SIZE * 7))
            weapon_rect = weapon_surf.get_rect(center = bg_rect.center)
            surface = self.display_surface
            surface.blit(weapon_surf, weapon_rect)

            # if weapon is ready show key shortcut
            if cooldown == 100:
                pos = bg_rect.move(4, 18).topright
                surface.blit(self.icons_dict["key_Space"][0], pos)

    # def show_magic_panel(self, magic_index, has_switched) -> None:
    #     bg_rect = self.selection_box(80, 635, has_switched)
    #     magic_surf = self.magic_graphics[magic_index]
    #     magic_rect = magic_surf.get_rect(center = bg_rect.center)

    #     self.display_surface.blit(magic_surf, magic_rect)

    #############################################################################################################

    def show_help(self) -> None:

        if self.show_help_info:
            # list actions to be displayed by the property "show"
            show_actions = [action for action in ACTIONS.values() if action["show"]]
            row_spacing = 2.2
            # render semitransparent panel in background
            rect = pygame.Rect(
                WIDTH - 300 - 32,
                TILE_SIZE // 2,
                400 - 2,
                (len(show_actions) + 1) * FONT_SIZE_MEDIUM * row_spacing
            )

            # self.game.render_panel(rect, PANEL_BG_COLOR)
            self.display_surface.blit(self.help_bg, rect.topleft)

            for i, action in enumerate(show_actions, start=1):
                self.game.render_text(
                    # f"{', '.join(action['show']):>11} - {action['msg']}",
                    f"{action['msg']}",
                    (WIDTH - 300 + 38, 2 + int(i * FONT_SIZE_MEDIUM * row_spacing)),
                    shadow = True
                )
                self.display_surface.blit(
                    self.icons_dict[action['show'][0]][0], (WIDTH - 300, -6 + int(i * FONT_SIZE_MEDIUM * row_spacing)))
        # else:
        #     self.display_surface.blit(self.icons_dict["key_H"], (WIDTH // 2 -
        #                               36, int(FONT_SIZE_MEDIUM * TEXT_ROW_SPACING) - 10))
        #     self.display_text("show help", (WIDTH // 2, int(FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)), border=True)

            # self.game.render_text(
            #     "press [h] for help",
            #     (WIDTH // 2, int(FONT_SIZE_MEDIUM * TEXT_ROW_SPACING)),
            #     shadow = True,
            #     centred = True
            # )

    #############################################################################################################
    def show_action(self, action: str, row: int, label: str = "") -> None:
        row_height: int = 48
        row_spacing = row * row_height
        label = label or ACTIONS[action]["msg"]
        icon: pygame.Surface = self.icons_dict[ACTIONS[action]["show"][0]][0]
        label_w, _ = self.font.size(label)
        self.display_surface.blit(self.available_action_bg,
                                  (WIDTH - TILE_SIZE - 200,
                                   HEIGHT - (2 * TILE_SIZE) - 16 - row_spacing))
        self.display_surface.blit(icon,
                                  (WIDTH - (2 * TILE_SIZE) - 16,
                                   HEIGHT - (2 * TILE_SIZE) - 14 - row_spacing))
        self.display_text(label, (WIDTH - TILE_SIZE - label_w - 40,
                                  HEIGHT - (2 * TILE_SIZE) - 7 - row_spacing))

    #############################################################################################################
    def show_notification(self, notification: Notification, row: int) -> None:
        row_height: int = 50
        row_spacing = row * row_height
        time_elapsed = self.scene.game.time_elapsed - notification.create_time

        NOTIFICATION_Y_TOP: int = 230
        NOTIFICATION_Y_BOTTOM: int = HEIGHT - TILE_SIZE
        notification_y_stop = NOTIFICATION_Y_TOP + row_spacing

        slide_in_duration = 1.0
        factor = time_elapsed / slide_in_duration if time_elapsed < slide_in_duration else 1.0
        factor = AnimationTransition.in_out_expo(factor)
        y = int(NOTIFICATION_Y_BOTTOM + (notification_y_stop - NOTIFICATION_Y_BOTTOM) * factor)

        # label = f":blink: {notification.message}"
        # parsed_label = RichPanel._parse_text(label)
        # label_text, _ = Style.split(parsed_label)
        # label_text = label_text.replace("{style}", "")
        # # print(label_text)
        # label_w, label_h = self.font.size(label_text)
        # icon: pygame.Surface = self.icons_dict[ACTIONS[action]["show"][0]]
        anim = self.scene.icons[NOTIFICATION_TYPE_ICONS[notification.type]]
        animation_speed = 5
        frame_index = (animation_speed * time_elapsed)

        # if int(frame_index) >= len(anim):
        frame_index = frame_index % len(anim)
        # icon = anim[int(frame_index)]
        # scale = 2
        rich_text = self.create_rich_text(notification.message, (notification.width + 90, notification.height + 60))
        rich_text.on_update(self.game.time_elapsed)

        self.display_surface.blit(
            self.notification_bg.get_scaled_fit(notification.width + 36, notification.height + 4),
            (TILE_SIZE, y))
        # self.display_surface.blit(pygame.transform.scale_by(icon, scale),
        #                           (TILE_SIZE + 10, y + 10))
        # self.display_text(label,
        #                   (TILE_SIZE + 46, y + 16), border=True)
        self.display_surface.blit(rich_text.canvas,
                                  (TILE_SIZE - 28, y - 26))

    #############################################################################################################
    def show_available_actions(self) -> None:

        if not self.show_help_info:
            self.show_action("help", 0)

        player: Player = self.scene.player
        if not player.is_flying and not player.is_attacking and not player.is_stunned:

            items: list[ItemSprite] = self.scene.item_sprites.sprites()
            collided_index = player.feet.collidelist(items)   # type: ignore[type-var]
            if collided_index > -1:
                self.show_action("pick_up", 1)

        if player.selected_item_idx >= 0:
            self.show_action("drop", 2)

            item: ItemSprite = player.items[player.selected_item_idx]
            label: str = ""
            if item.model.type == ItemTypeEnum.consumable:
                label = "consume"
            elif item.model.type == ItemTypeEnum.weapon:
                if player.selected_weapon:
                    if player.selected_weapon.name == item.name:
                        label = "disarm"
                    else:
                        label = "equip"
                else:
                    label = "equip"

            self.show_action("use_item", 3, label=label)

        if player.chest_in_range:
            self.show_action("open", 4, label="open chest")
        elif player.npc_met:
            if player.npc_met.has_dialog:
                self.show_action("talk", 4)
            elif player.npc_met.model.is_merchant:
                self.show_action("trade", 4)
    #############################################################################################################

    def activate_dialog_panel(self, dialog_text: str) -> None:
        self.show_dialog_panel_flag = True
        self.dialog_panel.set_text(dialog_text)
        self.dialog_panel.formatted_text.scroll_top()

    #############################################################################################################

    def activate_trade_panel(self) -> None:
        self.show_trade_panel_flag = True

    #############################################################################################################

    def deactivate_trade_panel(self) -> None:
        self.show_trade_panel_flag = False

    #############################################################################################################
    # @timeit
    def update(self, time_elapsed: float, events: list[pygame.event.EventType]) -> None:
        global INPUTS
        # if INPUTS["select"] or INPUTS["pick_up"]:
        if INPUTS["inventory"]:
            self.show_inventory_panel_flag = not self.show_inventory_panel_flag
            INPUTS["inventory"] = False

        if INPUTS["talk"]:
            if self.show_modal_panel_flag:
                if self.modal_panel.formatted_text.is_scroll_bottom():
                    self.show_modal_panel_flag = False
                else:
                    self.modal_panel.formatted_text.scroll_page_down()
                INPUTS["talk"] = False
                # INPUTS["pick_up"] = False

            if self.show_dialog_panel_flag:
                if self.dialog_panel.formatted_text.is_scroll_bottom():
                    self.show_dialog_panel_flag = False
                    self.scene.player.is_talking = False
                    if self.scene.player.npc_met:
                        self.scene.player.npc_met.is_talking = False
                        # self.scene.player.npc_met.has_dialog = False
                else:
                    self.dialog_panel.formatted_text.scroll_page_down()
                    # self.dialog_panel.formatted_text.scroll_bottom()
                INPUTS["talk"] = False
                # INPUTS["pick_up"] = False

        if INPUTS["end_trade"]:
            if self.show_trade_panel_flag:
                self.show_trade_panel_flag = False
                self.scene.player.is_talking = False
                if self.scene.player.npc_met:
                    self.scene.player.npc_met.is_talking = False
                INPUTS["quit"] = False
            INPUTS["end_trade"] = False

        if INPUTS["toggle"]:
            if self.show_trade_panel_flag:
                self.is_buying = not self.is_buying
            INPUTS["toggle"] = False

        if INPUTS["buy"]:
            if self.show_trade_panel_flag and self.scene.player.npc_met and self.is_buying:
                if self.scene.player.can_buy():
                    item = self.scene.player.npc_met.drop_item(show=False)
                    if item:
                        self.scene.player.model.money -= item.model.value
                        self.scene.player.npc_met.model.money += item.model.value
                        self.scene.player.pick_up(item)
                        self.scene.add_notification(
                            f"Bought '[item]{item.model.name}[/item]'",
                            NotificationTypeEnum.info)
            INPUTS["buy"] = False

        if INPUTS["sell"]:
            if self.show_trade_panel_flag and self.scene.player.npc_met and not self.is_buying:
                if self.scene.player.can_sell():
                    item = self.scene.player.drop_item(show=False)
                    if item:
                        self.scene.player.model.money += item.model.value
                        self.scene.player.npc_met.model.money -= item.model.value
                        self.scene.player.npc_met.pick_up(item)
                        self.scene.add_notification(
                            f"Sold '[item]{item.model.name}[/item]'",
                            NotificationTypeEnum.info)
            INPUTS["sell"] = False

        for event in events:
            if self.show_modal_panel_flag:
                if event.type == pygame.KEYDOWN:
                    self.modal_panel.on_key_press(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.modal_panel.on_mouse_button(event)

            if self.show_dialog_panel_flag:
                if event.type == pygame.KEYDOWN:
                    self.dialog_panel.on_key_press(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.dialog_panel.on_mouse_button(event)

        if self.show_modal_panel_flag:
            self.modal_panel.on_mouse_move()
            self.modal_panel.on_update(time_elapsed)

        if self.show_dialog_panel_flag:
            self.dialog_panel.on_mouse_move()
            self.dialog_panel.on_update(time_elapsed)

    #############################################################################################################
    # @timeit
    def display_ui(self, elapsed_time: float) -> None:
        player: Player = self.scene.player

        # upper right corner
        # FPS counter
        # self.box(WIDTH - 200, TILE_SIZE, 180, 10 + (25 * 1))
        # self.display_text(f"FPS: {self.game.fps:5.1f}", (WIDTH - 200 + 10, TILE_SIZE + 10))

        if self.show_inventory_panel_flag:
            self.show_inventory_panel(player)

        # lower left corner
        # weapon panel
        if not self.show_dialog_panel_flag and not self.show_trade_panel_flag:
            self.show_weapon_panel(player.selected_weapon, not player.can_switch_weapon, elapsed_time)
            # self.show_magic_panel(player.magic_index, not player.can_switch_magic)

            # middle lower and right upper
            # hot bar
            self.show_hotbar(player, self.inventory_slot.rect.topleft, show_shortcuts=True)

            # middle upper
            # help panel
            if self.show_help_info:
                self.show_help()
            else:
                # lower right corner
                # available actions key shortcuts
                self.show_available_actions()

        if self.show_modal_panel_flag:
            self.show_modal_panel()

        if self.show_dialog_panel_flag:
            self.show_dialog_panel()

        if self.show_trade_panel_flag:
            self.show_trade_panel()

        # left middle
        # show notifications
        for row, notification in enumerate(self.scene.notifications):
            self.show_notification(notification, row)

        # upper left corner
        # UI semitransparent background panel
        # self.box(TILE_SIZE, TILE_SIZE, 450, 125)
        self.show_stats_panel(player)

        if self.show_nine_patch_test:
            # self.display_surface.blit(self.np_01, (200, 100))
            # self.display_surface.blit(self.np_02, (200, 200))
            # self.display_surface.blit(self.np_03, (200, 300))
            # self.display_surface.blit(self.np_04, (200, 400))
            self.display_surface.blit(self.np_05, (200, 500))
            self.display_surface.blit(self.np_06, (200, 600))
            self.display_surface.blit(self.np_07, (200, 700))
            self.display_surface.blit(self.np_08, (200, 800))
            self.display_surface.blit(self.np_09, (200, 900))

            self.display_surface.blit(self.np_10, (200, 100))
            self.display_surface.blit(self.np_11, (200, 200))
            self.display_surface.blit(self.np_12, (200, 300))

    #############################################################################################################
    def show_icon_value(self, top_left: tuple[int, int], row: int, property: dict[str, str]) -> None:
        left_margin = 30
        top_margin = 40
        row_height = 35
        icon_scale = 2
        icon_offset = - TILE_SIZE // 2

        if property["icon_name"]:
            icon = pygame.transform.scale_by(self.scene.items_sheet[property["icon_name"]][0], icon_scale)
            self.display_surface.blit(icon, (top_left[0] + left_margin,
                                             top_left[1] + top_margin +  icon_offset + row_height * row))

        if property["value"]:
            self.display_text(
                property["value"],
                color=(0, 197, 199),
                pos=(top_left[0] + 3 * TILE_SIZE + left_margin, top_left[1] + top_margin + row_height * row))

    #############################################################################################################
    def show_stats_panel(self, player: Player) -> None:
        top_left = (TILE_SIZE, TILE_SIZE)
        self.display_surface.blit(self.stats_bg, top_left)

        left_margin = 30
        top_margin = 40

        properties = [
            {
                "icon_name": "big_heart",
                "value": "",
            },
            {
                "icon_name": "pan_balance",
                "value": f"{player.total_items_weight:4.2f}/{player.model.max_carry_weight:4.2f}",
            },
            {
                "icon_name": "hourglass",
                "value": f"{self.scene.hour:d}:{self.scene.minute:02d}",
            },
            {
                "icon_name": "golden_coin",
                "value": f"{player.model.money}",
            },
        ]

        for row, property in enumerate(properties):
            self.show_icon_value(top_left, row, property)

        hb = player.health_bar_ui
        hb.set_bar(player.model.health / player.model.max_health,
                   (4 * TILE_SIZE + left_margin, TILE_SIZE + top_margin - 8))
        self.display_surface.blit(hb.image, hb.rect)

    #############################################################################################################
    def show_merchant_stats_panel(self, npc: NPC, top_left: tuple[int, int]) -> None:
        # top_left = (TILE_SIZE, TILE_SIZE)

        properties = [
            {
                "icon_name": "pan_balance",
                "value": f"{npc.total_items_weight:4.2f}/{npc.model.max_carry_weight:4.2f}",
            },
            {
                "icon_name": "golden_coin",
                "value": f"{npc.model.money}",
            },
        ]

        for row, property in enumerate(properties):
            self.show_icon_value(top_left, row, property)

    #############################################################################################################

    def show_icon_label_value(self, top_left: tuple[int, int], row: int, property: dict[str, str]) -> None:
        left_margin = 30
        top_margin = 40
        row_height = 35
        icon_scale = 2
        icon_offset = - TILE_SIZE // 2

        if property["icon_name"]:
            if property["icon_name"] in self.scene.items_sheet:
                item_sprite = self.scene.items_sheet[property["icon_name"]][0]
            else:
                item_sprite = self.scene.icons[property["icon_name"]][0]
            icon = pygame.transform.scale_by(item_sprite, icon_scale)
            self.display_surface.blit(icon, (top_left[0] + left_margin,
                                             top_left[1] + top_margin +  icon_offset + row_height * row))
        if property["label"]:
            self.display_text(
                property["label"],
                color=(255, 255, 255),
                pos=(top_left[0] + 3 * TILE_SIZE + left_margin, top_left[1] + top_margin + row_height * row))

        if property["value"]:
            self.display_text(
                property["value"],
                color=(0, 197, 199),
                pos=(top_left[0] + 20 * TILE_SIZE + left_margin, top_left[1] + top_margin + row_height * row),
                align="right")

    #############################################################################################################
    def show_inventory_panel(self, npc: NPC) -> None:
        # top_left = (-400 + WIDTH // 2, HEIGHT - 350)
        if self.show_inventory_panel_flag:
            background = self.inventory_bg
            top_left = self.inventory_bg_rect.topleft
            properties_top_left = top_left
        else:
            if self.is_buying:
                background = self.trader_bg
                top_left = self.trader_bg_rect.topleft
                properties_top_left = (top_left[0], self.trader_bg_rect.height - 150)
            else:
                background = self.inventory_bg
                top_left = self.inventory_bg_rect.topleft
                properties_top_left = top_left

                self.display_surface.blit(self.trader_small_bg, self.trader_small_bg_rect.topleft)

        self.display_surface.blit(background, top_left)

        if npc.selected_item_idx >= 0:
            item_model = npc.items[npc.selected_item_idx].model
        else:
            return

        left_properties = [
            {
                "icon_name": "",
                "label": "",
                "value": f"{item_model.name}",
            },
            {
                "icon_name": "pan_balance",
                "label": "Weight",
                "value": f"{item_model.weight:4.2f}",
            },
            {
                "icon_name": "golden_coin",
                "label": "Value",
                "value": f"{item_model.value:4d}",
            },
            {
                "icon_name": "abacus2",
                "label": "Amount",
                "value": f"{item_model.count:4d}",
            },
        ]

        for row, property in enumerate(left_properties):
            self.show_icon_label_value(properties_top_left, row, property)

        right_properties: list[dict[str, str]] = [
            {
                "icon_name": "",
                "label": "",
                "value": "",
            },
            {
                "icon_name": "red_question",
                "label": "Type",
                "value": item_model.type.value.capitalize()
            }
        ]
        if item_model.type == ItemTypeEnum.weapon:
            right_properties.append(
                {
                    "icon_name": "big_heart",
                    "label": "Damage",
                    "value": f"{-item_model.damage:4d}",
                })
            right_properties.append(
                {
                    "icon_name": "hourglass",
                    "label": "Cooldown",
                    "value": f"{item_model.cooldown_time:4.2f}",
                },
            )

        if item_model.type == ItemTypeEnum.consumable:
            right_properties.append(
                {
                    "icon_name": "big_heart",
                    "label": "Health",
                    "value": f"{item_model.health_impact:+4d}",
                },
            )
        top_middle = (WIDTH // 2, properties_top_left[1])
        for row, property in enumerate(right_properties):
            self.show_icon_label_value(top_middle, row, property)

        if self.show_inventory_panel_flag:
            self.display_surface.blit(self.icons_dict["key_I"][0],
                                      (properties_top_left[0] + 800 - 8, properties_top_left[1] + 40))
        # self.display_surface.blit(self.icons_dict["key_<"][0],
        #                           (properties_top_left[0] - 24, properties_top_left[1] + 100))
        # self.display_surface.blit(self.icons_dict["key_>"][0],
        #                           (properties_top_left[0] + 800 - 8, properties_top_left[1] + 100))

    #############################################################################################################
    def show_trade_panel(self) -> None:
        player = self.scene.player
        if not player.npc_met or not player.npc_met.model.is_merchant:
            return

        merchant = player.npc_met
        npc = merchant if self.is_buying else player
        self.show_inventory_panel(npc)

        avatar = pygame.transform.scale_by(merchant.avatar, 0.5)
        avatar_rect = avatar.get_rect()
        self.display_surface.blit(
            avatar,
            (WIDTH // 2 - (avatar_rect.width // 2), self.trader_bg_rect.top + 10)
        )

        self.display_text(
            merchant.model.name,
            (WIDTH // 2, self.trader_bg_rect.top + 10 + avatar_rect.height - 16),
            font=self.game.fonts[FONT_SIZE_LARGE],
            color=CHAR_NAME_COLOR,
            border=(84, 135, 137),
            shadow=False,
            align="centred"
        )

        self.show_merchant_stats_panel(merchant, (WIDTH // 2 + (avatar_rect.width // 2), self.trader_bg_rect.top + 10))

        # bottom_left = self.inventory_slot.rect.bottomleft
        top_left = self.trader_bg_rect.topleft
        self.show_hotbar(merchant,
                         (self.inventory_slot.rect.left,
                          top_left[1] + 10 + avatar_rect.height + 24),
                         show_shortcuts=self.is_buying)
        top_left = self.inventory_slot.rect.topleft
        self.show_hotbar(player,
                         top_left,
                         show_shortcuts=not self.is_buying)

        start_idx = 3
        # self.show_action("toggle", start_idx)
        self.show_action("end_trade", start_idx + 0)
        if self.is_buying:
            self.show_action("toggle", start_idx + 1, label="show mine")
            self.show_action("buy", start_idx + 2)
        else:
            self.show_action("toggle", start_idx + 1, label="show shop")
            self.show_action("sell", start_idx + 2)

    #############################################################################################################
    def show_dialog_panel(self) -> None:
        dialog_panel_size = self.dialog_panel_bg.get_size()
        player = self.scene.player
        # draw avatar of NPC
        if player.npc_met:
            self.display_surface.blit(
                player.npc_met.avatar,
                (self.dialog_panel_offset[0],
                 self.dialog_panel_offset[1]  + 4 - TILE_SIZE * AVATAR_SCALE))
            # draw player avatar
            self.display_surface.blit(
                player.avatar,
                (self.dialog_panel_offset[0] + dialog_panel_size[0] - TILE_SIZE * AVATAR_SCALE,
                 self.dialog_panel_offset[1] + 4 - TILE_SIZE * AVATAR_SCALE))
        # draw dialog panel
        self.display_surface.blit(self.dialog_panel.get_panel(), self.dialog_panel_offset)
        self.display_surface.blit(self.name_panel_bg,
                                  (self.dialog_panel_offset[0] + 3 * TILE_SIZE,
                                   self.dialog_panel_offset[1] - 3 * TILE_SIZE))
        if player.npc_met:
            name = player.npc_met.model.name
        else:
            name = "????"
        self.display_text(name,
                          (self.dialog_panel_offset[0] + 4 * TILE_SIZE,
                           self.dialog_panel_offset[1] - int(1.5 * TILE_SIZE)),
                          font=self.game.fonts[FONT_SIZE_LARGE],
                          color=CHAR_NAME_COLOR
                          )
        # draw key shortcuts
        pos = (self.dialog_panel_offset[0] + dialog_panel_size[0] - 15,
               self.dialog_panel_offset[1] + 40)
        self.display_surface.blit(self.icons_dict["key_Space"][0], pos)

        # pos = (self.dialog_panel_offset[0] + dialog_panel_size[0] // 2,
        #        self.dialog_panel_offset[1] + dialog_panel_size[1] - 15)
        # self.display_surface.blit(self.icons_dict["key_Space"], pos)

        # draw dialog tooltip
        if self.dialog_panel.is_tooltip_available:
            tooltip_canvas, mouse_pos = self.dialog_panel.get_tooltip()
            self.display_surface.blit(tooltip_canvas, mouse_pos)

    #############################################################################################################
    def show_modal_panel(self) -> None:
        self.display_surface.blit(self.modal_panel.get_panel(), self.modal_panel_offset)
        if self.modal_panel.is_tooltip_available:
            tooltip_canvas, mouse_pos = self.modal_panel.get_tooltip()
            self.display_surface.blit(tooltip_canvas, mouse_pos)
