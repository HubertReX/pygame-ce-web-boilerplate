from pathlib import Path
import struct
import zengl
import pygame

from settings import SHADERS_DIR

zengl.init()

import _zengl


try: 
    CSI("test")
except:
    def CSI(param):
        pass


class OpenGL_shader():
    def __init__(self, size: tuple[int, int], shader_name: str = "") -> None:
        
        def compile_error_debug(shader: bytes, shader_type: int, log: bytes):
            name = {0x8B31: "Vertex Shader", 0x8B30: "Fragment Shader"}[shader_type]
            print("="*30,name,"="*30)
            try:

                log = log.rstrip(b"\x00").decode()
                shader = shader.rstrip(b"\x00").decode()
                _, pos, msg  = log.split(": ",2)
                c,l = map( int, pos.split(":",1) )
                #print( l,c,msg  )
                spacer = ""
                for ln,line in enumerate(shader.split("\n")):
                    if ln==l:
                        CSI("1;93m")
                    print(f"{str(ln).zfill(3)}: {line.rstrip()}", end="")
                    if ln==l:
                        CSI("1;97m")
                        CSI("1;91m")
                        print(f" // {msg}", end=spacer)
                        CSI("1;97m")
                        CSI("1;0m")
                    print()
                raise ValueError(f"{name} Error\n\n{log}")

            finally:
                print("="*70)

        self.ctx = zengl.context()
        self.timestamp: float = 0.0
        self.size = size

        _zengl.compile_error = compile_error_debug

        self.image = self.ctx.image(size, "rgba8unorm") #, samples=4)
        self.shader_name = shader_name
        self.pipeline = None

    def create_pipeline(self, shader_name: str = ""):
        # if provided new shader_name then use it (otherwise use shader_name provided in constructor)
        if shader_name:
            self.shader_name = shader_name
        
        fs_file = self.get_shader_file_name("fs")
        vs_file = self.get_shader_file_name("vs")

        FS = self.read_shader_from_file(fs_file)
        VS = self.read_shader_from_file(vs_file)
        
        layout =[
            {
                    "name": "Texture",
                    "binding": 0,
            },
        ]
        
        uniforms = {
                "time": 0.0,
                "screen_size": (self.size[0], self.size[1]),
        }
        
        resources = [
                {
                    "type": "sampler",
                    "binding": 0,
                    "image": self.image,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                    "wrap_x": "clamp_to_edge",
                    "wrap_y": "clamp_to_edge",
                },
        ]
        
        self.pipeline = self.ctx.pipeline(
            vertex_shader = VS,
            fragment_shader = FS,
            layout = layout,
            resources = resources,
            uniforms = uniforms,
            framebuffer = None,
            viewport = (0, 0, self.size[0], self.size[1]),
            topology = "triangle_strip",
            vertex_count = 4,
            # instance_count = 7,
        )
        
    def get_shader_file_name(self, prefix: str) -> Path:
        # try to get shader program specific for particular effect (shader_name)
        f_name = SHADERS_DIR / f"{prefix}_{self.shader_name}.glsl"
        # if there is no specific shader program, use default
        if not f_name.exists():
            f_name = SHADERS_DIR / f"{prefix}.glsl"
        
        return f_name
        
    def read_shader_from_file(self, file_name: Path):
        with open(file_name, encoding="UTF-8") as f:
            shader = "".join(f.readlines())
            
        return shader


    def render(self, surface, dt: float = 0.0, use_shaders: bool = True):
        self.ctx.new_frame()
        self.image.clear()
        self.image.write(pygame.image.tobytes(surface, "RGBA", flipped=True))
        self.timestamp += dt
        self.pipeline.uniforms["time"][:] = struct.pack("f", self.timestamp / 100.0)
        if use_shaders:
            self.pipeline.render()
        else:
            self.image.blit()
        self.ctx.end_frame()

