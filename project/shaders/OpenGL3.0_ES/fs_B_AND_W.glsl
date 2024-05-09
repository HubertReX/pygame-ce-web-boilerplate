#version 300 es
precision highp float;

uniform float time;
uniform vec2 screen_size;
uniform sampler2D Texture;

in vec2 vertex;
out vec4 out_color;

const float Epsilon = 1e-10;

// intensivity/saturation of a color
// value in range [0.0, 1.0]
// value  > 0.5 => saturated
// value == 0.5 => no change
// value  < 0.5 => bleached
const float SATURATION = 0.0;

// circle around color wheel
// value in range [0.0, 1.0]
// 0.0 => no change
const float HUE_SHIFT = 0.0;

// lightness/brightness
// value in range [0.0, 1.0]
// value > 0.5 => lighter
//         0.5 => no change
// value < 0.5 => darker
const float VALUE = 0.4;

vec3 RGBtoHSV(in vec3 RGB)
{
    vec4  P   = (RGB.g < RGB.b) ? vec4(RGB.bg, -1.0, 2.0/3.0) : vec4(RGB.gb, 0.0, -1.0/3.0);
    vec4  Q   = (RGB.r < P.x) ? vec4(P.xyw, RGB.r) : vec4(RGB.r, P.yzx);
    float C   = Q.x - min(Q.w, Q.y);
    float H   = abs((Q.w - Q.y) / (6.0 * C + Epsilon) + Q.z);
    vec3  HCV = vec3(H, C, Q.x);
    float S   = HCV.y / (HCV.z + Epsilon);
    
    return vec3(HCV.x, S, HCV.z);
}

vec3 HSVtoRGB(in vec3 HSV)
{
    float H   = HSV.x;
    float R   = abs(H * 6.0 - 3.0) - 1.0;
    float G   = 2.0 - abs(H * 6.0 - 2.0);
    float B   = 2.0 - abs(H * 6.0 - 4.0);
    vec3  RGB = clamp( vec3(R,G,B), 0.0, 1.0 );
    return ((RGB - 1.0) * HSV.y + 1.0) * HSV.z;
}

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
    vec3 color = screen(vertex);
    
    vec3 col_hsv = RGBtoHSV(color.rgb);
    
    // HUE
    col_hsv.x += HUE_SHIFT;

    // SATURATION
    col_hsv.y *= SATURATION * 2.0;

    // LIGHTNESS
    col_hsv.z *= VALUE * 2.0;

    col_hsv = clamp(col_hsv, 0.0, 1.0);
    color = HSVtoRGB(col_hsv.rgb);
    
    out_color = vec4(color, 1.0);
}