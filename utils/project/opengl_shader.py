from pathlib import Path
import struct
import zengl
import pygame
zengl.init()

import _zengl


"""
def compile_error(shader: bytes, shader_type: int, log: bytes):
    name = {0x8B31: "Vertex Shader", 0x8B30: "Fragment Shader"}[shader_type]
    log = log.rstrip(b"\x00").decode()
    raise ValueError(f"{name} Error\n\n{log}")

"""

try: 
    CSI("test")
except:
    def CSI(param):
        pass

class OpenGL_shader():
    def __init__(self, size: tuple[int, int], fragment_shader_file: Path, vertex_shader_file: Path) -> None:
        
        def compile_error_debug(shader: bytes, shader_type: int, log: bytes):
            name = {0x8B31: "Vertex Shader", 0x8B30: "Fragment Shader"}[shader_type]
            print("="*30,name,"="*30)
            try:

                log = log.rstrip(b"\x00").decode()
                _, pos, msg  = log.split(': ',2)
                c,l = map( int, pos.split(':',1) )
                #print( l,c,msg  )
                spacer = ""
                for ln,line in enumerate(VS.split("\n")):
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

        _zengl.compile_error = compile_error_debug

        self.image = self.ctx.image(size, "rgba8unorm") #, samples=4)
        self.depth = self.ctx.image(size, "depth24plus") #, samples=4)
        self.output = self.ctx.image(size, "rgba8unorm")


        FS = self.read_shader_from_file(fragment_shader_file)
        VS = self.read_shader_from_file(vertex_shader_file)


        self.pipeline = self.ctx.pipeline(
            vertex_shader = VS,
            fragment_shader = FS,
            uniforms={
                "aspect": size[0] / size[1],
                "time": 0.0,
            },
            framebuffer = [self.image, self.depth],
            topology = "triangle_strip",
            vertex_count = 4,
            instance_count = 7,
        )

    def read_shader_from_file(self, file_name: Path):
        with open(file_name, encoding="UTF-8") as f:
            shader = "\n".join(f.readlines())
            
        return shader

    def render(self, surface, dt: float = 0.0):
        self.ctx.new_frame()
        self.image.clear()
        self.depth.clear()
        self.image.write(pygame.image.tobytes(surface, 'RGBA', flipped=True))
        self.timestamp += dt
        self.pipeline.uniforms["time"][:] = struct.pack("f", self.timestamp / 10.0)
        self.pipeline.render()
        self.image.blit(self.output)
        self.output.blit()
        self.ctx.end_frame()

