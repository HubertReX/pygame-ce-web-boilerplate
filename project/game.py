from __future__ import annotations

import asyncio
import os
import random
from datetime import datetime
from os import environ
from typing import TYPE_CHECKING, Any, Callable, cast

import pygame
from opengl_shader import OpenGL_shader
from PIL import Image
from rich import print, traceback
from settings import (
    ACTIONS,
    BG_COLOR,
    CONFIG_FILE,
    CUTSCENE_BG_COLOR,
    DEFAULT_SHADER,
    FONT_COLOR,
    FONT_SIZE_DEFAULT,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    FONT_SIZE_TINY,
    FPS_CAP,
    GAME_NAME,
    GAMEPAD_WEB_CONTROL_NAMES,
    GAMEPAD_XBOX_AXIS2ACTIONS,
    GAMEPAD_XBOX_BUTTON2ACTIONS,
    GAMEPAD_XBOX_CONTROL_NAMES,
    HEIGHT,
    INPUTS,
    IS_FULLSCREEN,
    IS_WEB,
    JOY_COOLDOWN,
    JOY_DRIFT,
    JOY_MOVE_MULTIPLIER,
    MAIN_FONT,
    MOUSE_CURSOR_IMG,
    PANEL_BG_COLOR,
    PROGRAM_ICON,
    RECORDING_FPS,
    SCALE,
    SCREENSHOTS_DIR,
    SHADERS_NAMES,
    TEXT_ROW_SPACING,
    TILE_SIZE,
    USE_CUSTOM_MOUSE_CURSOR,
    USE_SHADERS,
    USE_SOD,
    WIDTH,
    # ColorValue,
    vec,
    vec3
)

if IS_WEB:
    from config_model.config import load_config
else:
    import ffmpeg
    from config_model.config_pydantic import load_config  # type: ignore[assignment]

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
# https://www.reddit.com/r/pygame/comments/12twl0e/cannot_rumble_dualshock_4_via_bluetooth_in_pygame/
environ["SDL_JOYSTICK_HIDAPI_PS4_RUMBLE"] = "1"

if USE_SOD:
    from second_order_dynamics import SecondOrderDynamics

# 101 0017 # 106 0021 # 107 0030 no left down
seed = 107
random.seed(seed)
# np.random.seed(seed)
traceback.install(show_locals=True, width=150)

# os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"

#################################################################################################################


class Game:
    # MARK: Game
    def __init__(self) -> None:
        self.conf = load_config(CONFIG_FILE)
        pygame.init()

        # initialise the joystick module
        pygame.joystick.init()

        # create empty list to store joysticks
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self.is_joystick_in_use: bool = False
        self.joy_actions_cooldown: dict[str, float] = {}

        self.clock: pygame.time.Clock = pygame.time.Clock()
        # time elapsed in seconds (milliseconds as fraction) without pause time
        self.time_elapsed: float = 0.0

        pygame.display.set_caption(GAME_NAME)
        program_icon = pygame.image.load(PROGRAM_ICON)
        pygame.display.set_icon(program_icon)

        # https://coderslegacy.com/python/pygame-rpg-improving-performance/
        self.flags: int = 0

        if IS_FULLSCREEN:
            self.flags |= pygame.FULLSCREEN

        if IS_WEB:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 0)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_ES)
        else:
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
        # pygame.RESIZABLE , | pygame.SCALED
        self.flags = self.flags | pygame.OPENGL | pygame.DOUBLEBUF
        self.screen: pygame.Surface = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE), self.flags, vsync=1)

        # , 32 .convert_alpha() # pygame.SRCALPHA
        self.canvas: pygame.Surface = pygame.Surface((WIDTH, HEIGHT), self.flags)

        size = self.screen.get_size()
        self.shader = OpenGL_shader(size, DEFAULT_SHADER)
        self.save_frame: bool = False

        self.fonts: dict[int, pygame.font.Font] = {}
        font_sizes = [FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE]
        for font_size in font_sizes:
            self.fonts[font_size] = pygame.font.Font(MAIN_FONT, font_size)

        self.font = self.fonts[FONT_SIZE_DEFAULT]
        self.is_running = True
        self.is_paused = False

        self.shader.create_pipeline()
        # self.loading_screen()

        # stacked game states (e.g. Scene, Menu)
        if TYPE_CHECKING:
            from state import State
        self.states: list[State] = []
        # dict of custom events with callable functions
        # (not used for now since pygame.time.set_timer is not implemented in pygbag)
        self.custom_events: dict[int, Callable] = {}
        # moved imports here to avoid circular imports
        # import menus
        # start_state = menus.MainMenuScreen(self, "MainMenu")
        # self.states.append(start_state)
        import scene
        start_state = scene.Scene(self, "Village", "start")
        # start_state = scene.Scene(self, "Maze", "start", is_maze=True, maze_cols=10, maze_rows=5)
        start_state.enter_state()
        # self.states.append(start_state)
        # self.states.append(start_state)

        if USE_CUSTOM_MOUSE_CURSOR:
            cursor_img = pygame.image.load(MOUSE_CURSOR_IMG)
            scale = cursor_img.get_width() // TILE_SIZE
            self.cursor_img = pygame.transform.scale(cursor_img, (scale, scale)).convert_alpha()
            # self.cursor_img = pygame.transform.invert(self.cursor_img)
            self.cursor_img.set_alpha(150)
            pygame.mouse.set_visible(False)
        if USE_SOD:
            self.init_SOD()

    #############################################################################################################
    def show_loading_screen(self) -> None:
        self.screen.fill(BG_COLOR)
        self.render_text(
            "Loading...",
            (WIDTH * SCALE // 2, HEIGHT * SCALE // 2),
            font_size=FONT_SIZE_LARGE,
            centred=True,
            bg_color=PANEL_BG_COLOR,
            surface=self.screen
        )
        self.shader.render(self.screen, [], 1.0, -1.0, 0.01, True)
        pygame.display.flip()

    #############################################################################################################
    def init_SOD(self) -> None:
        # frequency, reaction speed and oscillation
        f = 0.01
        # zeta, damping factor
        z = 0.3
        # response, immediate, overshoot, anticipation
        r = -3.0
        self.sod_time = 0.01
        cursor_rect = self.cursor_img.get_frect(center=pygame.mouse.get_pos())
        pos = vec(cursor_rect.center)

        self.SOD = SecondOrderDynamics(f, z, r, x0=pos)

    #############################################################################################################
    def render_panel(
        self,
        rect: pygame.Rect,
        color: pygame._common.ColorValue,
        surface: pygame.Surface | None = None
    ) -> None:
        # MARK: render
        """
        Renders semitransparent (if `alpha` provided) rect using provided color on `game.canvas`

        Args:
            rect (pygame.Rect): Size and position of panel
            color (ColorValue): color to fill in the panel (with alpha)
            surface (pygame.Surface): surface to blit on. Defaults to None
        """
        if not surface:
            surface = self.canvas

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, color, surf.get_rect())
        surface.blit(surf, rect)

    #############################################################################################################
    def render_texts(
            self,
            texts:     list[str],
            pos:       tuple[int, int],
            color:     pygame._common.ColorValue = FONT_COLOR,
            bg_color:  pygame._common.ColorValue = 0,
            shadow:    pygame._common.ColorValue = CUTSCENE_BG_COLOR,
            font_size: int = 0,
            centred:   bool = False,
            surface:   pygame.Surface | None = None
    ) -> None:
        """
        Blit several lines of text on surface or on `game.canvas` if surface is not provided, one under other,

        Args:
            texts (list[str]): list of strings to render
            pos (tuple[int, int]): position of first row
            color (ColorValue, optional): text color. Defaults to `FONT_COLOR`.
            bg_color (ColorValue, optional): draw background panel. Defaults to `0` == no bg.
            shadow (ColorValue, optional): draw outline of text with black color. Defaults to `CUTSCENE_BG_COLOR`.
            font_size (int, optional): font size from `FONT_SIZES_DICT` list. Defaults to `0` == `FONT_SIZE_DEFAULT`
            centred (bool, optional): shell the text be centered at `pos`. Defaults to `False`.
            surface (pygame.Surface, optional): surface to blit on, if `None` user `game.canvas`. Defaults to `None`.
        """

        for line_no, text in enumerate(texts):
            if font_size == 0:
                font_size = FONT_SIZE_SMALL
            new_pos = (pos[0], pos[1] + int(line_no * font_size * TEXT_ROW_SPACING))
            self.render_text(text, new_pos, color, bg_color, shadow, font_size, centred, surface)

    #############################################################################################################
    def render_text(
            self,
            text:      str,
            pos:       tuple[int, int],
            color:     pygame._common.ColorValue = FONT_COLOR,
            bg_color:  pygame._common.ColorValue = 0,
            shadow:    pygame._common.ColorValue = CUTSCENE_BG_COLOR,
            font_size: int = 0,
            centred:   bool = False,
            surface:   pygame.Surface | None = None
    ) -> None:
        """
        Blit line of text on `surface` or on `game.canvas` if `surface` is not provided

        Args:
            text (str): _description_
            pos (tuple[int, int]): _description_
            color (ColorValue, optional): _description_. Defaults to `FONT_COLOR`.
            bg_color (ColorValue, optional): _description_. Defaults to `0` == no bg.
            shadow (ColorValue, optional): _description_. Defaults to `CUTSCENE_BG_COLOR`.
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
        rect: pygame.Rect = surf.get_rect(center=pos) if centred else surf.get_rect(topleft=pos)

        # alpha blend semitransparent rect in background 8 pixels bigger than rect
        # works well for single line of text
        if bg_color:
            bg_rect: pygame.Rect = rect.copy().inflate(18, 18).move(-4, -4)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, bg_color, bg_surf.get_rect())
            surface.blit(bg_surf, bg_rect)

        # add black outline (render black text moved by offset to all 4 directions)
        if shadow:
            surf_shadow: pygame.surface.Surface = selected_font.render(text, False, shadow)
            offset = 1
            surface.blit(surf_shadow, (rect.x - offset, rect.y))
            surface.blit(surf_shadow, (rect.x + offset, rect.y))
            surface.blit(surf_shadow, (rect.x,          rect.y - offset))
            surface.blit(surf_shadow, (rect.x,          rect.y + offset))

        surface.blit(surf, rect)

    #############################################################################################################
    def custom_cursor(self, screen: pygame.Surface) -> None:
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

    #############################################################################################################
    def get_images(self, path: str) -> list[pygame.Surface]:
        """
        Gets a list of images from the specified path.

        Args:
            path (str): The directory path to load the images from.
            *: Additional keyword arguments, currently ignored.

        Returns:
            list[pygame.Surface]: A list of pygame.Surface objects representing the loaded images.
        """
        images = []
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            # img = pygame.image.load(full_path).convert_alpha()
            img = pygame.image.load(full_path)
            images.append(img)

        return images

    #############################################################################################################
    def get_animations(self, path: str) -> dict[str, list[pygame.Surface]]:
        """
        read sprite animations from given folder

        :param path: folder containing folders with animations names that contain frames as separate files
        :type path: str
        :return: dictionary with animation name (subfolder) as keys and empty list as value
        """
        animations: dict[str, list[pygame.Surface]] = {}
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path, file)):
                animations |= {file: []}
        return animations

    #############################################################################################################
    def save_screenshot(self, data: bytes | None = None) -> bool:
        """
        save current screen to SCREENSHOT_FOLDER as PNG with timestamp in name
        """
        if self.save_frame:
            # in previous loop, frame was saved back to screen
            # so now we can store it and disable frame saving
            self.save_frame = False
            INPUTS["screenshot"] = False

            time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = SCREENSHOTS_DIR / f"screenshot_{time_str}.png"
            # pygame.image.save(self.screen, file_name)
            Image.frombuffer("RGBA", (WIDTH, HEIGHT), data, "raw", "RGBA", 0, -1).save(file_name)
            if IS_WEB:
                import platform
                platform.window.download_from_browser_fs(  # type: ignore[attr-defined]
                    file_name.as_posix(), "image/png")
            else:
                print(f"screenshot saved to file '{file_name}'")
            return True
        else:
            # next frame rendered by pipeline needs to be saved back to screen
            self.save_frame = True
            return False

    #############################################################################################################
    def register_custom_event(self, custom_event_id: int, handle_function: Callable) -> None:
        """
        Registers a custom event with a specific ID and associates it with a handler function.

        Args:
            custom_event_id (int): A unique integer identifier for the custom event.
            handle_function (callable): A function that will be called when the custom event is triggered.

        """

        self.custom_events[custom_event_id] = handle_function

    #############################################################################################################
    def get_inputs(self) -> list[pygame.event.EventType]:
        # MARK: get_inputs
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

            elif event.type in [
                    pygame.WINDOWSHOWN, pygame.WINDOWMAXIMIZED, pygame.WINDOWRESTORED, pygame.WINDOWFOCUSGAINED]:
                self.is_paused = False
                # print(f"{self.is_paused=}")
            elif event.type in self.custom_events:
                handler = self.custom_events[event.type]
                handler(**event.dict)
            elif event.type == pygame.KEYDOWN:
                self.is_joystick_in_use = False
                for action, definition in ACTIONS.items():
                    if event.key in definition["keys"]:
                        INPUTS[action] = True
            elif event.type == pygame.KEYUP:
                self.is_joystick_in_use = False
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

            elif event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                self.joysticks[joy.get_instance_id()] = joy
                self.is_joystick_in_use = True
            elif event.type == pygame.JOYDEVICEREMOVED:
                del self.joysticks[event.instance_id]
                self.is_joystick_in_use = False

        for joystick in self.joysticks.values():
            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    print(f"{i} pressed")
                    self.is_joystick_in_use = True
                    break
            else:
                for i in range(joystick.get_numaxes()):
                    if joystick.get_axis(i) > JOY_DRIFT:
                        self.is_joystick_in_use = True
                        break
            break

        if self.is_joystick_in_use:
            for joystick in self.joysticks.values():
                if IS_WEB:
                    gamepad_controls = GAMEPAD_WEB_CONTROL_NAMES
                else:
                    gamepad_controls = GAMEPAD_XBOX_CONTROL_NAMES
                for button_name, action in GAMEPAD_XBOX_BUTTON2ACTIONS.items():
                    pressed = joystick.get_button(gamepad_controls["buttons"][button_name])
                    # if pressed:
                    #     print(f"{button_name} pressed")

                    if not pressed:
                        INPUTS[action] = pressed
                    elif self.time_elapsed - self.joy_actions_cooldown.get(action, 0.0) >= JOY_COOLDOWN:
                        self.joy_actions_cooldown[action] = self.time_elapsed
                        INPUTS[action] = pressed
                        # joystick.get_button(b2a["buttons"][button_name])

                for axis_name, actions in GAMEPAD_XBOX_AXIS2ACTIONS.items():
                    value = joystick.get_axis(gamepad_controls["axis"][axis_name])
                    if abs(value) > JOY_DRIFT:
                        if value > 0.0:
                            # e.g. left/up
                            INPUTS[actions[0]] = False
                            # eg. right/down
                            INPUTS[actions[1]] = True
                            INPUTS[f"{actions[1]}_value"] = abs(value)
                        else:
                            INPUTS[actions[0]] = True
                            INPUTS[f"{actions[0]}_value"] = abs(value)
                            INPUTS[actions[1]] = False

        global USE_SHADERS
        # global IS_PAUSED
        if INPUTS["pause"]:
            # IS_PAUSED = not IS_PAUSED
            self.is_paused = not self.is_paused
            print(f"{self.is_paused=}")
            INPUTS["pause"] = False

        if INPUTS["record"]:
            if not IS_WEB:
                if not self.save_frame:
                    self.start_recording()
                else:
                    self.save_recording()
            INPUTS["record"] = False

        if INPUTS["screenshot"]:
            INPUTS["screenshot"] = not self.save_screenshot()

        if INPUTS["run"]:
            for joystick in self.joysticks.values():
                joystick.rumble(1, 0, 450)
                joystick.rumble(0, 1, 250)

        # if INPUTS["shaders_toggle"]:
        #     USE_SHADERS = not USE_SHADERS
        #     INPUTS["shaders_toggle"] = False

        # if INPUTS["next_shader"]:
        #     shader_index = SHADERS_NAMES.index(self.shader.shader_name)
        #     if shader_index < 0:
        #         shader_index = 0
        #     else:
        #         shader_index += 1
        #         if shader_index >= len(SHADERS_NAMES):
        #             shader_index = 0

        #     self.shader.create_pipeline(SHADERS_NAMES[shader_index])
        #     INPUTS["next_shader"] = False

        return events

    #############################################################################################################
    def reset_inputs(self) -> None:
        for key in ACTIONS.keys():
            INPUTS[key] = False

    #############################################################################################################
    def save_recording(self) -> None:
        if not self.save_frame:
            return

        self.save_frame = False
        print("Recording stopped")
        self.rec_process.stdin.close()
        print("saving recordings - this can take a while...")
        self.render_text(
            "SAVING...",
            (WIDTH * SCALE // 2, HEIGHT * SCALE // 2),
            font_size=FONT_SIZE_LARGE,
            centred=True,
            bg_color=PANEL_BG_COLOR,
            surface=self.screen
        )

        positions = [vec3(0, 0, 0)]
        ratio: float = -1.0
        self.shader.render(self.screen, positions, 1.0, ratio, self.clock.tick(
            FPS_CAP) / 1000, USE_SHADERS, save_frame=self.save_frame)
        pygame.display.flip()
        self.rec_process.wait()

    #############################################################################################################
    def start_recording(self) -> None:
        self.save_frame = True

        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = SCREENSHOTS_DIR / f"recording_{time_str}.mp4"
        print(f"Recording started: {file_name}")

        self.rec_process = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="rgba",
                s=f"{WIDTH}x{HEIGHT}",
                r=FPS_CAP,
            )
            .vflip()
            .output(
                str(file_name), pix_fmt="rgb24", loglevel="quiet", r=RECORDING_FPS
            )
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

    #############################################################################################################
    def show_pause_message(self) -> None:
        self.render_text(
            "PAUSED",
            (WIDTH * SCALE // 2, HEIGHT * SCALE // 2),
            font_size=FONT_SIZE_LARGE,
            centred=True,
            bg_color=PANEL_BG_COLOR
        )

    #############################################################################################################
    def postprocessing(self, dt: float) -> None:
        # shaders are used for postprocessing special effects
        # the whole Surface is used as texture on rect that fills to a full screen
        ratio: float = 0.0
        if hasattr(self.states[-1], "player"):
            # if TYPE_CHECKING:
            from scene import Scene
            scene = cast(Scene, self.states[-1])
            # scene = self.states[-1]
            positions, ratio = scene.get_lights()
            scale = scene.camera.zoom
        else:
            positions = [vec3(0.0, 0.0, 0.0)]
            ratio = -1.0
            scale = 1.0

        res = self.shader.render(self.screen, positions, scale, ratio, dt, USE_SHADERS, save_frame=self.save_frame)

        if self.save_frame:
            if INPUTS["screenshot"]:
                self.save_screenshot(res)
            else:
                self.rec_process.stdin.write(res)
    #############################################################################################################

    async def loop(self) -> None:
        # MARK: loop
        self.fps: float = 0.0
        # self.avg_fps_3s: float = 0.0
        # self.avg_fps_10s: float = 0.0
        # self.fps_data_3s = deque([], 3 * FPS_CAP)
        # self.fps_data_10s = deque([], 10 * FPS_CAP)

        try:
            while self.is_running:
                # delta time since last frame in milliseconds
                dt = self.clock.tick(FPS_CAP) / 1000
                # slow down
                # dt *= 0.5
                self.fps = self.clock.get_fps()
                # self.fps_data_3s.append(self.fps)
                # self.fps_data_10s.append(self.fps)
                # self.avg_fps_3s = sum(self.fps_data_3s) / len(self.fps_data_3s)
                # self.avg_fps_10s = sum(self.fps_data_10s) / len(self.fps_data_10s)
                # events = []
                events = self.get_inputs()

                # first draw on separate Surface (game.canvas)
                if not self.is_paused:
                    self.time_elapsed += dt
                    self.states[-1].update(dt, events)
                self.canvas.fill(BG_COLOR)
                self.states[-1].draw(self.canvas, dt)
                self.custom_cursor(self.canvas)

                if self.is_paused:
                    self.show_pause_message()

                # than scale and copy on final Surface (game.screen)
                if SCALE != 1:
                    self.screen.blit(pygame.transform.scale_by(self.canvas, SCALE), (0, 0))
                else:
                    self.screen.blit(self.canvas, (0, 0))

                self.postprocessing(dt)

                pygame.display.flip()
                await asyncio.sleep(0)
        finally:
            self.save_recording()
            pygame.quit()
