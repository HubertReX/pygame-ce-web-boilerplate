

# /// pyproject
# [project]
# name = "zengl-test"
# version = "2023"
# description = "embed pygame in Panda3D webgl surface"
# readme = {file = "README.txt", content-type = "text/markdown"}
# requires-python = ">=3.11"
#
# dependencies = [
#  "pygame-ce",
#  "zengl",
# ]
# ///

# from: https://github.com/pygame-web/showroom/blob/main/src/test_zengl_debug.py

import asyncio
import math
import struct

import pygame
import zengl

# pygame.init()
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

screen = pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF)
zengl.init()

ctx = zengl.context()

"""
def compile_error(shader: bytes, shader_type: int, log: bytes):
    name = {0x8B31: "Vertex Shader", 0x8B30: "Fragment Shader"}[shader_type]
    log = log.rstrip(b"\x00").decode()
    raise ValueError(f"{name} Error\n\n{log}")

"""

import _zengl

# def CSI(param):
#     pass

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

_zengl.compile_error = compile_error_debug


size = pygame.display.get_window_size()

image = ctx.image(size, "rgba8unorm") #, samples=4)
depth = ctx.image(size, "depth24plus") #, samples=4)
output = ctx.image(size, "rgba8unorm")

#version 330 core
FS="""
        #version 300 es
        precision highp float;

        in vec3 v_vertex;
        in vec3 v_color;

        layout (location = 0) out vec4 out_color;

        void main() {
            float u = smoothstep(0.48, 0.47, abs(v_vertex.x - 0.5));
            float v = smoothstep(0.48, 0.47, abs(v_vertex.y - 0.5));
            out_color = vec4(v_color * (u * v), 1.0);
            out_color.rgb = pow(out_color.rgb, vec3(1.0 / 2.2));
        }
"""

VS="""
        #version 300 es
        precision highp float;

        mat4 perspective(float fovy, float aspect, float znear, float zfar) {
            float tan_half_fovy = tan(fovy * 0.008726646259971647884618453842);
            return mat4(
                1.0 / (aspect * tan_half_fovy), 0.0, 0.0, 0.0,
                0.0, 1.0 / (tan_half_fovy), 0.0, 0.0,
                0.0, 0.0, -(zfar + znear) / (zfar - znear), -1.0,
                0.0, 0.0, -(2.0 * zfar * znear) / (zfar - znear), 0.0
            );
        }

        mat4 lookat(vec3 eye, vec3 center, vec3 up) {
            vec3 f = normalize(center - eye);
            vec3 s = normalize(cross(f, up));
            vec3 u = cross(s, f);
            return mat4(
                s.x, u.x, -f.x, 0.0,
                s.y, u.y, -f.y, 0.0,
                s.z, u.z, -f.z, 0.0,
                -dot(s, eye), -dot(u, eye), dot(f, eye), 1.0
            );
        }

        const float PI = 3.1415926535897932384626;

        vec3 positions[4] = vec3[](
            vec3(0.0, 0.0, 0.5),
            vec3(0.0, 1.0, -0.5),
            vec3(1.0, 0.0, 0.5),
            vec3(1.0, 1.0, -0.5)
        );

        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }

        uniform float time;
        uniform float aspect;

        out vec3 v_vertex;
        out vec3 v_color;

        void main() {
            mat4 projection = perspective(45.0, aspect, 0.1, 1000.0);
            mat4 view = lookat(vec3(0.0, 4.0, 0.0), vec3(0.0, 0.0, 0.0), vec3(0.0, 0.0, 1.0));
            mat4 mvp = projection * view;

            v_vertex = positions[gl_VertexID];

            float r = time * 0.5 + PI - float(gl_InstanceID) * PI * 2.0 / 7.0;
            mat3 rotation = mat3(cos(r), 0.0, sin(r), 0.0, 1.0, 0.0, -sin(r), 0.0, cos(r));

            gl_Position = mvp * vec4(rotation * v_vertex, 1.0);
            v_color = hsv2rgb(vec3(float(gl_InstanceID) / 10.0, 1.0, 0.5));
        }
"""

pipeline = ctx.pipeline(
    vertex_shader=VS,
    fragment_shader=FS,
    uniforms={
        "aspect": size[0] / size[1],
        "time": 0.0,
    },
    framebuffer=[image, depth],
    topology="triangle_strip",
    vertex_count=4,
    instance_count=7,
)


def render(timestamp=0.0):
    ctx.new_frame()
    image.clear()
    depth.clear()
    screen.fill("black")
    pygame.draw.circle(screen, "red", (200,200), 100 + (math.sin(timestamp / 1000) * 100 ))
    image.write(pygame.image.tobytes(screen, 'RGBA', flipped=True))
    pipeline.uniforms["time"][:] = struct.pack("f", timestamp / 1000.0)
    pipeline.render()
    image.blit(output)
    output.blit()
    ctx.end_frame()


async def main():
    timestamp = 0.0
    while True:
        timestamp += 1000.0 / 60.0
        render(timestamp)
        await asyncio.sleep(0)

def main_std():
    timestamp = 0.0
    while True:
        timestamp += 1000.0 / 60.0
        render(timestamp)


asyncio.run(main())
# main_std()
