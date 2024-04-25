#!../.venv/bin/python
# /// script
# [project]
# name = "The Game"
# version = "0.1"
# description = "Boilerplate pygame-ce project for a top-down tiles sheet based RPG game that can run in the browser."
# requires-python = ">=3.11"
#
# dependencies = [
#  "zengl",
# ]
# ///
import asyncio
import os
import random
import sys

#  "pygame-ce",
import pygame
import zengl

# os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

pygame.init()
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
# pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

pygame.display.set_mode((640, 480), flags=pygame.OPENGL) #  | pygame.DOUBLEBUF, vsync=True

ctx = zengl.context()

window_size = pygame.display.get_window_size()
image = ctx.image(window_size, 'rgba8unorm')
overlay = ctx.image(window_size, 'rgba8unorm')

        #version 330 core
pipeline = ctx.pipeline(
    vertex_shader='''
        #version 300 es

        vec2 vertices[3] = vec2[](
            vec2(-1.0, -1.0),
            vec2(3.0, -1.0),
            vec2(-1.0, 3.0)
        );

        out vec2 vertex;

        void main() {
            gl_Position = vec4(vertices[gl_VertexID], 0.0, 1.0);
            vertex = vertices[gl_VertexID];
        }
    ''',
    fragment_shader='''
        #version 300 es

        uniform sampler2D Layer1;
        uniform sampler2D Layer2;

        in vec2 vertex;

        layout (location = 0) out vec4 out_color;

        void main() {
            vec2 uv = vertex * 0.5 + 0.5;
            vec4 color1 = texture(Layer1, uv);
            vec4 color2 = texture(Layer2, uv);
            out_color = color1 * (1.0 - color2.a) + color2 * color2.a;
        }
    ''',
    layout=[
        {
            'name': 'Layer1',
            'binding': 0,
        },
        {
            'name': 'Layer2',
            'binding': 1,
        },
    ],
    resources=[
        {
            'type': 'sampler',
            'binding': 0,
            'image': image,
        },
        {
            'type': 'sampler',
            'binding': 1,
            'image': overlay,
        },
    ],
    framebuffer=None,
    viewport=(0, 0, *window_size),
    topology='triangles',
    vertex_count=3,
)


def make_square(size, color):
    surface = pygame.surface.Surface((size, size), pygame.SRCALPHA)
    surface.fill(color)
    return surface


squares = []
for _ in range(20):
    size = random.randint(20, 80)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    square = {
        'size': size,
        'position': (random.randint(0, window_size[0]), random.randint(0, window_size[1])),
        'rotation': random.randint(0, 360),
        'surface': make_square(size, color),
    }
    squares.append(square)

screen = pygame.surface.Surface(window_size).convert_alpha()

async def main(): # ctx, window_size, image, overlay, pipeline, squares, screen):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_q, pygame.K_ESCAPE]:
                    pygame.quit()
                    sys.exit()
                

        image.write(os.urandom(window_size[0] * window_size[1] * 4))

        screen.fill((0, 0, 0, 0))

        mouse = pygame.mouse.get_pos()
        for square in squares:
            square['rotation'] += 1
            if square['rotation'] > 360:
                square['rotation'] = 0
            square_surface = square['surface']
            if sum((a - b) ** 2.0 for a, b in zip(mouse, square['position'])) < square['size'] ** 2.0:
                square_surface = pygame.transform.scale(square_surface, (square['size'] + 10, square['size'] + 10))
            rotated_surface = pygame.transform.rotate(square_surface, square['rotation'])
            width, height = rotated_surface.get_size()
            position = (square['position'][0] - width // 2, square['position'][1] - height // 2)
            screen.blit(rotated_surface, position)

        ctx.new_frame()
        overlay.write(pygame.image.tobytes(screen, 'RGBA', flipped=True))

        pipeline.render()
        ctx.end_frame()

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
   