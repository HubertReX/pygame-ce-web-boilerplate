
#################################################################################################################
import pygame

from settings import HUD_DIR, TRANSPARENT_COLOR, load_image


class NinePatch():

    def __init__(self, file: str = "", pos: tuple[int, int] = (0, 0), scale: int = 1, border: int = 6) -> None:
        self.border = border * scale
        self.pos = pos
        # self.message = message

        if not file:
            file = "nine_patch_05.png"

        self.image_org: pygame.Surface = load_image(HUD_DIR / "Theme" / file).convert_alpha()

        if scale != 1:
            self.image_org = pygame.transform.scale_by(self.image_org, scale)

        self.image: pygame.Surface = self.image_org

        self.rect_org: pygame.Rect = self.image_org.get_rect(topleft = pos)
        self.rect: pygame.Rect = self.image.get_rect(topleft = pos)

    def get_border_topleft(self) -> pygame.Surface:
        return self.image_org.subsurface(0, 0, self.border, self.border)

    def get_border_topright(self) -> pygame.Surface:
        return self.image_org.subsurface(self.rect_org.width - self.border, 0, self.border, self.border)

    def get_border_bottomleft(self) -> pygame.Surface:
        return self.image_org.subsurface(0, self.rect_org.height - self.border, self.border, self.border)

    def get_border_bottomright(self) -> pygame.Surface:
        return self.image_org.subsurface(self.rect_org.width - self.border,
                                         self.rect_org.height - self.border, self.border, self.border)

    def get_border_top(self, width: int, height: int) -> pygame.Surface:
        image = self.image_org.subsurface(self.border, 0,
                                          self.rect_org.width - (2 * self.border),
                                          self.border)

        return pygame.transform.scale(image, (width, height))

    def get_border_bottom(self, width: int, height: int) -> pygame.Surface:
        image = self.image_org.subsurface(self.border, self.rect_org.height - self.border,
                                          self.rect_org.width - (2 * self.border),
                                          self.border)

        return pygame.transform.scale(image, (width, height))

    def get_border_left(self, width: int, height: int) -> pygame.Surface:
        image = self.image_org.subsurface(0, self.border,
                                          self.border,
                                          self.rect_org.height - (2 * self.border))

        return pygame.transform.scale(image, (width, height))

    def get_border_right(self, width: int, height: int) -> pygame.Surface:
        image = self.image_org.subsurface(self.rect_org.width - self.border, self.border,
                                          self.border,
                                          self.rect_org.height - (2 * self.border))

        return pygame.transform.scale(image, (width, height))

    def get_middle(self, width: int, height: int) -> pygame.Surface:
        image = self.image_org.subsurface(self.border, self.border,
                                          self.rect_org.width - (2 * self.border),
                                          self.rect_org.height - (2 * self.border))

        return pygame.transform.scale(image, (width, height))

    def get_scaled_to_image(self, image: pygame.Surface) -> pygame.Surface:
        rect = image.get_rect()
        # print(rect.width, rect.height)

        self.get_scaled_fit(rect.width, rect.height)
        self.image.blit(image, (self.border, self.border))

        return self.image

    def get_scaled_fit(self, width: int, height: int) -> pygame.Surface:
        return self.get_scaled_to(width + (2 * self.border), height + (2 * self.border))

    def get_scaled_to(self, width: int, height: int) -> pygame.Surface:
        if width <= self.rect_org.width:
            width = self.rect_org.width

        if height <= self.rect_org.height:
            height = self.rect_org.height

        inner_width = width - (2 * self.border)
        inner_height = height - (2 * self.border)
        self.image = pygame.Surface((width, height)).convert_alpha()
        self.rect = self.image.get_rect()
        self.image.fill(TRANSPARENT_COLOR)
        self.image.blit(self.get_border_topleft(), (0, 0))
        self.image.blit(self.get_border_top(inner_width, self.border), (self.border, 0))
        self.image.blit(self.get_border_topright(), (width - self.border, 0))

        self.image.blit(self.get_border_left(self.border, inner_height), (0, self.border))
        self.image.blit(self.get_middle(inner_width, inner_height), (self.border, self.border))
        self.image.blit(self.get_border_right(self.border, inner_height), (width - self.border, self.border))

        self.image.blit(self.get_border_bottomleft(), (0, height - self.border))
        self.image.blit(self.get_border_bottom(inner_width, self.border), (self.border, height - self.border))
        self.image.blit(self.get_border_bottomright(), (width - self.border, height - self.border))

        self.rect = self.image.get_rect(topleft = self.pos)

        return self.image
#################################################################################################################
