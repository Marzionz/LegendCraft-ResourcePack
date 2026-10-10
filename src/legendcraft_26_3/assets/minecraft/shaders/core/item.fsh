#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:globals.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>
#include <legendcraft:void_window.glsl>

uniform sampler2D Sampler0;

#ifdef GLINT
uniform sampler2D GlintSampler;
#endif

#ifndef OIT_ALPHA_ONLY
layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
#endif
layout(location = 2) in vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) in vec4 lightMapColor;
layout(location = 4) in vec4 overlayColor;
#endif
layout(location = 5) in vec2 texCoord0;
#ifdef GLINT
layout(location = 6) in vec2 texCoordGlint;
#endif
layout(location = 7) in vec3 voidViewRel;
layout(location = 8) in vec3 voidNormal;
layout(location = 9) in float voidFade;
layout(location = 10) in float voidMarked;
layout(location = 11) in float ghostAlpha;

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

#ifndef OIT_ALPHA_ONLY
// Glint, translucent accumulation and fog: what every texel gets, a void texel included.
vec4 finishColor(vec4 color) {
    #ifdef GLINT
    vec4 glintColor = GlintAlpha * texture(GlintSampler, texCoordGlint);
    color.rgb += glintColor.rgb * glintColor.rgb;
    #endif

    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    vec4 fogColor = vec4(FogColor.rgb * color.a, FogColor.a);
    #else
    vec4 fogColor = FogColor;
    #endif

    return apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, fogColor);
}

vec4 calculateFinalColor(vec4 color) {
    color.rgb = mix(overlayColor.rgb, color.rgb, overlayColor.a);
    color *= lightMapColor;
    return finishColor(color);
}
#endif

void main() {
    vec4 color = texture(Sampler0, texCoord0);
    // A void texel takes no cutout, tint, hurt overlay or lightmap; its window's fade and band
    // set its opacity.
    bool voidTexel = voidMarked > 0.5 && is_void_window(color);
    if (voidTexel) {
        float opacity = voidFade * void_window_opacity(color);
        #ifdef OIT_ALPHA_ONLY
        color = vec4(0.0, 0.0, 0.0, opacity);
        #else
        color = vec4(void_window(voidViewRel, voidNormal, void_window_rim(Sampler0, texCoord0)), opacity);
        #endif
    } else {
        #ifdef ALPHA_CUTOUT
        if (color.a < ALPHA_CUTOUT) {
            discard;
        }
        #endif

        color *= vertexColor * ColorModulator;
    }

    #ifdef GLINT
    color.a = max(color.a, GlintAlpha);
    #endif
    // After glint's floor, so a ghost is never drawn above its level.
    color.a *= ghostAlpha;

    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = voidTexel ? finishColor(color) : calculateFinalColor(color);
    #endif
}
