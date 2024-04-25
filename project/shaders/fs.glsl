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
