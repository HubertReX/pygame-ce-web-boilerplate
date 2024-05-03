from datetime import datetime
from os import environ
from typing import Sequence
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import asyncio
import os
from settings import *
import pygame, sys
if USE_SHADERS:
    from opengl_shader import OpenGL_shader

traceback.install(show_locals=True, width=150, )

class Game:
    def __init__(self) -> None:
        pygame.init()
        self.clock: pygame.time.Clock = pygame.time.Clock()
        # time elapsed in seconds (milliseconds as fraction) without pause time
        self.time_elapsed: float = 0.0
        
        pygame.display.set_caption(GAME_NAME)
        program_icon = pygame.image.load(PROGRAM_ICON)
        pygame.display.set_icon(program_icon)
        
        # https://coderslegacy.com/python/pygame-rpg-improving-performance/
        self.flags: int = 0
            
        if IS_FULLSCREEN:
            self.flags = self.flags | pygame.FULLSCREEN
        
        if IS_WEB:
            # for now shader works only in web mode (to be fixed)
            if USE_SHADERS:
                self.flags = self.flags | pygame.OPENGL | pygame.DOUBLEBUF
            else:
                self.flags = self.flags | pygame.DOUBLEBUF
    
            self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags)
        else:
            self.flags = self.flags | pygame.SCALED | pygame.DOUBLEBUF # pygame.RESIZABLE
            self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags, vsync=1)
            
        self.canvas: pygame.Surface = pygame.Surface((WIDTH, HEIGHT), self.flags) # , 32 .convert_alpha() # pygame.SRCALPHA

        size = pygame.display.get_window_size()
        if USE_SHADERS:
            self.shader = OpenGL_shader(size, Path("shaders") / "fs.glsl", Path("shaders") / "vs.glsl")
        # self.canvas.set_colorkey(COLORS["black"])
        self.fonts = {}
        font_sizes = [FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE]
        for font_size in font_sizes:
            self.fonts[font_size] = pygame.font.Font(MAIN_FONT, font_size)
        
        self.font = self.fonts[FONT_SIZE_MEDIUM]
        self.is_running = True

        # stacked game states (e.g. Scene, Menu)
        self.states = []
        # dict of custom events with callable functions (not used for now since pygame.time.set_timer is not implemented in pygbag)
        self.custom_events: dict[int, callable] = {}
        # moved imports here to avoid circular imports
        # import menus
        # start_state = menus.MainMenuScreen(self, "MainMenu")
        # self.states.append(start_state)
        import scene
        start_state = scene.Scene(self, 'Village', 'start')
        # start_state = scene.Scene(self, 'Maze', 'start', is_maze=True, maze_cols=10, maze_rows=5)
        start_state.enter_state()
        self.states.append(start_state)
        # self.states.append(start_state)
        
        if USE_CUSTOM_MOUSE_CURSOR:
            cursor_img = pygame.image.load(MOUSE_CURSOR_IMG)
            scale = cursor_img.get_width() // (TILE_SIZE)
            self.cursor_img = pygame.transform.scale(cursor_img, (scale, scale)).convert_alpha()
            # self.cursor_img = pygame.transform.invert(self.cursor_img)
            self.cursor_img.set_alpha(150)
            pygame.mouse.set_visible(False)
            
    
    def render_panel(self, rect: pygame.Rect, color: str | Sequence[int]) -> None:
            """
            Renders semitransparent (if alpha provided) rect using provided color on game.canvas

                Parameters:
                        rect (Rect): Size and position of rect
                        color (str|Sequence[int]): color to fill in the rect (with alpha)
            """        
            surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(surf, color, surf.get_rect())
            self.canvas.blit(surf, rect)        
        
        
    def render_texts(            
            self, 
            texts: list[str], 
            pos: list[int], 
            color: str="white", 
            bg_color: list[int] | None = None, 
            shadow: bool=True, 
            font_size: int=0, 
            centred=False
        ):
        """
        Blit several lines of text on game.canvas, one under other, 
        """
        for line_no, text in enumerate(texts):
            if font_size == 0:
                font_size = FONT_SIZE_SMALL
            new_pos = [pos[0], pos[1] + line_no * font_size * TEXT_ROW_SPACING]
            self.render_text(text, new_pos, color, bg_color, shadow, font_size, centred)

        
    def render_text(
            self, 
            text: str, 
            pos: list[int], 
            color: str="white", 
            bg_color: list[int] | None = None, 
            shadow: bool=True, 
            font_size: int=0, 
            centred=False
        ):
        """
        Blit line of text on game.canvas
        """
        selected_font = self.font
        if self.fonts.get(font_size, False):
            selected_font = self.fonts[font_size]
            
        surf: pygame.surface.Surface = selected_font.render(text, False, color)
        rect: pygame.Rect = surf.get_rect(center = pos) if centred else surf.get_rect(topleft = pos)

        # alpha blend semitransparent rect in background 8 pixels bigger than rect
        # works well for single line of text
        if bg_color:
            bg_rect: pygame.Rect = rect.copy().inflate(18, 18).move(-4, -4)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA) #, pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, bg_color, bg_surf.get_rect())
            self.canvas.blit(bg_surf, bg_rect)        

        # add black outline (render black text moved by offset to all 4 directions)
        if shadow:
            surf_shadow: pygame.surface.Surface = selected_font.render(text, False, (0,0,0,0))
            offset = 2
            self.canvas.blit(surf_shadow, (rect.x-offset, rect.y))
            self.canvas.blit(surf_shadow, (rect.x+offset, rect.y))
            self.canvas.blit(surf_shadow, (rect.x, rect.y-offset))
            self.canvas.blit(surf_shadow, (rect.x, rect.y+offset))
            
        self.canvas.blit(surf, rect)
        
    def custom_cursor(self, screen: pygame.Surface):
        """
        blit custom cursor in mouse current position if USE_CUSTOM_MOUSE_CURSOR is enabled
        """
        if not USE_CUSTOM_MOUSE_CURSOR:
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
    
    def get_animations(self, path: str) -> dict[str, Any]:
        """
        read sprite animations from given folder

        :param path: folder containing folders with animations names that contain frames as separate files
        :type path: str
        :return: dictionary with animation name (subfolder) as keys
        """
        animations = {}
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                animations.update({file: []})
        return animations

    def save_screenshot(self):
        """
        save current screen to SCREENSHOT_FOLDER as PNG with timestamp in name
        """
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = SCREENSHOTS_DIR / f"screenshot_{time_str}.png"
        pygame.image.save(self.screen, file_name)
        if IS_WEB:
            import platform
            platform.window.download_from_browser_fs(file_name.as_posix(), "image/png")
        else:
            print(f"screenshot saved to file '{file_name}'")
            
        # self.reset_inputs()
            
    def register_custom_event(self, custom_event_id: int, handle_function: callable):
        self.custom_events[custom_event_id] = handle_function
    
    def get_inputs(self) -> list[pygame.event.EventType]:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.is_running = False
                pygame.quit()
                sys.exit()
                
            global IS_PAUSED
            
            if event.type in [pygame.WINDOWHIDDEN, pygame.WINDOWMINIMIZED, pygame.WINDOWFOCUSLOST]:
                IS_PAUSED = True
                print(f"{IS_PAUSED=}")
                
            elif event.type in [pygame.WINDOWSHOWN, pygame.WINDOWMAXIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWFOCUSGAINED]:
                IS_PAUSED = False
                # print(f"{IS_PAUSED=}")
            elif event.type in self.custom_events:
                handler = self.custom_events[event.type]
                handler()
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
                    INPUTS["zoom_in"] = True
                elif event.y == -1:
                    INPUTS["scroll_down"] = True
                    INPUTS["zoom_out"] = True
                    
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
        while self.is_running:
            # delta time since last frame in milliseconds
            dt = self.clock.tick(FPS_CAP) / 1000
            events = []
            events = self.get_inputs()

            # first draw on separate Surface (game.canvas)
            if not IS_PAUSED:
                self.time_elapsed += dt
                self.states[-1].update(dt, events)
            self.canvas.fill((0,0,0,0))
            self.states[-1].draw(self.canvas, dt)
            self.custom_cursor(self.canvas)
            
            if IS_PAUSED:
                self.render_text("PAUSED", (WIDTH*SCALE // 2, HEIGHT*SCALE // 2), font_size=FONT_SIZE_LARGE, centred=True, bg_color=(10,10,10,150), shadow=True)
            
            # than scale and copy on final Surface (game.screen)
            self.screen.blit(pygame.transform.scale_by(self.canvas, SCALE), (0,0))
            
            # shaders are used for postprocessing special effects
            # the whole Surface is used as texture on rect that fills to a full screen
            
            if USE_SHADERS:
                self.shader.render(self.screen, dt)
            else:
                pygame.display.update()
            await asyncio.sleep(0)
            
            