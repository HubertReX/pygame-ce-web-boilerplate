import math
import struct
from tqdm import tqdm
import zengl
from PIL import Image
import numpy as np
import ffmpeg

# https://stackoverflow.com/a/70791145/5236278

zengl.init(zengl.loader(headless=True))
ctx = zengl.context()

size = (1280, 720)
image = ctx.image(size, 'rgba8unorm', samples=1)
depth = ctx.image(size, 'depth24plus', samples=1)
process2 = (ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgba', s='{}x{}'.format(size[0], size[1]), r=60)
            .vflip()
            .output("recording.mp4", pix_fmt='rgb24', loglevel="quiet", r=60)
            .overwrite_output()
            .run_async(pipe_stdin=True)
)
def grass_mesh():
    a = np.linspace(0.0, 1.0, 8)
    b = np.square(a)
    c = np.sin(b * (np.pi - 1.0) + 1.0)
    verts = []
    for i in range(7):
        verts.append((-c[i] * 0.03, b[i] * 0.2, a[i]))
        verts.append((c[i] * 0.03, b[i] * 0.2, a[i]))
    verts.append((0.0, 0.2, 1.0))
    verts = ','.join('vec3(%.8f, %.8f, %.8f)' % x for x in verts)
    return 'vec3 grass[15] = vec3[](%s);' % verts

uniform_buffer = ctx.buffer(size=80)

N = 1000

instances = np.array([
    np.random.uniform(-1.0, 1.0, N),
    np.random.uniform(-1.0, 1.0, N),
    np.random.uniform(-np.pi, np.pi, N),
    np.random.uniform(0.0, 1.0, N),
]).T

instance_buffer = ctx.buffer(instances.astype('f4').tobytes())

ctx.includes['grass'] = grass_mesh()

triangle = ctx.pipeline(
    vertex_shader='''
        #version 330
        #include "grass"
        layout (std140) uniform Common {
            mat4 mvp;
        };
        layout (location = 0) in vec4 in_data;
        out vec2 v_data;
        void main() {
            vec3 v = grass[gl_VertexID];
            vec3 vert = vec3(
                in_data.x + cos(in_data.z) * v.x + sin(in_data.z) * v.y,
                in_data.y + cos(in_data.z) * v.y - sin(in_data.z) * v.x,
                v.z
            );
            gl_Position = mvp * vec4(vert, 1.0);
            v_data = vec2(in_data.w, v.z);
        }
    ''',
    fragment_shader='''
        #version 330
        in vec2 v_data;
        layout (location = 0) out vec4 out_color;
        void main() {
            vec3 yl = vec3(0.63, 1.0, 0.3);
            vec3 gn = vec3(0.15, 0.83, 0.3);
            out_color = vec4((yl + (gn - yl) * v_data.x) * v_data.y, 1.0);
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
    topology='triangle_strip',
    # cull_face='back',
    vertex_buffers=zengl.bind(instance_buffer, '4f /i', 0),
    instance_count=N,
    vertex_count=15,
)

for i in tqdm(range(300)):
    x, y = math.sin(i * 0.01) * 3.0, math.cos(i * 0.01) * 3.0
    camera = zengl.camera((x, y, 2.0), (0.0, 0.0, 0.5), aspect=size[0] / size[1], fov=45.0)

    uniform_buffer.write(camera)
    floats_list = [x, y, 2.0, 0.0]
    uniform_buffer.write(struct.pack('%sf' % len(floats_list), *floats_list), offset=64)

    image.clear_value = (1.0, 1.0, 1.0, 1.0)
    image.clear()
    depth.clear()
    triangle.render()
    image.blit()
    process2.stdin.write(
            image.read()
        )
process2.stdin.close()
process2.wait()

Image.frombuffer('RGBA', size, image.read(), 'raw', 'RGBA', 0, -1).save('recording.png')
