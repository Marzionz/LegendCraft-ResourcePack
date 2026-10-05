#version 330

// A window into the void: texels marked by their alpha are not drawn as paint.
// Through them the viewer sees a space below the surface, pinned to the world and shifting as the
// viewer moves, the way a scene does through a window. Inside it a nebula swirls, pixel shooting
// stars fly as in the End portal, and motes rise from the deep and fade before the surface.
// Needs the Globals block (camera position, game time) and the fragment's camera-relative position.

// The marker is an alpha of 250 to 254: the hole's texels carry painted void art at that alpha,
// which is what a client drawing its own shaders (an Iris shaderpack) shows instead. The alpha also
// says how far the texel is from the rim: 250 on the rim, 254 four texels in or more.
const float VOID_WINDOW_ALPHA_LOW = 249.5 / 255.0;
const float VOID_WINDOW_ALPHA_HIGH = 254.5 / 255.0;

const vec3 VOID_ABYSS = vec3(10.0, 4.0, 16.0) / 255.0;
const vec3 VOID_RAW = vec3(30.0, 2.0, 51.0) / 255.0;
const vec3 VOID_DEEP_VIOLET = vec3(58.0, 14.0, 85.0) / 255.0;
const vec3 VOID_VIOLET = vec3(123.0, 31.0, 162.0) / 255.0;
const vec3 VOID_LIGHT = vec3(193.0, 88.0, 220.0) / 255.0;

const float VOID_TAU = 6.2831853;
// GameTime runs 0 to 1 over a 24000-tick day and then wraps. Every motion below turns a whole
// number of times per day, so the wrap is seamless.
const float VOID_DAY_SECONDS = 1200.0;

const int VOID_STAR_LAYERS = 6;
const float VOID_STAR_CELLS_PER_BLOCK = 2.0;
const float VOID_STAR_WRAP_CELLS = 64.0;
const float VOID_STAR_DENSITY = 0.12;
const float VOID_STAR_PIXEL = 1.0 / 16.0;
const vec3[] VOID_STAR_COLOURS = vec3[](
    VOID_LIGHT,
    VOID_VIOLET,
    vec3(224.0, 90.0, 232.0) / 255.0,
    vec3(138.0, 123.0, 255.0) / 255.0
);
const int VOID_MOTE_PLANES = 5;
// Rising motes complete 60 cycles a day: one every 20 seconds.
const float VOID_MOTE_CYCLES_PER_DAY = 60.0;
const float VOID_MOTE_DEEPEST = 5.0;
const float VOID_MOTE_SHALLOWEST = 0.25;

bool is_void_window(vec4 texel) {
    return texel.a > VOID_WINDOW_ALPHA_LOW && texel.a < VOID_WINDOW_ALPHA_HIGH;
}

float void_rim_at(vec4 texel) {
    return is_void_window(texel) ? (texel.a * 255.0 - 249.0) / 5.0 : 0.0;
}

// How deep inside the hole this point lies, 0 at the rim to 1 well inside, smoothed between texels.
float void_window_rim(sampler2D tex, vec2 uv) {
    vec2 at = uv * vec2(textureSize(tex, 0)) - 0.5;
    ivec2 i = ivec2(floor(at));
    vec2 f = fract(at);
    float a = void_rim_at(texelFetch(tex, i, 0));
    float b = void_rim_at(texelFetch(tex, i + ivec2(1, 0), 0));
    float c = void_rim_at(texelFetch(tex, i + ivec2(0, 1), 0));
    float d = void_rim_at(texelFetch(tex, i + ivec2(1, 1), 0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float void_hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float void_noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(void_hash(i), void_hash(i + vec2(1.0, 0.0)), u.x),
               mix(void_hash(i + vec2(0.0, 1.0)), void_hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

float void_fbm(vec2 p) {
    float sum = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 4; i++) {
        sum += void_noise(p) * amp;
        p = mat2(1.6, 1.2, -1.2, 1.6) * p + 7.3;
        amp *= 0.5;
    }
    return sum;
}

mat2 void_rotate(float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return mat2(c, s, -s, c);
}

// A slow circle of `radius`, turning `turnsPerDay` (a whole number) times per day.
vec2 void_orbit(float turnsPerDay, float radius, float phase) {
    float a = VOID_TAU * (GameTime * turnsPerDay + phase);
    return vec2(cos(a), sin(a)) * radius;
}

// One star per cell for a `density` share of cells, a soft point at a random spot in it.
float void_stars(vec2 p, float density, float radius) {
    vec2 cell = floor(p);
    if (void_hash(cell) > density) {
        return 0.0;
    }
    vec2 centre = vec2(void_hash(cell + 7.1), void_hash(cell + 3.3)) * 0.7 + 0.15;
    return smoothstep(radius, 0.0, length(fract(p) - centre)) * (0.4 + 0.6 * void_hash(cell + 1.9));
}

// Where the view ray through `rel` meets the plane `depth` blocks below the surface, in world xz.
// The surface is the flat decal the fragment lies on; looking up from below sees nothing deep.
vec2 void_layer(vec3 rel, vec3 dir, vec3 camera, float depth) {
    float t = depth / max(-dir.y, 0.05);
    vec3 hit = rel + dir * t + camera;
    return hit.xz;
}

// End-portal-style shooting stars: single Minecraft pixels, square to the world, in four colours.
// Each layer sits deeper, flies its stars along its own heading and runs slower the deeper it is;
// a layer wraps every VOID_STAR_WRAP_CELLS cells, so the day wrap lands on the same pattern.
vec3 void_shooting_stars(vec3 rel, vec3 dir, vec3 camera) {
    vec3 sum = vec3(0.0);
    for (int i = 0; i < VOID_STAR_LAYERS; i++) {
        float layer = float(i);
        float depth = 0.9 + layer * 1.1;
        mat2 heading = void_rotate(layer * 2.39996 + 0.7);
        vec2 p = heading * void_layer(rel, dir, camera, depth) * VOID_STAR_CELLS_PER_BLOCK;
        p.x += fract(GameTime * (40.0 - layer * 4.0)) * VOID_STAR_WRAP_CELLS;
        vec2 cell = floor(p);
        cell.x = mod(cell.x, VOID_STAR_WRAP_CELLS);
        cell += layer * 31.7;
        if (void_hash(cell) > VOID_STAR_DENSITY) {
            continue;
        }
        vec2 centre = vec2(void_hash(cell + 7.1), void_hash(cell + 3.3)) * 0.7 + 0.15;
        vec2 off = transpose(heading) * (fract(p) - centre) / VOID_STAR_CELLS_PER_BLOCK;
        if (max(abs(off.x), abs(off.y)) > VOID_STAR_PIXEL * 0.5) {
            continue;
        }
        vec3 tint = VOID_STAR_COLOURS[int(void_hash(cell + 5.5) * 4.0) % 4];
        float bright = (0.6 + 0.4 * void_hash(cell + 1.9)) * (1.0 - layer * 0.1);
        sum += tint * bright;
    }
    return sum;
}

// Motes on planes that rise from the deep, swell and drift as they come up, then fade out before
// the surface; each plane draws a new scatter on each rise.
vec3 void_motes(vec3 rel, vec3 dir, vec3 camera) {
    vec3 sum = vec3(0.0);
    for (int i = 0; i < VOID_MOTE_PLANES; i++) {
        float k = float(i);
        float cycle = GameTime * VOID_MOTE_CYCLES_PER_DAY + k / float(VOID_MOTE_PLANES);
        float rise = fract(cycle);
        // Four scatters per plane; 60 cycles a day divides evenly, so the day wrap keeps the scatter.
        float scatter = mod(floor(cycle), 4.0);
        float depth = mix(VOID_MOTE_DEEPEST, VOID_MOTE_SHALLOWEST, rise);
        vec2 drift = void_rotate(k * 2.1 + scatter * 1.3) * vec2(rise * 0.8, 0.0);
        vec2 p = (void_layer(rel, dir, camera, depth) + drift) * 1.6 + scatter * 13.1 + k * 5.7;
        float fade = smoothstep(0.0, 0.3, rise) * smoothstep(1.0, 0.7, rise);
        float glow = void_stars(p, 0.2, mix(0.12, 0.22, rise));
        float core = void_stars(p, 0.2, mix(0.04, 0.07, rise));
        sum += (VOID_VIOLET * glow + VOID_LIGHT * core * 1.4) * fade;
    }
    return sum;
}

vec3 void_window(vec3 rel, float rim) {
    vec3 dir = normalize(rel);
    // The camera's world position, kept small: the pattern repeats every 1024 blocks.
    vec3 camera = vec3(CameraBlockPos & ivec3(1023)) - CameraOffset;

    vec3 color = VOID_ABYSS;

    // The nebula: warped clouds that swirl in place, with bright filaments where the folds meet.
    vec2 nebulaAt = void_layer(rel, dir, camera, 0.6);
    vec2 warp = vec2(void_fbm(nebulaAt * 0.7 + void_orbit(10.0, 0.6, 0.0)),
                     void_fbm(nebulaAt * 0.7 + void_orbit(10.0, 0.6, 0.37) + 5.2));
    float cloud = void_fbm(nebulaAt * 0.9 + warp * 1.8);
    color = mix(color, VOID_RAW, smoothstep(0.3, 0.7, cloud));
    color = mix(color, VOID_DEEP_VIOLET, smoothstep(0.55, 0.85, cloud) * 0.7);
    float filament = 1.0 - abs(2.0 * void_fbm(nebulaAt * 1.3 + warp * 2.4 + 11.0) - 1.0);
    color += VOID_VIOLET * pow(filament, 8.0) * 0.55;

    // A second, deeper cloud, darker and drifting the other way.
    vec2 deepAt = void_layer(rel, dir, camera, 3.0);
    float deep = void_fbm(deepAt * 0.45 + void_orbit(6.0, 0.9, 0.5));
    color += VOID_RAW * smoothstep(0.45, 0.8, deep) * 0.8;

    // Far stars by direction alone: at infinity they shift with turning, never with walking.
    vec2 farAt = dir.xz / (abs(dir.y) + 0.35) * 18.0;
    float twinkle = 0.65 + 0.35 * sin(VOID_TAU * (GameTime * 200.0 + void_hash(floor(farAt))));
    color += VOID_LIGHT * 0.5 * twinkle * void_stars(farAt, 0.3, 0.07);

    color += void_shooting_stars(rel, dir, camera);
    color += void_motes(rel, dir, camera);

    // The pit's walls: the deep fades to black toward the rim, and the rim's broken edge glows.
    float inside = smoothstep(0.0, 0.85, rim);
    color = mix(VOID_ABYSS * 0.5, color, inside);
    float pulse = 0.8 + 0.2 * sin(VOID_TAU * GameTime * 150.0);
    float edge = 1.0 - rim;
    color += VOID_VIOLET * pow(edge, 3.0) * 0.9 * pulse;
    color += VOID_LIGHT * pow(edge, 8.0) * 0.6 * pulse;

    return min(color, vec3(1.0));
}
