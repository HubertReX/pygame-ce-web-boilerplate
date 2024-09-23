from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from rich import print
import pygame
from objects import ItemSprite, InventorySlot, Notification, NotificationTypeEnum
from animation.transitions import AnimationTransition
from sftext.style import Style
from sftext.sftext import SFText


if TYPE_CHECKING:
    from characters import Player
    from game import Game
    from scene import Scene


from nine_patch import NinePatch
from rich_text import RichPanel
from settings import (
    ACTIONS,
    AVATAR_SCALE,
    CHAR_NAME_COLOR,
    DIALOGS_DIR,
    EMOJIS_DICT,
    EMOJIS_PATH,
    FONT_COLOR,
    FONT_SIZE_HUGE,
    FONT_SIZE_LARGE,
    FONT_SIZE_TINY,
    FONT_SIZE_MEDIUM,
    FONTS_PATH,
    HEIGHT,
    HUD_DIR,
    HUD_ICONS,
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

# TODO: add support for animations
NOTIFICATION_TYPE_ICONS: dict[str, str] = {
    NotificationTypeEnum.debug.value:   "human",
    # NotificationTypeEnum.info.value:    "dots_anim",
    NotificationTypeEnum.info.value:    "dots",
    NotificationTypeEnum.warning.value: "exclamation",
    # NotificationTypeEnum.error.value:   "red_exclamation_anim",
    NotificationTypeEnum.error.value:   "red_exclamation",
    # NotificationTypeEnum.success.value: "blessed_anim",
    NotificationTypeEnum.success.value: "blessed",
    # NotificationTypeEnum.failure.value: "shocked_anim",
    NotificationTypeEnum.failure.value: "shocked",
}


class UI:
    def __init__(self, scene: Scene, tiny_font: pygame.font.Font, medium_font: pygame.font.Font) -> None:
        self.scene = scene
        self.game: Game = self.scene.game
        self.display_surface = self.game.HUD
        self.font = medium_font
        self.tiny_font = tiny_font
        self.inventory_slot: InventorySlot = InventorySlot(
            None,
            (WIDTH // 2 - (INVENTORY_ITEM_WIDTH * MAX_HOTBAR_ITEMS // 2),
             HEIGHT - INVENTORY_ITEM_WIDTH - 12),
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

        help_w = int(24 * FONT_SIZE_MEDIUM * 2.2)
        self.help_bg = NinePatch(file="nine_patch_04.png", scale=4).get_scaled_to(400 - 2, help_w)

        # self.panel_border_size = self.panel_border.get_size()
        # self.factor = 6 * 4
        # self.panel_background = pygame.Surface(
        #     (self.panel_border_size[0] - self.factor * 2,
        #      self.panel_border_size[1] - self.factor * 2)).convert_alpha()
        # self.panel_background.fill((0, 0, 0, 0))

        self.show_modal_panel_flag: bool = False
        self.show_dialog_panel_flag: bool = False
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
            border_size=(border, border),
            tooltip_offset=self.game.cursor_img.get_size(),
        )

        self.icons_dict: dict[str, pygame.Surface] = self.load_icons()

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
        formatted_text.on_update()

        return formatted_text
    #############################################################################################################

    def reset(self) -> None:
        self.show_modal_panel_flag = False
        self.show_dialog_panel_flag = False

        self.modal_panel.formatted_text.scroll_top()

        self.dialog_panel.formatted_text.scroll_top()

    #############################################################################################################
    def load_icons(self) -> dict[str, pygame.Surface]:
        icons: dict[str, pygame.Surface] = {}
        for emoji in EMOJIS_DICT.keys():
            path = EMOJIS_PATH / EMOJIS_DICT[emoji]
            image = pygame.image.load(path).convert_alpha()
            icons[emoji] = pygame.transform.scale2x(image)

        for emoji in HUD_ICONS.keys():
            path = HUD_DIR / HUD_ICONS[emoji]
            image = pygame.image.load(path).convert_alpha()
            icons[emoji] = pygame.transform.scale(image, (32, 32))

        # generate keys with letter buttons (A-Z)
        center = icons["key"].get_rect().center
        for letter in range(ord("A"), ord("Z") + 1):
            text_surf = self.tiny_font.render(chr(letter), False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -1)
            bg = icons["key"].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{chr(letter)}"] = bg

        # 0 to 9
        tiny_font = self.game.fonts[FONT_SIZE_TINY]
        for digit in range(0, 9):
            text_surf = tiny_font.render(str(digit), False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -2)
            bg = icons["key"].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{str(digit)}"] = bg

        # F1 to F12
        tiny_font = self.game.fonts[FONT_SIZE_TINY]
        for letter in range(1, 13):
            text_surf = tiny_font.render(f"F{str(letter)}", False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -2)
            bg = icons["key"].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_F{str(letter)}"] = bg

        # other keys
        for sign in "<>`[]+-":
            text_surf = self.tiny_font.render(sign, False, FONT_COLOR)
            text_rect = text_surf.get_rect(center = center).move(0, -1)
            bg = icons["key"].copy()
            bg.blit(text_surf, text_rect)
            icons[f"key_{sign}"] = bg

        return icons

    #############################################################################################################
    def display_text(
        self,
        text: str,
        pos: tuple[int, int],
        font: pygame.font.Font | None = None,
        color: pygame._common.ColorValue | None = None,
        border: bool = False
    ) -> None:
        if not font:
            font = self.font

        if not color:
            color = FONT_COLOR
        if border:
            text_surf = font.render(str(text), False, PANEL_BG_COLOR)
            text_rect = text_surf.get_rect(topleft = pos).move(2, 2)

            self.display_surface.blit(text_surf, text_rect)

        text_surf = font.render(str(text), False, color)
        text_rect = text_surf.get_rect(topleft = pos)

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
    def show_hotbar(self) -> None:

        player: Player = self.scene.player
        for i in range(MAX_HOTBAR_ITEMS):
            tl = self.inventory_slot.rect.topleft

            item_model = player.items[i].model if i < len(player.items) else None

            if player.selected_weapon and player.selected_weapon.model == item_model:
                image = self.inventory_slot.image_selected
            else:
                image = self.inventory_slot.image
            # background of slot
            self.display_surface.blit(image, (tl[0] + i * INVENTORY_ITEM_WIDTH, tl[1]))
            if i < len(player.items):
                item: ItemSprite = player.items[i]
                if item.model.type == ItemTypeEnum.weapon:
                    image = item.image_directions["up"]
                else:
                    image = item.image or pygame.Surface((TILE_SIZE, TILE_SIZE))
                image = pygame.transform.scale_by(image, INVENTORY_ITEM_SCALE)
                x_offset = 5  # size[0] // 2
                y_offset = 9
                # item image
                self.display_surface.blit(image, (x_offset + (tl[0] + i * INVENTORY_ITEM_WIDTH), y_offset + tl[1]))

                self.display_text(str(item.model.count),
                                  (6 + tl[0] + i * INVENTORY_ITEM_WIDTH, 14 + tl[1]),
                                  font=self.tiny_font,
                                  border=True)
            # selector
            if i == player.selected_item_idx:
                self.display_surface.blit(self.inventory_slot.image_selector, (tl[0] + i * INVENTORY_ITEM_WIDTH, tl[1]))

            # key shortcut
            if i <= len(player.items) - 1:
                self.display_surface.blit(
                    self.icons_dict[f"key_{i + 1}"],
                    (tl[0] + 2 + i * INVENTORY_ITEM_WIDTH + INVENTORY_ITEM_WIDTH // 4,
                     tl[1] - 22))

        # left/right hotbar selection key shortcut
        h = 24
        self.display_surface.blit(self.icons_dict["key_<"], ((tl[0] - 24), tl[1] + h))
        self.display_surface.blit(self.icons_dict["key_>"], (
                                  (tl[0] + MAX_HOTBAR_ITEMS * INVENTORY_ITEM_WIDTH - 16), tl[1] + h))

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
                surface.blit(self.icons_dict["key_Space"], pos)

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
            # render semitransparent panel in background
            rect = pygame.Rect(
                WIDTH - 400 - 32,
                15 + FONT_SIZE_MEDIUM * TEXT_ROW_SPACING,
                400 - 2,
                (len(show_actions) + 1) * FONT_SIZE_MEDIUM * TEXT_ROW_SPACING
            )

            # self.game.render_panel(rect, PANEL_BG_COLOR)
            self.display_surface.blit(self.help_bg, rect.topleft)

            for i, action in enumerate(show_actions, start=1):
                self.game.render_text(
                    # f"{', '.join(action['show']):>11} - {action['msg']}",
                    f"{action['msg']}",
                    (WIDTH - 400 + 38, 40 + int(i * FONT_SIZE_MEDIUM * 2.2)),
                    shadow = True
                )
                self.display_surface.blit(
                    self.icons_dict[action['show'][0]], (WIDTH - 400, 32 + int(i * FONT_SIZE_MEDIUM * 2.2)))
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
        icon: pygame.Surface = self.icons_dict[ACTIONS[action]["show"][0]]
        label_w, _ = self.font.size(label)
        self.display_surface.blit(self.available_action_bg,
                                  (WIDTH - TILE_SIZE - 200,
                                   HEIGHT - (2 * TILE_SIZE) - 16 - row_spacing))
        self.display_surface.blit(icon,
                                  (WIDTH - (2 * TILE_SIZE) - 16,
                                   HEIGHT - (2 * TILE_SIZE) - 14 - row_spacing))
        self.display_text(label, (WIDTH - TILE_SIZE - label_w - 40,
                                  HEIGHT - (2 * TILE_SIZE) - 7 - row_spacing), border=True)

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
        anim = self.scene.emotes[NOTIFICATION_TYPE_ICONS[notification.type]]
        animation_speed = 5
        frame_index = (animation_speed * time_elapsed)

        # if int(frame_index) >= len(anim):
        frame_index = frame_index % len(anim)
        # icon = anim[int(frame_index)]
        # scale = 2
        rich_text = self.create_rich_text(notification.message, (notification.width + 90, notification.height + 60))

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
            self.show_action("talk", 4)
    #############################################################################################################

    def activate_dialog_panel(self, dialog_text: str) -> None:
        self.show_dialog_panel_flag = True
        self.dialog_panel.set_text(dialog_text)
        self.dialog_panel.formatted_text.scroll_top()

    #############################################################################################################

    def update(self, events: list[pygame.event.EventType]) -> None:
        global INPUTS
        # if INPUTS["select"] or INPUTS["pick_up"]:
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

        self.modal_panel.on_mouse_move()
        self.modal_panel.on_update()

        self.dialog_panel.on_mouse_move()
        self.dialog_panel.on_update()

    #############################################################################################################
    def display_ui(self, elapsed_time: float) -> None:
        player: Player = self.scene.player
        # upper left corner
        # UI semitransparent background panel
        # self.box(TILE_SIZE, TILE_SIZE, 450, 125)
        self.show_stats_panel(player)

        # left middle
        # show notifications
        for row, notification in enumerate(self.scene.notifications):
            self.show_notification(notification, row)

        # upper right corner
        # FPS counter
        self.box(WIDTH - 200, TILE_SIZE, 180, 10 + (25 * 1))
        self.display_text(f"FPS: {self.game.fps:5.1f}", (WIDTH - 200 + 10, TILE_SIZE + 10))

        # lower left corner
        # weapon panel
        if not self.show_dialog_panel_flag:
            self.show_weapon_panel(player.selected_weapon, not player.can_switch_weapon, elapsed_time)
            # self.show_magic_panel(player.magic_index, not player.can_switch_magic)

            # middle lower and right upper
            # hot bar
            self.show_hotbar()

            # middle upper
            # help panel
            self.show_help()

            # lower right corner
            # available actions key shortcuts
            self.show_available_actions()

        if self.show_modal_panel_flag:
            self.show_modal_panel()

        if self.show_dialog_panel_flag:
            self.show_dialog_panel()

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
    def show_stats_panel(self, player: Player) -> None:
        self.display_surface.blit(self.stats_bg, (TILE_SIZE, TILE_SIZE))

        left_margin = 30
        top_margin = 40
        row_height = 35
        icon_scale = 2
        icon_offset = TILE_SIZE // 2
        ###########################################################################
        # HEALTH
        # self.display_text("Health", (TILE_SIZE + left_margin, TILE_SIZE + top_margin))
        icon = pygame.transform.scale_by(self.scene.items_sheet["big_heart"][0], icon_scale)
        self.display_surface.blit(icon, (TILE_SIZE + left_margin, icon_offset + top_margin))
        hb = player.health_bar_ui
        hb.set_bar(player.model.health / player.model.max_health,
                   (4 * TILE_SIZE + left_margin, TILE_SIZE + top_margin - 8))
        self.display_surface.blit(hb.image, hb.rect)

        ###########################################################################
        # WEIGHT
        icon = pygame.transform.scale_by(self.scene.items_sheet["pan_balance"][0], icon_scale)
        self.display_surface.blit(icon, (TILE_SIZE + left_margin, icon_offset + top_margin + row_height))
        self.display_text(
            f"{player.total_items_weight:4.2f}/{player.model.max_carry_weight:4.2f}",
            color=(0, 197, 199),
            border=True,
            pos=(4 * TILE_SIZE + left_margin, TILE_SIZE + top_margin + row_height))

        # if player.selected_item_idx >= 0:
        #     item_model = player.items[player.selected_item_idx].model
        #     item = f"{item_model.name} ({item_model.count})"
        # else:
        #     item = "N/A"
        # self.display_text(
        #     f"Item    {item}", (TILE_SIZE + left_margin, TILE_SIZE + + top_margin + row_height * 2))

        ###########################################################################
        # HOUR
        icon = pygame.transform.scale_by(self.scene.items_sheet["hourglass"][0], icon_scale)
        self.display_surface.blit(icon, (TILE_SIZE + left_margin, icon_offset + top_margin + row_height * 2))
        # self.show_bar(player.energy, player.stats['energy'], self.energy_bar_rect, ENERGY_COLOR)
        self.display_text(
            f"{self.scene.hour:d}:{self.scene.minute:02d}",
            color=(0, 197, 199),
            border=True,
            pos=(4 * TILE_SIZE + left_margin, TILE_SIZE + top_margin + row_height * 2))

        ###########################################################################
        # MONEY
        icon = pygame.transform.scale_by(self.scene.items_sheet["coin"][0], icon_scale)
        self.display_surface.blit(icon, (TILE_SIZE + left_margin, icon_offset + top_margin + row_height * 3))
        self.display_text(
            f"{player.model.money}",
            color=(0, 197, 199),
            border=True,
            pos=(4 * TILE_SIZE + left_margin, TILE_SIZE + top_margin + row_height * 3))

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
                          color=CHAR_NAME_COLOR)
        # draw key shortcuts
        pos = (self.dialog_panel_offset[0] + dialog_panel_size[0] - 15,
               self.dialog_panel_offset[1] + 40)
        self.display_surface.blit(self.icons_dict["key_Space"], pos)

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
