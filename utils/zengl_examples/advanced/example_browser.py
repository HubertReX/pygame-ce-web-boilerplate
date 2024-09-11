import importlib
import os
import random

import imgui
from imgui.integrations.pyglet import create_renderer
from pyglet import gl

import assets
import window

examples = [
#     ('zengl_logo', 'ZenGL Logo'),
#     ('hello_triangle', 'Hello Triangle'),
#     ('bezier_curves', 'Bezier Curves'),
#     ('rigged_objects', 'Rigged Objects'),
#     ('envmap', 'Environment Map'),
#     ('normal_mapping', 'Normal Mapping'),
#     ('grass', 'Grass'),
#     ('box_grid', 'Box Grid'),
#     ('blending', 'Blending'),
#     ('julia_fractal', 'Fractal'),
#     ('vertex_colors', 'Toon Shading'),
#     ('deferred_rendering', 'Deferred Rendering'),
#     ('crate', 'Crate'),
# ]
('bezier_curves','bezier_curves'),
('bezier_surface','bezier_surface'),
('blinn_phong','blinn_phong'),
('blinn_phong_instanced','blinn_phong_instanced'),
('blinn_phong_simplified','blinn_phong_simplified'),
('blur','blur'),
('box_grid','box_grid'),
('composer','composer'),
('compute','compute'),
('convex_shapes','convex_shapes'),
('crate','crate'),
('cubemap_debugger','cubemap_debugger'),
('deferred_rendering','deferred_rendering'),
('empty_3d','empty_3d'),
('empty_app','empty_app'),
('example_browser','example_browser'),
('ffmpeg_stream','ffmpeg_stream'),
('float_output_image','float_output_image'),
('font','font'),
('font_new','font_new'),
('fxaa','fxaa'),
('generate_ao_map','generate_ao_map'),
('hardcoded_camera','hardcoded_camera'),
('heightmap_terrain','heightmap_terrain'),
('image_write_check','image_write_check'),
('index_buffer','index_buffer'),
('instanced_crates','instanced_crates'),
('instanced_rendering','instanced_rendering'),
('integrate_imgui','integrate_imgui'),
('marching_cubes','marching_cubes'),
('matplotlib_as_texture','matplotlib_as_texture'),
('mipmaps','mipmaps'),
('monkey','monkey'),
('multiple_outputs','multiple_outputs'),
('panorama_to_cubemap','panorama_to_cubemap'),
('particle_system','particle_system'),
('pocket_cube','pocket_cube'),
('points','points'),
('polygon_offset','polygon_offset'),
('pybullet_box_pile','pybullet_box_pile'),
('pygame_window','pygame_window'),
('pygmsh_shape','pygmsh_shape'),
('quaternions','quaternions'),
('reflection','reflection'),
('reflection_cubemap','reflection_cubemap'),
('render_interpolated_normals','render_interpolated_normals'),
('render_to_cubemap','render_to_cubemap'),
('render_to_lightmap','render_to_lightmap'),
('render_to_texture','render_to_texture'),
('render_to_texture_recursive','render_to_texture_recursive'),
('rigged_objects','rigged_objects'),
('rigging','rigging'),
('sdf_example','sdf_example'),
('sdf_tree','sdf_tree'),
('shader_include','shader_include'),
('shadertoy','shadertoy'),
('shadow','shadow'),
('skybox','skybox'),
('soft_body_simulation','soft_body_simulation'),
('sprites','sprites'),
('ssao','ssao'),
('ssao_from_depth','ssao_from_depth'),
('stencil','stencil'),
('streaming_video','streaming_video'),
('streaming_webcam','streaming_webcam'),
('texture_array','texture_array'),
('uniform_buffer','uniform_buffer'),
('uniforms','uniforms'),
('uniforms_mutate','uniforms_mutate'),
('uvsphere_to_cubemap','uvsphere_to_cubemap'),
('vertex_buffer','vertex_buffer'),
('vertex_colors','vertex_colors'),
('vertex_offset','vertex_offset'),
('window','window'),
('wine_barrel','wine_barrel'),
]
wnd = window.Window((1600, 900))
imgui.create_context()
imgui.get_io().ini_file_name = b''
impl = create_renderer(wnd._wnd)


class g:
    modules = {}
    example = None
    load_next = 'bezier_curves'
    download_progress = None


def load_example(name):
    if name in g.modules:
        importlib.reload(g.modules[name])
    else:
        g.modules[name] = importlib.import_module(name, '.')
    return g.modules[name]


def update(main_loop=True):
    if not main_loop and not g.load_next:
        if wnd.key_pressed('up'):
            index = next(i for i in range(-1, len(examples)) if examples[i + 1][0] == g.example)
            g.load_next = examples[index][0]
        if wnd.key_pressed('down'):
            index = next(i for i in range(len(examples)) if examples[i - 1][0] == g.example)
            g.load_next = examples[index][0]
        if wnd.key_pressed('tab'):
            g.load_next = g.example
            while g.load_next == g.example:
                g.load_next = random.choice(examples)[0]
    imgui.new_frame()
    # imgui.show_demo_window()
    imgui.push_style_var(imgui.STYLE_FRAME_PADDING, (4.0, 6.0))
    imgui.push_style_var(imgui.STYLE_WINDOW_BORDERSIZE, 0.0)
    imgui.push_style_color(imgui.COLOR_TEXT_DISABLED, 1.0, 1.0, 1.0, 1.0)
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu('Examples', True):
            for example, title in examples:
                if imgui.menu_item(title, None, g.example == example, g.load_next is None)[0]:
                    g.load_next = example
            imgui.end_menu()
        if g.download_progress:
            filename, progress = g.download_progress
            full = int(progress * 50)
            line = 'Downloading |' + '-' * full + ' ' * (50 - full) + '| ' + filename
            if imgui.begin_menu(line, False):
                imgui.end_menu()
        if g.load_next:
            if imgui.begin_menu('Loading...', False):
                imgui.end_menu()
        imgui.end_main_menu_bar()
    imgui.pop_style_color()
    imgui.pop_style_var(2)
    imgui.render()
    impl.render(imgui.get_draw_data())
    res = wnd.update()
    if not main_loop and g.load_next:
        return False
    elif g.load_next:
        g.example = g.load_next
        g.load_next = None
        assets.Loader = LoaderHook
        window.Window = WindowHook
        wnd._wnd.set_caption(os.path.join(os.path.dirname(__file__), g.example + '.py'))
        module = load_example(g.example)
        module.ctx.release('all')
    return res


class LoaderHook:
    def __init__(self, filename, total_size):
        self.filename = filename
        self.total_size = total_size
        self.index = 0

    def update(self, chunk_size):
        self.index += chunk_size
        g.download_progress = (self.filename, self.index / self.total_size)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        update(main_loop=False)

    def finish(self):
        g.download_progress = None


class WindowHook:
    def __init__(self):
        self.size = wnd.size
        self.aspect = wnd.aspect
        self.time = 0.0
        self.first = True

    @property
    def mouse(self):
        return wnd.mouse

    @property
    def wheel(self):
        return wnd.wheel

    def key_pressed(self, key):
        return wnd.key_pressed(key)

    def key_released(self, key):
        return wnd.key_released(key)

    def key_down(self, key):
        return wnd.key_down(key)

    def update(self):
        if self.first:
            self.first = False
            return True
        self.time += 1.0 / 60.0
        return update(main_loop=False)


while update():
    gl.glClearColor(0.0, 0.0, 0.0, 1.0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
