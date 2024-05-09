#version 330 core

vec2 vertices[4] = vec2[](
    vec2(-1.0, -1.0),
    vec2(-1.0, 1.0),
    vec2(1.0, -1.0),
    vec2(1.0, 1.0)
);

out vec2 vertex;

void main() {
    gl_Position = vec4(vertices[gl_VertexID], 0.0, 1.0);
    vertex = vertices[gl_VertexID];
}