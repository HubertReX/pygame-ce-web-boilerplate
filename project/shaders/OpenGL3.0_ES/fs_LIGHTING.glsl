#version 300 es
precision highp float;

// common include must provide:
// int MAX_LIGHTS_CNT - maksimal size of array (needs to fixed even the atctual number of lights might change)
// vec2 screen_size - width, heigh used to map uv
#include "common"

uniform float time;
// day/night ratio
// 0.0 ==> day
// 1.0 ==> night
uniform float ratio;
// camera zoom level
uniform float scale;
// how many lights are there currently in the scene
// LightPositions uniform is alwasy passing all MAX_LIGHTS_CNT
// and we need to know how many values are actually valid
uniform int lights_cnt;
// uniform vec2 screen_size;
uniform sampler2D Texture;

in vec2 vertex;

layout (std140) uniform LightPositions {
    // 0: light x pos
    // 1: light y pos
    // 3: light size of the circle around the source to be lit
    vec3 ligh_positions[MAX_LIGHTS_CNT];
};

out vec4 out_color;

const float PI = 3.1415926535897932384626;
const float Epsilon = 1e-10;

// intensivity/saturation of a color
// value in range [0.0, 1.0]
// value  > 0.5 => saturated
// value == 0.5 => no change
// value  < 0.5 => bleached
const float SATURATION = 0.62;

// circle around color wheel
// value in range [0.0, 1.0]
// 0.0 => no change
const float HUE_SHIFT = 0.0;

// lightness/brightness
// value in range [0.0, 1.0]
// value > 0.5 => lighter
//         0.5 => no change
// value < 0.5 => darker
const float VALUE = 0.5;

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

float get_distance(vec3 pos) {
    vec2 uv = vertex * 0.5 + 0.5;
    uv = screen_size * uv;
    // piselate
    float TILE = 4.0 * scale;
    uv = floor(uv / TILE) * TILE;
    return distance(uv, pos.xy);
}

void dummy() {
    // pretand to use uniforms
    // without it pipeline creation fails in zengl
    out_color = vec4(screen_size.x, 0.0, 0.0, time);
}

void main() {
    dummy();
    float dist = 999999.0;
    float size = 100.0;
    vec3 color = screen(vertex);

    vec3 col_hsv = RGBtoHSV(color.rgb);

    // HUE
    col_hsv.x += HUE_SHIFT;

    // SATURATION
    col_hsv.y *= SATURATION * 2.0;

    const float night = 0.1;
    const float day = 1.0;

    // LIGHTNESS
    if (ratio > 0.0) {
        float new_night = mix(day, night,  ratio);
        int max_lights = min(lights_cnt, MAX_LIGHTS_CNT);
        float new_dist = 0.0;
        for (int i = 0; i < max_lights; i++) {
            new_dist = get_distance(ligh_positions[i]);
            if (new_dist < dist) {
                dist = new_dist;
                size = ligh_positions[i].z * scale;
            }
        }
        float max_distance = size + (sin(time * PI * 400.0) * 5.0); // 256.0;
        float min_distance = max_distance - (16.0 * scale); // 150.0;

        // dist = floor(dist / 16.0) * 16.0;

        // full night color
        if (dist >= max_distance) {
            col_hsv.z *= new_night;
            // day = day;
        }
        // transition between night and day color
        if (dist < max_distance && dist >= min_distance) {
            col_hsv.z *= (mix(day, new_night,clamp(( dist - min_distance) / (max_distance - min_distance), 0.0, 1.0)));

            // col_hsv.z *= mix(day, night, ratio);
        }
        // day color
        if (dist < min_distance) {
            col_hsv.z *= day;
            // day = day;
        }
    } else {
        col_hsv.z *= day;
    }
    col_hsv = clamp(col_hsv, 0.0, 1.0);
    color = HSVtoRGB(col_hsv.rgb);


    out_color = vec4(color, 1.0);
}