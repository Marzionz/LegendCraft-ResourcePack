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

uniform sampler2D Sampler1;
uniform sampler2D Sampler2;

out float sphericalVertexDistance;
out float cylindricalVertexDistance;
out vec4 vertexColor;
out vec4 lightMapColor;
out vec4 overlayColor;

out vec2 texCoord0;
out vec3 voidViewRel;
out vec3 voidNormal;
out float voidFade;
out float voidMarked;

// An item tinted green 1, blue 254 is a void window (tools/void_marker.py). Its red is the window's
// fade, and its ordinary texels are tinted grey by that red alone, so the mark never colours them.
bool is_void_mark(vec4 tint) {
    return abs(tint.g * 255.0 - 1.0) < 0.5 && abs(tint.b * 255.0 - 254.0) < 0.5;
}

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    voidMarked = is_void_mark(Color) ? 1.0 : 0.0;
    vec4 tint = voidMarked > 0.5 ? vec4(Color.rrr, Color.a) : Color;

    sphericalVertexDistance = fog_spherical_distance(Position);
    cylindricalVertexDistance = fog_cylindrical_distance(Position);

    vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, tint);
    lightMapColor = sample_lightmap(Sampler2, UV2);
    overlayColor = texelFetch(Sampler1, UV1, 0);

    texCoord0 = UV0;
    voidViewRel = Position;
    voidNormal = Normal;
    voidFade = Color.r;
}
