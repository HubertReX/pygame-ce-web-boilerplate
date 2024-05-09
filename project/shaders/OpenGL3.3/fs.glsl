#version 330 core


uniform float time;
uniform vec2 screen_size;
uniform sampler2D Texture;

in vec2 vertex;
out vec4 out_color;

vec3 screen(vec2 vertex) {
    if (abs(vertex.x) > 1.001 || abs(vertex.y) > 1.001) {
        return vec3(0.0);
    }
    vec2 uv = vertex * 0.5 + 0.5;
    vec3 color = texture(Texture, uv).rgb;
    return color;
}

void dummy() {
    // pretand to use uniforms
    // without it pipeline creation fails in zengl
    out_color = vec4(screen_size.x, screen_size.y, 0, time);
}

void main() {
    dummy();
    // simple texture mapping - no change
    vec3 color = screen(vertex);
    out_color = vec4(color, 1.0);
}