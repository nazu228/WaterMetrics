"""
GLSL шейдеры для Cyber Grid God Mode Engine (WaterMetrics).
Включает 2-проходную систему рендеринга:
1. GRID_VERT + GRID_FRAG — 3D каркасная сетка Synthwave с перспективной проекцией,
   FBM/синусоидальными волнами, откликом на мышь и круги от кликов.
2. BLOOM_VERT + BLOOM_FRAG — Неоновый пост-процессинг (Bloom, хроматическая аберрация,
   виньетирование, CRT-сканлайны и радиальные полосы шторма).
"""

# ---------------------------------------------------------------------------
# SHADER 1: GRID_VERT — 3D Synthwave Wireframe Grid Vertex Shader
# ---------------------------------------------------------------------------
GRID_VERT = """
#version 330 core

layout(location = 0) in vec2 a_grid_pos;  // grid XZ position [-1..1]
layout(location = 1) in float a_mirror;   // 0.0 = bottom grid, 1.0 = top grid

uniform float u_time;
uniform float u_storm;          // 0.0 calm -> 1.0 full storm
uniform float u_aspect;         // viewport width / height
uniform vec2  u_mouse_ndc;      // mouse in NDC [-1..1]
uniform vec2  u_ripple_xz[16];  // ripple XZ positions in grid space
uniform float u_ripple_t[16];   // ripple birth times
uniform float u_ripple_str[16]; // ripple strengths
uniform int   u_ripple_count;

out float v_fog;          // distance-based fog [0..1]
out float v_brightness;   // line brightness (horizon = 1.0, edges = 0.0)
out float v_ripple_glow;  // extra glow from nearby ripples
out float v_is_top;       // 0=bottom, 1=top

// Wave displacement Y for a single grid vertex (Smooth Low-Frequency Organic Composition)
float wave_y(vec2 xz, float time) {
    float storm = 1.0 + u_storm * 2.0;

    float w1 = sin(xz.x * 1.2 + time * 0.7) * cos(xz.y * 0.9 - time * 0.5) * 0.08 * storm;
    float w2 = sin(xz.x * 0.7 - time * 0.4 + xz.y * 0.8) * 0.05 * storm;
    float w3 = cos(xz.x * 0.5 + xz.y * 1.1 + time * 0.6) * 0.03 * storm;

    return w1 + w2 + w3;
}

// Ripple displacement from click events
float ripple_y(vec2 xz, float time) {
    float h = 0.0;
    for (int i = 0; i < u_ripple_count; i++) {
        float age  = time - u_ripple_t[i];
        if (age < 0.0 || age > 4.5) continue;
        float dist = length(xz - u_ripple_xz[i]);
        float r    = age * 0.6;
        float ring = exp(-pow(dist - r, 2.0) / (0.04 * 0.04));
        float dec  = exp(-age * 1.3) * u_ripple_str[i];
        h += ring * dec * 0.09;
    }
    return h;
}

void main() {
    vec2 xz = a_grid_pos;
    float mirror = a_mirror;

    // Compute Y displacement
    float y_wave   = wave_y(xz, u_time);
    float y_ripple = ripple_y(xz, u_time);
    float y = y_wave + y_ripple;

    // Mouse parallax tilt — subtle horizon lean
    float tilt = u_mouse_ndc.y * 0.04;
    y += tilt * (1.0 - abs(xz.y));

    // World position:
    // Bottom grid: Y goes below horizon (negative)
    // Top grid: Y goes above horizon (positive, mirrored)
    float sign_val = (mirror < 0.5) ? -1.0 : 1.0;
    vec3 world_pos = vec3(xz.x, sign_val * (0.0 - abs(y)), xz.y);

    // Perspective projection
    float z_dist = xz.y * 0.5 + 0.5;  // remap [-1..1] -> [0..1]
    if (mirror > 0.5) z_dist = 1.0 - z_dist;

    float z_near  = 0.15;
    float z_far   = 1.0;
    float persp_z = mix(z_near, z_far, z_dist);

    float fov     = 0.75;
    float px = world_pos.x / (persp_z * fov * u_aspect);

    float horizon_offset = (mirror < 0.5) ? -0.02 : 0.02;
    float grid_y = world_pos.y / (persp_z * fov);
    float py = grid_y + horizon_offset;

    // Fog: vertices far from horizon are more faded
    v_fog = clamp(z_dist * 1.3, 0.0, 1.0);

    // Brightness: horizon = brightest
    v_brightness = pow(z_dist, 0.55);

    // Ripple glow contribution
    v_ripple_glow = clamp(abs(y_ripple) * 18.0, 0.0, 1.0);

    v_is_top = mirror;

    gl_Position = vec4(px, py, 0.0, 1.0);
}
"""

# ---------------------------------------------------------------------------
# SHADER 2: GRID_FRAG — Wireframe Line Fragment Shader
# ---------------------------------------------------------------------------
GRID_FRAG = """
#version 330 core

in float v_fog;
in float v_brightness;
in float v_ripple_glow;
in float v_is_top;

out vec4 frag_color;

uniform vec3  u_line_color;    // theme accent color
uniform float u_time;
uniform float u_storm;

void main() {
    float alpha = v_brightness * (1.0 - v_fog * 0.72);

    float pulse = 0.88 + 0.12 * sin(u_time * 1.8);
    alpha *= pulse;

    if (u_storm > 0.05) {
        float flicker = 0.9 + 0.1 * sin(u_time * 28.0 + v_fog * 15.0);
        alpha *= mix(1.0, flicker, u_storm * 0.6);
    }

    vec3 col = u_line_color + u_line_color * v_ripple_glow * 1.2;
    alpha += v_ripple_glow * 0.5;
    alpha = clamp(alpha, 0.0, 1.0);

    frag_color = vec4(col, alpha);
}
"""

# ---------------------------------------------------------------------------
# SHADER 3: BLOOM_VERT — Fullscreen Quad Vertex Shader
# ---------------------------------------------------------------------------
BLOOM_VERT = """
#version 330 core

void main() {
    vec2 pos[3] = vec2[](vec2(-1.0, -1.0), vec2(3.0, -1.0), vec2(-1.0, 3.0));
    gl_Position = vec4(pos[gl_VertexID], 0.0, 1.0);
}
"""

# ---------------------------------------------------------------------------
# SHADER 4: BLOOM_FRAG — Bloom Post-Processing Shader
# ---------------------------------------------------------------------------
BLOOM_FRAG = """
#version 330 core

out vec4 frag_color;

uniform sampler2D u_scene;      // original wireframe render
uniform vec2      u_resolution;
uniform float     u_storm;
uniform float     u_time;
uniform vec3      u_line_color;

vec3 gaussian_blur(sampler2D tex, vec2 uv, vec2 dir) {
    vec3 col = vec3(0.0);
    float weights[7] = float[](0.0625, 0.125, 0.1875, 0.25, 0.1875, 0.125, 0.0625);
    float offsets[7] = float[](-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0);
    vec2 texel = 1.0 / u_resolution;
    for (int i = 0; i < 7; i++) {
        col += texture(tex, uv + dir * texel * offsets[i] * 1.8).rgb * weights[i];
    }
    return col;
}

vec3 bright_pass(vec2 uv) {
    vec3 col = texture(u_scene, uv).rgb;
    float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
    return col * smoothstep(0.15, 0.55, lum);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;

    vec3 scene = texture(u_scene, uv).rgb;

    vec3 bright = bright_pass(uv);
    vec3 blur_h = gaussian_blur(u_scene, uv, vec2(1.0, 0.0));
    vec3 blur_v = gaussian_blur(u_scene, uv, vec2(0.0, 1.0));
    vec3 bloom  = (blur_h + blur_v) * 0.5;

    float bloom_str = 1.4 + u_storm * 1.2;
    bloom = clamp(bloom * bloom_str, 0.0, 1.0);

    vec3 col = scene + bloom * 0.9;

    float dist  = length(uv - 0.5);
    float ca_str = (0.003 + u_storm * 0.004) * dist * dist;
    float r = texture(u_scene, uv + vec2( ca_str, 0.0)).r;
    float g = texture(u_scene, uv).g;
    float b = texture(u_scene, uv - vec2( ca_str, 0.0)).b;
    col = mix(col, vec3(r, g, b) + bloom * 0.5, 0.45);

    float vig = 1.0 - dot(uv - 0.5, uv - 0.5) * 1.35;
    col *= clamp(vig, 0.0, 1.0);

    float scan = 0.97 + 0.03 * sin(gl_FragCoord.y * 1.5 + u_time * 6.0);
    col *= scan;

    if (u_storm > 0.3) {
        vec2 dir_to_center = normalize(vec2(0.5) - uv);
        vec3 streak = vec3(0.0);
        float steps = 6.0;
        for (float s = 1.0; s <= steps; s += 1.0) {
            vec2 samp_uv = uv + dir_to_center * (s / steps) * u_storm * 0.012;
            streak += texture(u_scene, clamp(samp_uv, 0.001, 0.999)).rgb;
        }
        col += (streak / steps) * u_storm * 0.25;
    }

    frag_color = vec4(clamp(col, 0.0, 1.0), 1.0);
}
"""

# Алиасы для обратной совместимости
FULLSCREEN_VERT = BLOOM_VERT
FULLSCREEN_FRAG = BLOOM_FRAG
OCEAN_VERT = GRID_VERT
OCEAN_FRAG = GRID_FRAG
POST_VERT = BLOOM_VERT
POST_FRAG = BLOOM_FRAG
