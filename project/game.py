from datetime import datetime
from os import environ
from typing import Sequence
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import asyncio
import os
from config_model.config import load_config
from settings import *
import pygame, sys
from opengl_shader import OpenGL_shader
if not IS_WEB:
    from pygame_screen_record import ScreenRecorder, add_codec

    # add_codec("mp4", "mpv4")
    # add_codec("webm", "vp90")

if USE_SOD:
    from second_order_dynamics import SecondOrderDynamics

traceback.install(show_locals=True, width=150, )
# os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"

#MARK: Game
class Game:
    def __init__(self) -> None:
        self.conf = load_config(CONFIG_FILE)
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
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 0)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_ES)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        else:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
                
        self.flags = self.flags | pygame.OPENGL| pygame.DOUBLEBUF # pygame.RESIZABLE , | pygame.SCALED 
        self.screen: pygame.Surface = pygame.display.set_mode((WIDTH*SCALE, HEIGHT*SCALE), self.flags, vsync=1)
            
        self.canvas: pygame.Surface = pygame.Surface((WIDTH, HEIGHT), self.flags) # , 32 .convert_alpha() # pygame.SRCALPHA

        size = self.screen.get_size()
        self.shader = OpenGL_shader(size, DEFAULT_SHADER)

        self.fonts = {}
        font_sizes = [FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE]
        for font_size in font_sizes:
            self.fonts[font_size] = pygame.font.Font(MAIN_FONT, font_size)
        
        self.font = self.fonts[FONT_SIZE_DEFAULT]
        self.is_running = True
        self.is_paused = False

        # stacked game states (e.g. Scene, Menu)
        from state import State
        self.states: list[State] = []
        # dict of custom events with callable functions (not used for now since pygame.time.set_timer is not implemented in pygbag)
        self.custom_events: dict[int, callable] = {}
        # moved imports here to avoid circular imports
        # import menus
        # start_state = menus.MainMenuScreen(self, "MainMenu")
        # self.states.append(start_state)
        import scene
        start_state = scene.Scene(self, "Village", "start")
        # start_state = scene.Scene(self, "Maze", "start", is_maze=True, maze_cols=10, maze_rows=5)
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
        if USE_SOD:
            self.init_SOD()


    def init_SOD(self):
        f = 0.01 # frequency, reaction speed and oscillation
        z = 0.3  # zeta, damping factor
        r = -3.0 # response, immediate, overshoot, anticipation
        self.sod_time = 0.01
        cursor_rect = self.cursor_img.get_frect(center=pygame.mouse.get_pos())
        pos = vec(cursor_rect.center)
        
        self.SOD = SecondOrderDynamics(f, z, r, x0=pos)
    
    
    #MARK: render
    def render_panel(self, rect: pygame.Rect, color: ColorValue, surface: pygame.Surface = None) -> None:
        """
        Renders semitransparent (if `alpha` provided) rect using provided color on `game.canvas`

        Args:
            rect (pygame.Rect): Size and position of panel
            color (ColorValue): color to fill in the panel (with alpha)
            surface (pygame.Surface): surface to blit on. Defaults to None

        Returns:
            None
        """        
        if not surface:
            surface = self.canvas
            
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, color, surf.get_rect())
        surface.blit(surf, rect)        
        
        
    def render_texts(            
            self, 
            texts:     list[str], 
            pos:       list[int], 
            color:     ColorValue = "white", 
            bg_color:  ColorValue = 0, 
            shadow:    ColorValue = (10,10,10,255), 
            font_size: int = 0, 
            centred:   bool = False,
            surface:   pygame.Surface = None
        ):
        """
        Blit several lines of text on surface or on `game.canvas` if surface is not provided, one under other, 

        Args:
            texts (list[str]): list of strings to render
            pos (list[int]): position of first row
            color (ColorValue, optional): text color. Defaults to `"white"`.
            bg_color (ColorValue, optional): draw background panel. Defaults to `0` == no bg.
            shadow (ColorValue, optional): draw outline of text with black color. Defaults to `(10,10,10,255)`.
            font_size (int, optional): font size from predefined list `FONT_SIZES_DICT`. Defaults to `0` == `FONT_SIZE_DEFAULT`.
            centred (bool, optional): shell the text be centered at `pos`. Defaults to `False`.
            surface (pygame.Surface, optional): surface to blit on, if `None` user `game.canvas`. Defaults to `None`.
        """
        for line_no, text in enumerate(texts):
            if font_size == 0:
                font_size = FONT_SIZE_SMALL
            new_pos = [pos[0], pos[1] + line_no * font_size * TEXT_ROW_SPACING]
            self.render_text(text, new_pos, color, bg_color, shadow, font_size, centred, surface)

        
    def render_text(
            self, 
            text:      str, 
            pos:       list[int], 
            color:     ColorValue = "white",
            bg_color:  ColorValue = 0, 
            shadow:    ColorValue = (10,10,10,255), 
            font_size: int = 0, 
            centred:   bool = False,
            surface:   pygame.Surface = None
        ):
        """
        Blit line of text on `surface` or on `game.canvas` if `surface` is not provided

        Args:
            text (str): _description_
            pos (list[int]): _description_
            color (ColorValue, optional): _description_. Defaults to `"white"`.
            bg_color (ColorValue, optional): _description_. Defaults to `0` == no bg.
            shadow (ColorValue, optional): _description_. Defaults to `(10,10,10,255)`.
            font_size (int, optional): _description_. Defaults to `0` == `FONT_SIZE_DEFAULT`.
            centred (bool, optional): _description_. Defaults to `False`.
            surface (pygame.Surface, optional): _description_. Defaults to `None`.
        """
        
        
        if not surface:
            surface = self.canvas
            
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
            surface.blit(bg_surf, bg_rect)        

        # add black outline (render black text moved by offset to all 4 directions)
        if shadow:
            surf_shadow: pygame.surface.Surface = selected_font.render(text, False, shadow)
            offset = 1
            surface.blit(surf_shadow, (rect.x-offset, rect.y))
            surface.blit(surf_shadow, (rect.x+offset, rect.y))
            surface.blit(surf_shadow, (rect.x,        rect.y-offset))
            surface.blit(surf_shadow, (rect.x,        rect.y+offset))
            
        surface.blit(surf, rect)
        
        
    def custom_cursor(self, screen: pygame.Surface):
        """
        blit custom cursor in mouse current position if USE_CUSTOM_MOUSE_CURSOR is enabled
        """
        if not USE_CUSTOM_MOUSE_CURSOR:
            return
        
        cursor_rect = self.cursor_img.get_frect(center=pygame.mouse.get_pos())
        
        if USE_SOD:
            pos = vec(cursor_rect.center)
            if self.time_elapsed - self.sod_time > 3:
                self.sod_time = self.time_elapsed + 0.01
                self.SOD.reset(pos)

            res = self.SOD.update(self.time_elapsed - self.sod_time, pos,)
            res[0] = max(0, res[0])
            res[1] = max(0, res[1])
            
            res[0] = min(WIDTH - 8, res[0])
            res[1] = min(HEIGHT - 8, res[1])
            screen.blit(self.cursor_img, res)
        else:
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
    
    
    #MARK: get_inputs
    def get_inputs(self) -> list[pygame.event.EventType]:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.is_running = False
                # pygame.quit()
                # sys.exit()
                
            # global IS_PAUSED
            
            if event.type in [pygame.WINDOWHIDDEN, pygame.WINDOWMINIMIZED, pygame.WINDOWFOCUSLOST]:
                self.is_paused = True
                print(f"{self.is_paused=}")
                
            elif event.type in [pygame.WINDOWSHOWN, pygame.WINDOWMAXIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWFOCUSGAINED]:
                self.is_paused = False
                # print(f"{self.is_paused=}")
            elif event.type in self.custom_events:
                handler = self.custom_events[event.type]
                handler(**event.dict)
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
                    
        global USE_SHADERS
        # global IS_PAUSED
        if INPUTS["pause"]:
            # IS_PAUSED = not IS_PAUSED
            self.is_paused = not self.is_paused
            print(f"{self.is_paused=}")
            INPUTS["pause"] = False
        
        if INPUTS["record"]:
            if not IS_WEB:
                if self.recorder.running_thread is None:
                    self.recorder.start_rec()
                    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"recording_{time_str}.mp4"
                    self.recordings_names.append(file_name)
                    print("Recording started")
                else:
                    self.recorder.stop_rec()
                    print("Recording stopped")
            INPUTS["record"] = False            
        
        if INPUTS["shaders_toggle"]:
            USE_SHADERS = not USE_SHADERS
            INPUTS["shaders_toggle"] = False            
        
        if INPUTS["next_shader"]:
            shader_index = SHADERS_NAMES.index(self.shader.shader_name)
            if shader_index < 0:
                shader_index = 0
            else:
                shader_index += 1
                if shader_index >= len(SHADERS_NAMES):
                    shader_index = 0
                    
            self.shader.create_pipeline(SHADERS_NAMES[shader_index])
            INPUTS["next_shader"] = False            
                    
        return events
                    
                    
    def reset_inputs(self):
        for key in ACTIONS.keys():
            INPUTS[key] = False
            
            
    #MARK: loop
    async def loop(self):
        self.shader.create_pipeline()
        
        if not IS_WEB:
            # encoder is determined by recording file extension (see save_recordings below)
            self.recorder = ScreenRecorder(RECORDING_FPS, compress=0)
            self.recordings_names = []
        
        try:
            while self.is_running:
                # delta time since last frame in milliseconds
                dt = self.clock.tick(FPS_CAP) / 1000
                events = []
                events = self.get_inputs()

                # first draw on separate Surface (game.canvas)
                if not self.is_paused:
                    self.time_elapsed += dt
                    self.states[-1].update(dt, events)
                self.canvas.fill((0,0,0,0))
                self.states[-1].draw(self.canvas, dt)
                self.custom_cursor(self.canvas)
                
                if self.is_paused:
                    self.render_text("PAUSED", (WIDTH*SCALE // 2, HEIGHT*SCALE // 2), font_size=FONT_SIZE_LARGE, centred=True, bg_color=(10,10,10,150))
                
                # than scale and copy on final Surface (game.screen)
                if SCALE != 1:
                    self.screen.blit(pygame.transform.scale_by(self.canvas, SCALE), (0,0))
                else:
                    self.screen.blit(self.canvas, (0,0))
                # shaders are used for postprocessing special effects
                # the whole Surface is used as texture on rect that fills to a full screen
                
                self.shader.render(self.screen, dt, USE_SHADERS)
                    
                pygame.display.flip()
                await asyncio.sleep(0)
        finally:
            
            if not IS_WEB:
                # first stop if there is ongoing recording
                if self.recorder.running_thread is not None:
                    self.recorder.stop_rec()
                
                if len(self.recorder.recordings) > 0:
                    print("saving recordings - this can take a while...")
                    self.render_text("SAVING...", (WIDTH*SCALE // 2, HEIGHT*SCALE // 2), font_size=FONT_SIZE_LARGE, centred=True, bg_color=(10,10,10,150), surface=self.screen)
                    self.shader.render(self.screen, dt, False)
                    pygame.display.flip()
                # save only the last recording
                # self.recorder.save_recording(SCREENSHOTS_DIR / "intro.mp4")
                
                # save all recordings in provided folder
                # mp4 extension defaults to h264/AVC1
                self.recorder.save_recordings(self.recordings_names, SCREENSHOTS_DIR)
                # save all recordings with default file naming (recording_{N}.mp4)
                # self.recorder.save_recordings("mp4", SCREENSHOTS_DIR)
            pygame.quit()
        