#version 330

#moj_import <minecraft:light.glsl>
#moj_import <minecraft:fog.glsl>
#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:projection.glsl>
#moj_import <minecraft:sample_lightmap.glsl>

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV1;
in ivec2 UV2;
in vec3 Normal;

uniform sampler2D Sampler2;

out float sphericalVertexDistance;
out float cylindricalVertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;
out vec3 voidViewRel;
out vec3 voidNormal;
out float voidFade;
out float voidMarked;
out float ghostAlpha;

// An item tinted green 1, blue 254 is a void window (tools/void_marker.py). Its red is the window's
// fade, and its ordinary texels are tinted grey by that red alone, so the mark never colours them.
bool is_void_mark(vec4 tint) {
    return abs(tint.g * 255.0 - 1.0) < 0.5 && abs(tint.b * 255.0 - 254.0) < 0.5;
}

// A ghost limb rig codes its alpha into its tints (LegendCraft-Core GhostAlpha, tools/ghost_mark.py):
// red's low nibble GHOST_MARK_RED and blue's GHOST_MARK_BLUE mark the tint, and green's low nibble is
// a level drawn at level / GHOST_LEVELS alpha. The face keeps the tint's top nibbles as its colour.
const float GHOST_MARK_RED = 10.0;
const float GHOST_MARK_BLUE = 5.0;
const float GHOST_LEVELS = 16.0;

float low_nibble(float channel) {
    return mod(floor(channel * 255.0 + 0.5), 16.0);
}

// The tint's ghost level, or 0 for a tint that carries no mark.
float ghost_level(vec4 tint) {
    if (abs(low_nibble(tint.r) - GHOST_MARK_RED) > 0.5 || abs(low_nibble(tint.b) - GHOST_MARK_BLUE) > 0.5) {
        return 0.0;
    }
    return low_nibble(tint.g);
}

// The tint's colour with its code replaced by each nibble's midpoint.
vec3 ghost_colour(vec4 tint) {
    return (floor(tint.rgb * 255.0 / 16.0 + 0.5 / 16.0) * 16.0 + 8.0) / 255.0;
}

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    voidMarked = is_void_mark(Color) ? 1.0 : 0.0;
    vec4 tint = voidMarked > 0.5 ? vec4(Color.rrr, Color.a) : Color;
    float level = ghost_level(Color);
    ghostAlpha = level > 0.5 ? level / GHOST_LEVELS : 1.0;
    if (level > 0.5) {
        tint = vec4(ghost_colour(Color), Color.a);
    }

    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);

    vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, tint) * sample_lightmap(Sampler2, UV2);

    texCoord0 = UV0;
    voidViewRel = Position;
    voidNormal = Normal;
    voidFade = Color.r;
}
