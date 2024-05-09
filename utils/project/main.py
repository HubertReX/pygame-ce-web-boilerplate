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
from pathlib import Path
import pygame
from opengl_shader import OpenGL_shader

# pygame.init()
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

screen = pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF)

async def main():
    timestamp = 0.0
    size = pygame.display.get_window_size()
    shader = OpenGL_shader(size, Path("fs.glsl"), Path("vs.glsl"))
    while True:
        timestamp += 1000.0 / 60.0
        screen.fill("black")
        pygame.draw.circle(screen, "red", (200,200), 100 + (math.sin(timestamp / 1000) * 100 ))
        
        shader.render(screen, timestamp)
        await asyncio.sleep(0)

def main_std():
    timestamp = 0.0
    size = pygame.display.get_window_size()
    shader = OpenGL_shader(size, Path("fs.glsl"), Path("vs.glsl"))
    while True:
        timestamp += 1000.0 / 60.0
        shader.render(screen, timestamp)


asyncio.run(main())
# main_std()
