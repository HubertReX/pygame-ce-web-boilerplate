import asyncio
import os
import pygame, sys
from state import SplashScreen
from settings import *



class Game:
    def __init__(self) -> None:
        pygame.init()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.flags: int = 0 # pygame.RESIZABLE
        if IS_FULLSCREEN:
            self.flags = pygame.FULLSCREEN|pygame.SCALED
            
        self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags)
        pygame.display.set_caption("GAME")
        self.canvas: pygame.Surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.font = pygame.font.Font(FONT, TILE_SIZE*2)
        self.running = True

        self.states = []
        self.splash_screen = SplashScreen(self)
        self.states.append(self.splash_screen)
        if USE_CUSTOM_CURSOR:
            self.cursor_img = pygame.transform.scale(pygame.image.load("assets/aim.png"), (32,32)).convert_alpha()
            self.cursor_img.set_alpha(150)
            pygame.mouse.set_visible(False)
        
    def render_text(self, text: str, pos: list[int], color: str="white", font: pygame.font=None, centred=False):
        if not font:
            font = self.font
        surf: pygame.surface.Surface = font.render(text, False, color)
        rect: pygame.Rect = surf.get_rect(center = pos) if centred else surf.get_rect(topleft = pos)
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
            img = pygame.image.load(full_path).convert_alpha()
            images.append(img)
        return images
    
    def get_animations(self, path: str):
        animations = {}
        for file in os.listdir(path):
            animations.update({file: []})
        return animations
        
        
    def get_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key in[pygame.K_ESCAPE, pygame.K_q]:
                    INPUTS['quit'] = True
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    INPUTS['select'] = True
                elif event.key == pygame.K_r:
                    INPUTS['reload'] = True
                elif event.key == pygame.K_EQUALS:
                    INPUTS['zoom_in'] = True
                elif event.key == pygame.K_MINUS:
                    INPUTS['zoom_out'] = True
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    INPUTS['left'] = True
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    INPUTS['right'] = True
                elif event.key in [pygame.K_UP, pygame.K_w]:
                    INPUTS['up'] = True
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    INPUTS['down'] = True
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    INPUTS['quit'] = False
                elif event.key == pygame.K_SPACE:
                    INPUTS['select'] = False
                elif event.key == pygame.K_r:
                    INPUTS['reload'] = False
                elif event.key == pygame.K_EQUALS:
                    INPUTS['zoom_in'] = False
                elif event.key == pygame.K_MINUS:
                    INPUTS['zoom_out'] = False
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    INPUTS['left'] = False
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    INPUTS['right'] = False
                elif event.key in [pygame.K_UP, pygame.K_w]:
                    INPUTS['up'] = False
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    INPUTS['down'] = False
                    
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
                    
    def reset_inputs(self):
        for key in KEYS:
            INPUTS[key] = False
            
    async def loop(self):
        while self.running:
            dt = self.clock.tick(FPS_CAP) / 1000
            self.get_inputs()
            self.states[-1].update(dt)
            self.states[-1].draw(self.canvas)
            self.custom_cursor(self.canvas)
            self.screen.fill("black")
            self.screen.blit(pygame.transform.scale_by(self.canvas, SCALE), (0,0))
            pygame.display.update()
            await asyncio.sleep(0)
            
            