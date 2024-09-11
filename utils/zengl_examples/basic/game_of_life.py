import os
import sys

import pygame
import zengl
import zengl_extras

zengl_extras.init()

pygame.init()
pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)

ctx = zengl.context()

size = pygame.display.get_window_size()
image = ctx.image(size, 'rgba8unorm')
temp = ctx.image(size, 'rgba8unorm')

pipeline = ctx.pipeline(
    vertex_shader='''
        #version 330 core

        vec2 positions[3] = vec2[](
            vec2(-1.0, -1.0),
            vec2(3.0, -1.0),
            vec2(-1.0, 3.0)
        );

        void main() {
            gl_Position = vec4(positions[gl_VertexID], 0.0, 1.0);
        }
    ''',
    fragment_shader='''
        #version 330 core

        uniform sampler2D Texture;
        uniform ivec2 Size;

        layout (location = 0) out vec4 out_color;

        int c(int x, int y) {
            ivec2 at = (ivec2(gl_FragCoord.xy) + ivec2(x, y) + Size) % Size;
            return texelFetch(Texture, at, 0).r < 0.5 ? 0 : 1;
        }

        void main() {
            float res;
            int neighbours = c(-1, -1) + c(-1, 0) + c(0, 1) + c(0, -1) + c(-1, 1) + c(1, -1) + c(1, 0) + c(1, 1);
            if (c(0, 0) == 1) {
                res = (neighbours == 2 || neighbours == 3) ? 1.0 : 0.0;
            } else {
                res = (neighbours == 3) ? 1.0 : 0.0;
            }
            out_color = vec4(res, res, res, 1.0);
        }
    ''',
    uniforms={
        'Size': size,
    },
    layout=[
        {
            'name': 'Texture',
            'binding': 0,
        },
    ],
    resources=[
        {
            'type': 'sampler',
            'binding': 0,
            'image': temp,
        },
    ],
    framebuffer=[image],
    topology='triangles',
    vertex_count=3,
)

image.write(os.urandom(size[0] * size[1] * 4))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    now = pygame.time.get_ticks() / 1000.0

    ctx.new_frame()
    image.blit(temp)
    pipeline.render()
    image.blit()
    ctx.end_frame()

    pygame.display.flip()
