import pygame
from settings import FONT_COLOR, PANEL_BG_COLOR, TILE_SIZE, WIDTH, HEIGHT


class UI:
    def __init__(self, screen: pygame.Surface, font: pygame.Surface):
        self.display_surface = screen
        self.font = font

    def display_text(self, text: str, pos: tuple[int, int]):
        text_surf = self.font.render(str(text), False, FONT_COLOR)
        text_rect = text_surf.get_rect(topleft = pos)

        self.display_surface.blit(text_surf, text_rect)

    def box(self, left, top, width, height):
        UI_BORDER_COLOR = '#111111'

        bg_rect = pygame.Rect(left, top, width, height)

        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA).convert_alpha()
        bg_surface.fill(PANEL_BG_COLOR)
        self.display_surface.blit(bg_surface, bg_rect.topleft)

        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)

    def selection_box(self, left, top, has_switched, cooldown=100):
        ITEM_BOX_SIZE = TILE_SIZE * 8
        UI_BORDER_COLOR = '#111111'
        UI_BORDER_COLOR_ACTIVE = 'gold'
        UI_COOL_OFF_COLOR = "red"

        c = 1 - max(0, cooldown / 100)
        h = int(ITEM_BOX_SIZE * c)
        bg_cool_off_rect = pygame.Rect(left, top + ITEM_BOX_SIZE - h, ITEM_BOX_SIZE, h)
        bg_rect = pygame.Rect(left, top, ITEM_BOX_SIZE, ITEM_BOX_SIZE)

        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA).convert_alpha()
        bg_surface.fill(PANEL_BG_COLOR)
        # pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_cool_rect)
        self.display_surface.blit(bg_surface, bg_rect.topleft)
        # if cooldown < 100:
        pygame.draw.rect(self.display_surface, UI_COOL_OFF_COLOR, bg_cool_off_rect)

        if has_switched:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR_ACTIVE, bg_rect, 3)
        else:
            pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3)
        return bg_rect

    def weapon_overlay(self, weapon, has_switched, cooldown):
        bg_rect = self.selection_box(TILE_SIZE, HEIGHT - (TILE_SIZE * 9), has_switched, cooldown)
        if weapon:
            weapon_surf = pygame.transform.scale(weapon.image_directions["up"], (TILE_SIZE * 7, TILE_SIZE * 7))
            weapon_rect = weapon_surf.get_rect(center = bg_rect.center)

            self.display_surface.blit(weapon_surf, weapon_rect)

    # def magic_overlay(self, magic_index, has_switched):
    #     bg_rect = self.selection_box(80, 635, has_switched)
    #     magic_surf = self.magic_graphics[magic_index]
    #     magic_rect = magic_surf.get_rect(center = bg_rect.center)

    #     self.display_surface.blit(magic_surf, magic_rect)

    def display(self, player, elapsed_time: float):
        # UI semitransparent background panel
        self.box(TILE_SIZE, TILE_SIZE, 320, 100)

        self.display_text("Health", (TILE_SIZE + 10, TILE_SIZE + 20))
        hb = player.health_bar_ui
        hb.set_bar(player.model.health / player.model.max_health, (TILE_SIZE + 150, TILE_SIZE + 10))
        self.display_surface.blit(hb.image, hb.rect)
        # self.show_bar(player.energy, player.stats['energy'], self.energy_bar_rect, ENERGY_COLOR)

        self.display_text(
            f"Weight  {player.total_items_weight:4.2f}/{player.model.max_carry_weight:4.2f}",
            (TILE_SIZE + 10, TILE_SIZE + 45))
        self.display_text(
            f"Money   {player.model.money}", (TILE_SIZE + 10, TILE_SIZE + 70))

        # weapon panel
        if player.is_attacking:
            now = elapsed_time - player.attack_time
            weapon_cooldown = player.selected_weapon.model.cooldown_time if player.selected_weapon else 0.0
            limit = (player.attack_cooldown / 1000.0) + weapon_cooldown
            res = int(now / limit * 100)
            res = min(100, res)
        else:
            res = 100

        self.weapon_overlay(player.selected_weapon, not player.can_switch_weapon, res)
        # self.magic_overlay(player.magic_index, not player.can_switch_magic)