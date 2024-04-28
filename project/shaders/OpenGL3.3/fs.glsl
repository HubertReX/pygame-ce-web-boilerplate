precision mediump float;
// #ifdef GL_ES 

// precision highp float;

// #endif

// in vec3 v_vertex;
// in vec3 v_color;

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

// layout (location = 1) out vec4 out_color;
// vec4 out_color;

void main() {
    vec3 v_color = vec3(0.24, 0.69, 0.24);
    float u = smoothstep(0.0, u_resolution.x, abs(gl_FragCoord.x - (u_resolution.x / 2.0)));
    float v = smoothstep(0.48, 0.47, abs(gl_FragCoord.y - 0.5));
    // out_color.rgb = pow(out_color.rgb, vec3(1.0 / 2.2));
    vec2 st = gl_FragCoord.xy/u_resolution.xy;
	vec4 out_color = vec4(st.x,st.y,0.0,1.0);
    out_color = vec4(v_color * u, 1.0);
    gl_FragColor = out_color; 
    // vec4(float(out_color.r), float(out_color.g), float(out_color.b), 1.0);
}
