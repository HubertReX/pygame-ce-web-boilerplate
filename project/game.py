from datetime import datetime
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import asyncio
import os
from settings import *
import pygame, sys

traceback.install(show_locals=True, width=150, )  

class Game:
    def __init__(self) -> None:
        pygame.init()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        pygame.display.set_caption(GAME_NAME)
        program_icon = pygame.image.load(PROGRAM_ICON)
        pygame.display.set_icon(program_icon)
        
        # https://coderslegacy.com/python/pygame-rpg-improving-performance/
        self.flags: int =  0
        if not IS_WEB:
            self.flags = self.flags | pygame.SCALED | pygame.DOUBLEBUF # pygame.RESIZABLE
            
        if IS_FULLSCREEN:
            self.flags = self.flags | pygame.FULLSCREEN
        
        if IS_WEB:
            self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags)
        else:
            self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags, vsync=1)
        self.canvas: pygame.Surface = pygame.Surface((WIDTH, HEIGHT)) #.convert_alpha()
        # self.canvas.set_colorkey(COLORS["black"])
        self.fonts = {}
        font_sizes = [FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE]
        for font_size in font_sizes:
            self.fonts[font_size] = pygame.font.Font(MAIN_FONT, font_size)
        
        self.font = self.fonts[FONT_SIZE_MEDIUM]
        self.running = True

        self.states = []
        # moved here to avoid circular imports
        import menus
        self.splash_screen = menus.MainMenuScreen(self, "MainMenu")
        self.states.append(self.splash_screen)
        if USE_CUSTOM_CURSOR:
            self.cursor_img = pygame.transform.scale(pygame.image.load("assets/aim.png"), (32,32)).convert_alpha()
            self.cursor_img = pygame.transform.invert(self.cursor_img)
            self.cursor_img.set_alpha(150)
            pygame.mouse.set_visible(False)
        
    def render_text(
            self, text: str, 
            pos: list[int], 
            color: str="white", 
            bg_color: str=None, 
            shadow: bool=True, 
            font_size: int=0, 
            centred=False
        ):
        selected_font = self.font
        if self.fonts.get(font_size, False):
            selected_font = self.fonts[font_size]
            
        surf: pygame.surface.Surface = selected_font.render(text, False, color)
        rect: pygame.Rect = surf.get_rect(center = pos) if centred else surf.get_rect(topleft = pos)
        
        if bg_color:
            bg_rect: pygame.Rect = rect.copy().inflate(15, 15)
            pygame.draw.rect(self.canvas, bg_color, bg_rect)
        
        if shadow:
            surf_shadow: pygame.surface.Surface = selected_font.render(text, False, "black")
            offset = 2
            self.canvas.blit(surf_shadow, (rect.x-offset, rect.y))
            self.canvas.blit(surf_shadow, (rect.x+offset, rect.y))
            self.canvas.blit(surf_shadow, (rect.x, rect.y-offset))
            self.canvas.blit(surf_shadow, (rect.x, rect.y+offset))
            # self.canvas.blit(pygame.transform.scale_by(surf_shadow, 1.2), (rect.x-2, rect.y-2))
            
            # rect_shadow = rect.copy()
            # rect_shadow[0] += 3
            # rect_shadow[1] += 3
            # self.canvas.blit(surf_shadow, rect_shadow)
            
        self.canvas.blit(surf, rect)
        
    def custom_cursor(self, screen: pygame.Surface):
        if not USE_CUSTOM_CURSOR:
            return
        cursor_rect = self.cursor_img.get_frect(center=pygame.mouse.get_pos())
        screen.blit(self.cursor_img, cursor_rect.center)
        
    def get_images(self, path: str):
        images = []
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            # img = pygame.image.load(full_path).convert_alpha()
            img = pygame.image.load(full_path) #.convert()
            images.append(img)
        return images
    
    def get_animations(self, path: str):
        animations = {}
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                animations.update({file: []})
        return animations

    def save_screenshot(self):
        # save current screen to SCREENSHOT_FOLDER as PNG with timestamp in name
        
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = SCREENSHOTS_DIR / f"screenshot_{time_str}.png"
        pygame.image.save(self.screen, file_name)
        if IS_WEB:
            import platform
            platform.window.download_from_browser_fs(file_name.as_posix(), "image/png")
        else:
            print(f"screenshot saved to file '{file_name}'")
            
        # self.reset_inputs()
            
        
    def get_inputs(self) -> list[pygame.event.EventType]:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
                
            global IS_PAUSED
            
            if event.type in [pygame.WINDOWHIDDEN, pygame.WINDOWMINIMIZED, pygame.WINDOWFOCUSLOST]:
                IS_PAUSED = True
                print(f"{IS_PAUSED=}")
                
            elif event.type in [pygame.WINDOWSHOWN, pygame.WINDOWMAXIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWFOCUSGAINED]:
                IS_PAUSED = False
                # print(f"{IS_PAUSED=}")
            elif event.type == pygame.KEYDOWN:
                for action, definition in ACTIONS.items():
                    if event.key in definition["keys"]:
                        INPUTS[action] = True
            elif event.type == pygame.KEYUP:
                for action, definition in ACTIONS.items():
                    if event.key in definition["keys"]:
                        INPUTS[action] = False
                                    
            elif event.type == pygame.MOUSEWHEEL:
                if event.y == 1:
                    INPUTS["scroll_up"] = True
                elif event.y == -1:
                    INPUTS["scroll_down"] = True
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    INPUTS["left_click"] = True
                elif event.button == 3:
                    INPUTS["right_click"] = True
                elif event.button == 4:
                    INPUTS["scroll_click"] = True
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    INPUTS["left_click"] = False
                elif event.button == 3:
                    INPUTS["right_click"] = False
                elif event.button == 4:
                    INPUTS["scroll_click"] = False
        return events
                    
    def reset_inputs(self):
        for key in ACTIONS.keys():
            INPUTS[key] = False
            
    async def loop(self):
        while self.running:
            dt = self.clock.tick(FPS_CAP) / 1000
            events = []
            # if self.states[-1].__class__.__name__ != "MenuScreen":
            #     self.get_inputs()
            events = self.get_inputs()
            # print(f"loop {IS_PAUSED=}")
            if not IS_PAUSED:
                self.states[-1].update(dt, events)
                self.canvas.fill("black")
                self.states[-1].draw(self.canvas)
                self.custom_cursor(self.canvas)
                # self.screen.fill("black")
            else:
                self.render_text("PAUSED", (WIDTH*SCALE // 2, HEIGHT*SCALE // 2), font_size=FONT_SIZE_LARGE, centred=True)
            
            self.screen.blit(pygame.transform.scale_by(self.canvas, SCALE), (0,0))
            pygame.display.update()
            await asyncio.sleep(0)
            
            