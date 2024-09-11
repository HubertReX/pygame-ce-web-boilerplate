import struct
from pathlib import Path
from typing import Any, Iterable

import zengl_extras
import pygame
import zengl
from settings import COMMON_SHADERS_DIR, IS_WEB, MAX_LIGHTS_COUNT, SHADERS_DIR, vec, vec3

if IS_WEB:
    zengl.init()
else:
    zengl_extras.init()


try:
    CSI("test")  # type: ignore[used-before-def]  # noqa: F821
except NameError:
    def CSI(param: Any) -> None:
        pass

#######################################################################################################################


class OpenGL_shader():
    def __init__(self, size: tuple[int, int], shader_name: str = "") -> None:

        def compile_error_debug(shader: str, shader_type: int, log: str) -> None:
            name = {0x8B31: "Vertex Shader", 0x8B30: "Fragment Shader"}[shader_type]
            print("=" * 30, name, "=" * 30)
            try:

                log = log.rstrip(b"\x00").decode(errors="ignore")  # type: ignore[attr-defined, arg-type]
                shader = shader.rstrip(b"\x00").decode()  # type: ignore[attr-defined, arg-type]
                _, pos, msg  = log.split(": ", 2)
                c, error_line_no = map(int, pos.split(":", 1))
                # print( l,c,msg  )
                spacer = ""  # "#" * 50
                for ln, line in enumerate(shader.split("\n")):
                    if ln == error_line_no:
                        CSI("1;93m")
                    print(f"{str(ln).zfill(3)}: {line.rstrip()}", end="")
                    if ln == error_line_no:
                        CSI("1;97m")
                        CSI("1;91m")
                        print(f" // {msg}", end=spacer)
                        CSI("1;97m")
                        CSI("1;0m")
                    print()
                raise ValueError(f"{name} Error\n\n{log}")

            finally:
                print("=" * 70)

        self.ctx = zengl.context()
        self.timestamp: float = 0.0
        self.size = size

        zengl_extras.compile_error = compile_error_debug

        self.image = self.ctx.image(size, "rgba8unorm")  # , samples=4)
        self.HUD = self.ctx.image(size, "rgba8unorm")  # , samples=4)
        # self.depth = self.ctx.image(size, "depth24plus") # , samples=4)

        float_size = 16
        floats_per_light = 3  # x, y, size
        self.lights_pos_buffer = self.ctx.buffer(size=float_size * floats_per_light * MAX_LIGHTS_COUNT)

        self.shader_name = shader_name
        self.pipeline: zengl.Pipeline = self.create_pipeline()

    ###################################################################################################################
    def create_pipeline(self, shader_name: str = "") -> zengl.Pipeline:
        # if provided new shader_name then use it (otherwise use shader_name provided in constructor)
        if shader_name:
            self.shader_name = shader_name

        fs_file = self.get_shader_file_name("fs")
        vs_file = self.get_shader_file_name("vs")

        FS = self.read_shader_from_file(fs_file)
        VS = self.read_shader_from_file(vs_file)

        common_file = COMMON_SHADERS_DIR / "common.glsl"
        common = self.read_shader_from_file(common_file)
        common = common.format(width = self.size[0], height = self.size[1], MAX_LIGHTS_COUNT = MAX_LIGHTS_COUNT)

        rgb2hsv_file = COMMON_SHADERS_DIR / "RGB2HSV.glsl"
        RGB2HSV = self.read_shader_from_file(rgb2hsv_file)

        includes = {
            "common": common,
            "RGB2HSV": RGB2HSV,
        }

        layout: Iterable[zengl.LayoutBinding] = [
            {
                "name": "Texture",
                "binding": 0,
            },
            {
                "name": "LightPositions",
                "binding": 1,
            },
            {
                "name": "HUD",
                "binding": 2,
            },
        ]

        uniforms: dict[str, Any] = {
            "time": 0.0,
            "scale": 0.0,
            "ratio": 0.0,
            "lights_cnt": 0,
        }

        resources: Iterable[zengl.BufferResource | zengl.SamplerResource] = [
            {
                "type": "sampler",
                "binding": 0,
                "image": self.image,
                "min_filter": "nearest",
                "mag_filter": "nearest",
                "wrap_x": "clamp_to_edge",
                "wrap_y": "clamp_to_edge",
            },
            {
                "type": "uniform_buffer",
                "binding": 1,
                "buffer": self.lights_pos_buffer,
            },
            {
                "type": "sampler",
                "binding": 2,
                "image": self.HUD,
                "min_filter": "nearest",
                "mag_filter": "nearest",
                "wrap_x": "clamp_to_edge",
                "wrap_y": "clamp_to_edge",
            },
        ]

        # depth = {
        #     "test": True,
        #     "write": False,
        #     "func": "greater",
        # },

        # blend = {
        #     "enable": True,
        #     "src_color": "src_alpha",
        #     "dst_color": "one_minus_src_alpha",
        # }

        return self.ctx.pipeline(
            vertex_shader = VS,
            fragment_shader = FS,
            includes=includes,
            layout = layout,
            resources = resources,
            uniforms = uniforms,
            # framebuffer = [self.image, self.depth],
            # framebuffer = [self.image],
            framebuffer = (None if IS_WEB else [self.image, self.HUD]),
            # blend = blend,
            # depth = depth,
            # cull_face="back",
            viewport = (0, 0, self.size[0], self.size[1]),
            topology = "triangle_strip",
            vertex_count = 4,
            # instance_count = 7,
        )

    ###################################################################################################################
    def get_shader_file_name(self, prefix: str) -> Path:
        # try to get shader program specific for particular effect (shader_name)
        f_name = SHADERS_DIR / f"{prefix}_{self.shader_name}.glsl"
        # if there is no specific shader program, use default
        if not f_name.exists():
            f_name = SHADERS_DIR / f"{prefix}.glsl"

        return f_name

    ###################################################################################################################
    def read_shader_from_file(self, file_name: Path) -> str:
        with open(file_name, encoding="UTF-8") as f:
            shader = "".join(f.readlines())

        return shader

    ###################################################################################################################
    def render(
        self,
        surface: pygame.Surface,
        HUD: pygame.Surface,
        lights_pos: list[vec3],
        scale: float,
        ratio: float,
        dt: float = 0.0,
        use_shaders: bool = True,
        save_frame: bool = False
    ) -> bytes | None:
        """
        Add postprocessing effects to the surface using shaders with lighting.

        Args:
            surface (pygame.Surface): The surface to be saned to `OpenGL` as texture.
            lights_pos (list[vec3]): A list of light positions `(x, y)` and radius `(z)`.
            scale (float): The scale factor of the camera (`zoom`).
            ratio (float): The day/night ration (`0.0` ==> `day`, `1.0` ==> `night`).
            dt (float, optional): The time delta since last frame. Defaults to `0.0`.
            use_shaders (bool, optional): Whether to use shaders or not. Defaults to `True`.
            save_frame (bool, optional): Whether to return the rendered image. Defaults to `False`.

        """
        self.ctx.new_frame()
        self.image.clear()
        self.image.write(pygame.image.tobytes(surface, "RGBA", flipped=True))
        self.HUD.clear()
        self.HUD.write(pygame.image.tobytes(HUD, "RGBA", flipped=True))
        # Fatal Python error: none_dealloc: deallocating None: bug likely caused by a refcount error in a C extension
        # Python runtime state: initialized

        # Current thread 0x00000001e9c18c00 (most recent call first):
        #   File "/Users/hubertnafalski/Documents/Projects/pygame-ce-web-boilerplate/project/opengl_shader.py",
        # line 172 in render
        # self.lights_pos_buffer.write(data, offset= (i * 16))
        self.timestamp += dt
        res = None

        if use_shaders:
            for i, p in enumerate(lights_pos):
                data = struct.pack("3f4x", p.x, p.y, p.z)
                self.lights_pos_buffer.write(data, offset= (i * 16))
            if self.pipeline.uniforms:
                self.pipeline.uniforms["time"][:] = struct.pack("f", self.timestamp / 100.0)
                self.pipeline.uniforms["scale"][:] = struct.pack("f", scale)
                self.pipeline.uniforms["ratio"][:] = struct.pack("f", ratio)
                self.pipeline.uniforms["lights_cnt"][:] = struct.pack("i", len(lights_pos))
            self.pipeline.render()
            # desktop rendering requires different handling in order to
            # record screen processed by shaders
            if not IS_WEB:
                # since we use framebuffer we need to blit
                self.image.blit()

                # return back image as bytes
                # useful only for screenshots and gameplay recording
                # otherwise saved screen doesn't reflect shaders effect
                if save_frame:
                    res = self.image.read()
        else:
            self.image.blit()
        self.ctx.end_frame()

        return res
