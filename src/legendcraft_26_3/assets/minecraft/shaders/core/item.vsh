#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:light.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:sample_lightmap.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
layout(location = 3) in ivec2 UV1;
layout(location = 4) in ivec2 UV2;
#ifdef GLINT_SPECIAL
layout(location = 5) in vec2 UV3;
#endif
layout(location = 6) in vec3 Normal;

#ifndef OIT_ALPHA_ONLY
uniform sampler2D Sampler1;
uniform sampler2D Sampler2;

layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif
layout(location = 2) out vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) out vec4 lightMapColor;
layout(location = 4) out vec4 overlayColor;
#endif

layout(location = 5) out vec2 texCoord0;
#ifdef GLINT
layout(location = 6) out vec2 texCoordGlint;
#endif
layout(location = 7) out vec3 voidViewRel;
layout(location = 8) out vec3 voidNormal;
layout(location = 9) out float voidFade;
layout(location = 10) out float voidMarked;
layout(location = 11) out float ghostAlpha;

// An item tinted green 1, blue 254 is a void window. Its red is the window's fade, and its ordinary
// texels are tinted grey by that red alone, so the mark never colours them.
bool is_void_mark(vec4 tint) {
    return abs(tint.g * 255.0 - 1.0) < 0.5 && abs(tint.b * 255.0 - 254.0) < 0.5;
}

// A ghost limb rig codes its alpha into its tints (LegendCraft-Core's GhostAlpha writes it):
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

    #ifndef OIT_ALPHA_ONLY
    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);
    #endif
    vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, tint);
    #ifndef OIT_ALPHA_ONLY
    lightMapColor = sample_lightmap(Sampler2, UV2);
    overlayColor = texelFetch(Sampler1, UV1, 0);
    #endif

    texCoord0 = UV0;
    #ifdef GLINT
    #ifdef GLINT_SPECIAL
    texCoordGlint = (TextureMat * vec4(UV3, 0.0, 1.0)).xy;
    #else
    texCoordGlint = (TextureMat * vec4(UV0, 0.0, 1.0)).xy;
    #endif
    #endif
    voidViewRel = Position;
    voidNormal = Normal;
    voidFade = Color.r;
}
