#version 300 es
precision highp float;

uniform float time;
uniform vec2 screen_size;
uniform sampler2D Texture;

in vec2 vertex;
out vec4 out_color;

float hash13(vec3 p3) {
    p3 = fract(p3 * 0.1031);
    p3 += dot(p3, p3.zyx + 31.32);
    return fract((p3.x + p3.y) * p3.z);
}

vec2 hash23(vec3 p3) {
    p3 = fract(p3 * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}

vec3 sample_screen(vec2 uv) {
    return vec3(
        texture(Texture, uv - vec2(0.002, 0.0)).r,
        texture(Texture, uv).g,
        texture(Texture, uv + vec2(0.002, 0.0)).b
    );
}

vec3 screen(vec2 vertex) {
    if (abs(vertex.x) > 1.001 || abs(vertex.y) > 1.001) {
        return vec3(0.0);
    }
    vec2 uv = vertex * 0.5 + 0.5;
    vec3 color = sample_screen(uv);
    float noise = hash13(floor(vec3(uv * screen_size, floor(time))));
    float scanline = sin(uv.y * screen_size.y * 3.141592 + time * 0.05) * 0.1 + 0.9;
    color *= 1.0 + (noise - 0.5) * 0.1;
    color = color * scanline * 1.05 + 0.05;
    return color;
}

void main() {
    vec2 v = vertex * (1.0 + pow(abs(vertex.yx), vec2(2.0)) * 0.1);
    vec3 color = vec3(0.0);
    for (int i = 0; i < 16; ++i) {
        vec2 offset = hash23(vec3(v * screen_size, float(i))) - 0.5;
        color += screen(v * 1.01 + offset / screen_size);
    }
    color /= 16.0;
    out_color = vec4(color, 1.0);
}