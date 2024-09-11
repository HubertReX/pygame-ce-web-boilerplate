import struct
import sys

import pygame
import zengl
import zengl_extras

zengl_extras.init()

pygame.init()
pygame.display.set_mode((720, 720), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)

ctx = zengl.context()

size = pygame.display.get_window_size()
image = ctx.image(size, 'rgba8unorm', samples=4)
depth = ctx.image(size, 'depth24plus', samples=4)
uniform_buffer = ctx.buffer(size=80, uniform=True)

pipeline = ctx.pipeline(
    vertex_shader='''
        #version 330 core

        layout (std140) uniform Common {
            mat4 camera_matrix;
            vec4 camera_position;
        };

        vec3 vertices[26] = vec3[](
            vec3(0.000000, 0.707107, 0.707107),
            vec3(0.000000, 1.000000, -0.000000),
            vec3(0.000000, 0.707107, -0.707107),
            vec3(0.500000, 0.500000, 0.707107),
            vec3(0.707107, 0.707107, -0.000000),
            vec3(0.500000, 0.500000, -0.707107),
            vec3(0.707107, -0.000000, 0.707107),
            vec3(1.000000, -0.000000, -0.000000),
            vec3(0.707107, -0.000000, -0.707107),
            vec3(0.500000, -0.500000, 0.707107),
            vec3(0.707107, -0.707107, -0.000000),
            vec3(0.500000, -0.500000, -0.707107),
            vec3(0.000000, -0.000000, -1.000000),
            vec3(0.000000, -0.707107, 0.707107),
            vec3(0.000000, -1.000000, -0.000000),
            vec3(0.000000, -0.707107, -0.707107),
            vec3(-0.000000, -0.000000, 1.000000),
            vec3(-0.500000, -0.500000, 0.707107),
            vec3(-0.707107, -0.707107, -0.000000),
            vec3(-0.500000, -0.500000, -0.707107),
            vec3(-0.707107, -0.000000, 0.707107),
            vec3(-1.000000, -0.000000, -0.000000),
            vec3(-0.707107, -0.000000, -0.707107),
            vec3(-0.500000, 0.500000, 0.707107),
            vec3(-0.707107, 0.707107, -0.000000),
            vec3(-0.500000, 0.500000, -0.707107)
        );

        vec2 texcoords[43] = vec2[](
            vec2(0.750000, 0.750000),
            vec2(0.750000, 0.500000),
            vec2(0.750000, 0.250000),
            vec2(0.625000, 0.750000),
            vec2(0.625000, 0.500000),
            vec2(0.625000, 0.250000),
            vec2(0.500000, 0.750000),
            vec2(0.500000, 0.500000),
            vec2(0.500000, 0.250000),
            vec2(0.375000, 0.750000),
            vec2(0.375000, 0.500000),
            vec2(0.375000, 0.250000),
            vec2(0.687500, 0.000000),
            vec2(0.562500, 0.000000),
            vec2(0.437500, 0.000000),
            vec2(0.312500, 0.000000),
            vec2(0.187500, 0.000000),
            vec2(0.062500, 0.000000),
            vec2(0.937500, 0.000000),
            vec2(0.812500, 0.000000),
            vec2(0.250000, 0.750000),
            vec2(0.250000, 0.500000),
            vec2(0.250000, 0.250000),
            vec2(0.687500, 1.000000),
            vec2(0.562500, 1.000000),
            vec2(0.437500, 1.000000),
            vec2(0.312500, 1.000000),
            vec2(0.187500, 1.000000),
            vec2(0.062500, 1.000000),
            vec2(0.937500, 1.000000),
            vec2(0.812500, 1.000000),
            vec2(0.125000, 0.750000),
            vec2(0.125000, 0.500000),
            vec2(0.125000, 0.250000),
            vec2(0.000000, 0.750000),
            vec2(1.000000, 0.750000),
            vec2(0.000000, 0.500000),
            vec2(1.000000, 0.500000),
            vec2(1.000000, 0.250000),
            vec2(0.000000, 0.250000),
            vec2(0.875000, 0.750000),
            vec2(0.875000, 0.500000),
            vec2(0.875000, 0.250000)
        );

        int vertex_indices[144] = int[](
            12, 2, 5, 0, 4, 1, 1, 5, 2, 0, 16, 3, 3, 7, 4, 4, 8, 5, 3, 16, 6, 12, 5, 8, 12, 8, 11, 6, 10, 7, 8,
            10, 11, 6, 16, 9, 12, 11, 15, 9, 14, 10, 10, 15, 11, 9, 16, 13, 12, 15, 19, 13, 18, 14, 14, 19, 15,
            13, 16, 17, 12, 19, 22, 17, 21, 18, 18, 22, 19, 17, 16, 20, 20, 16, 23, 12, 22, 25, 20, 24, 21, 21,
            25, 22, 24, 2, 25, 23, 16, 0, 12, 25, 2, 24, 0, 1, 0, 3, 4, 1, 4, 5, 3, 6, 7, 4, 7, 8, 6, 9, 10, 8,
            7, 10, 9, 13, 14, 10, 14, 15, 13, 17, 18, 14, 18, 19, 17, 20, 21, 18, 21, 22, 20, 23, 24, 21, 24,
            25, 24, 1, 2, 24, 23, 0
        );

        int texcoord_indices[144] = int[](
            12, 2, 5, 0, 4, 1, 1, 5, 2, 0, 23, 3, 3, 7, 4, 4, 8, 5, 3, 24, 6, 13, 5, 8, 14, 8, 11, 6, 10, 7, 8,
            10, 11, 6, 25, 9, 15, 11, 22, 9, 21, 10, 10, 22, 11, 9, 26, 20, 16, 22, 33, 20, 32, 21, 21, 33, 22,
            20, 27, 31, 17, 33, 39, 31, 36, 32, 32, 39, 33, 31, 28, 34, 35, 29, 40, 18, 38, 42, 35, 41, 37, 37,
            42, 38, 41, 2, 42, 40, 30, 0, 19, 42, 2, 41, 0, 1, 0, 3, 4, 1, 4, 5, 3, 6, 7, 4, 7, 8, 6, 9, 10, 8,
            7, 10, 9, 20, 21, 10, 21, 22, 20, 31, 32, 21, 32, 33, 31, 34, 36, 32, 36, 39, 35, 40, 41, 37, 41,
            42, 41, 1, 2, 41, 40, 0
        );

        out vec3 v_vertex;
        out vec3 v_normal;
        out vec2 v_texcoord;

        void main() {
            v_vertex = vertices[vertex_indices[gl_VertexID]];
            v_normal = vertices[vertex_indices[gl_VertexID]];
            v_texcoord = texcoords[texcoord_indices[gl_VertexID]];
            gl_Position = camera_matrix * vec4(v_vertex, 1.0);
        }
    ''',
    fragment_shader='''
        #version 330 core

        in vec3 v_normal;

        layout (location = 0) out vec4 out_color;

        void main() {
            vec3 light_direction = vec3(0.48, 0.32, 0.81);
            float lum = dot(light_direction, normalize(v_normal)) * 0.7 + 0.3;
            out_color = vec4(lum, lum, lum, 1.0);
        }
    ''',
    layout=[
        {
            'name': 'Common',
            'binding': 0,
        },
    ],
    resources=[
        {
            'type': 'uniform_buffer',
            'binding': 0,
            'buffer': uniform_buffer,
        },
    ],
    framebuffer=[image, depth],
    topology='triangles',
    cull_face='back',
    vertex_count=144,
)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    now = pygame.time.get_ticks() / 1000.0

    ctx.new_frame()
    image.clear()
    depth.clear()
    camera_position = (4.0, 3.0, 2.0)
    camera = zengl.camera(camera_position, aspect=1.0, fov=45.0)
    uniform_buffer.write(struct.pack('64s3f4x', camera, *camera_position))
    pipeline.render()
    image.blit()
    ctx.end_frame()

    pygame.display.flip()
