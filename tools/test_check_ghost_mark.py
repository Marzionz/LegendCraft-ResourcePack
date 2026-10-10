"""Acceptance suite for the ghost mark: the gate over shipped tints, and the item shaders' reading.

A ghost limb rig's tint colours carry an alpha code that the item shader turns into the face's
alpha. Any other tint carrying it would draw its item translucent.

Acceptance criteria:
1. The mark is read exactly: both mark nibbles and a level from 1 to 15. Control: level 0, a wrong
   nibble, white and the void marker are not marks.
2. A constant tint carrying the mark fails the gate, naming the file; so does a tint source's
   default, and a constant given as a float triple.
3. A float triple is read as the game reads it, each channel as float32 times 255 floored: one the
   game codes as a mark fails though rounding would clear it, and one the game leaves unmarked
   passes though rounding would mark it.
4. Control: a tree whose tints carry no mark passes.
5. The gate checks what it was pointed at or fails: a missing root, a root that is a file, an
   unreadable directory under the root and a tree with no item definition each fail.
6. Each covered item shader (the 26.1 and 26.2 overlays), compiled and run on a real GL context,
   draws a marked face in its nibble-midpoint colour at level/16 alpha, and leaves an unmarked
   tint, a level-0 tint and the void marker as they were. Kill arm: dropping the alpha, the
   level read, the recolour or the fragment's alpha multiply each fails that arm.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ghost_mark import is_ghost_coded  # noqa: E402
from void_marker import void_tint  # noqa: E402

GATE = os.path.join(HERE, "check_ghost_mark.py")
SOURCE = os.path.join(os.path.dirname(HERE), "src")
COVERED_OVERLAYS = ("legendcraft_26_1", "legendcraft_26_2")

# The contract with Core's GhostAlpha, pinned here as literals.
MARK_RED = 0xA
MARK_BLUE = 0x5
LEVELS = 16


def coded(rgb, level):
    return (rgb & 0xF0F0F0) | (MARK_RED << 16) | (level << 8) | MARK_BLUE


def item(tints):
    return {"model": {"type": "minecraft:model", "model": "legendcraft:item/fixture",
                      "tints": tints}}


def channels(rgb):
    return tuple(((rgb >> shift) & 0xFF) / 255.0 for shift in (16, 8, 0))


def shader_sources(overlay):
    shaders = os.path.join(SOURCE, overlay, "assets", "minecraft", "shaders", "core")
    with open(os.path.join(shaders, "item.vsh"), encoding="utf-8") as handle:
        vertex = handle.read()
    with open(os.path.join(shaders, "item.fsh"), encoding="utf-8") as handle:
        fragment = handle.read()
    return vertex, fragment


def between(text, start, end, what):
    begin = text.find(start)
    if begin < 0:
        raise AssertionError("%s: no %r to start from" % (what, start))
    finish = text.find(end, begin)
    if finish < 0:
        raise AssertionError("%s: no %r after %r" % (what, end, start))
    return text[begin:finish]


def harness(vertex, fragment):
    """The shaders' own ghost code, lifted verbatim into a pass that draws one tinted texel."""
    helpers = between(vertex, "bool is_void_mark", "void main()", "item.vsh helpers")
    body = between(vertex, "voidMarked = ", "sphericalVertexDistance", "item.vsh main")
    shade = between(fragment, "color *= vertexColor", "fragColor = apply_fog", "item.fsh main")
    vs = ("#version 330\nin vec2 Pos;\nin vec4 Color;\nout vec4 vertexColor;\n"
          "out float ghostAlpha;\nfloat voidMarked;\n" + helpers
          + "void main() {\n    gl_Position = vec4(Pos, 0.0, 1.0);\n    " + body
          + "    vertexColor = tint;\n}\n")
    fs = ("#version 330\nin vec4 vertexColor;\nin float ghostAlpha;\n"
          "uniform vec4 ColorModulator;\nconst vec4 overlayColor = vec4(0.0, 0.0, 0.0, 1.0);\n"
          "const vec4 lightMapColor = vec4(1.0);\nout vec4 fragColor;\nvoid main() {\n"
          "    vec4 color = vec4(1.0);\n    " + shade + "    fragColor = color;\n}\n")
    return vs, fs


class Renderer:
    """One texel through a real GLSL compiler and rasteriser: Mesa's, headless, over EGL."""

    def __init__(self):
        import moderngl
        self.gl = moderngl
        self.ctx = moderngl.create_standalone_context(backend="egl")
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((1, 1), 4, dtype="f4")])

    def draw(self, vs, fs, rgba):
        program = self.ctx.program(vertex_shader=vs, fragment_shader=fs)
        if "ColorModulator" in program:
            program["ColorModulator"].value = (1.0, 1.0, 1.0, 1.0)
        corners = ((-1.0, -1.0), (3.0, -1.0), (-1.0, 3.0))
        data = b"".join(struct.pack("6f", x, y, *rgba) for x, y in corners)
        buffer = self.ctx.buffer(data)
        vao = self.ctx.vertex_array(program, [(buffer, "2f 4f", "Pos", "Color")])
        self.fbo.use()
        self.ctx.disable(self.gl.BLEND)
        self.fbo.clear(0.0, 0.0, 0.0, 0.0)
        vao.render(self.gl.TRIANGLES)
        texel = struct.unpack("4f", self.fbo.read(components=4, dtype="f4"))
        vao.release()
        buffer.release()
        program.release()
        return texel


# Tint in, then the colour and alpha the face is drawn with, worked by hand from the contract.
DRAWN = (
    ("level 3", 0x5A63A5, (0x58, 0x68, 0xA8), 3 / 16),
    ("level 15", 0x2A1F35, (0x28, 0x18, 0x38), 15 / 16),
    ("unmarked: red's nibble is not the mark", 0x5B63A5, (0x5B, 0x63, 0xA5), 1.0),
    ("level 0 is no mark", 0x5A60A5, (0x5A, 0x60, 0xA5), 1.0),
    ("the void marker keeps its grey", 0x8001FE, (0x80, 0x80, 0x80), 1.0),
)

MUTANTS = (
    ("item.vsh", "ghostAlpha = level > 0.5 ? level / GHOST_LEVELS : 1.0;", "ghostAlpha = 1.0;"),
    ("item.vsh", "float level = ghost_level(Color);", "float level = 0.0;"),
    ("item.vsh", "tint = vec4(ghost_colour(Color), Color.a);", "tint = Color;"),
    ("item.fsh", "color.a *= ghostAlpha;", ""),
)


class GhostMarkTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.renderer = Renderer()

    def setUp(self):
        self.workspace = tempfile.mkdtemp(prefix="ghostmark-")
        self.addCleanup(shutil.rmtree, self.workspace, True)
        self.tree = os.path.join(self.workspace, "src")
        os.makedirs(self.tree)

    def write(self, relative, definition):
        path = os.path.join(self.tree, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(definition, handle)

    def gate(self, tree=None):
        return subprocess.run([sys.executable, GATE, "--source-tree", tree or self.tree],
                              capture_output=True, text=True)

    def test_the_mark_is_read_exactly(self):
        for level in range(1, LEVELS):
            self.assertTrue(is_ghost_coded(coded(0x8C5A3B, level)), "level %d is a mark" % level)
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 0)), "level 0 draws nothing; never a mark")
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 6) ^ 0x010000), "red's nibble is the mark")
        self.assertFalse(is_ghost_coded(coded(0x8C5A3B, 6) ^ 0x000001), "blue's nibble is the mark")
        self.assertFalse(is_ghost_coded(0xFFFFFF), "an untinted face is not a mark")
        self.assertFalse(is_ghost_coded(void_tint()), "the void marker is not a mark")

    def test_a_shipped_tint_carrying_the_mark_fails(self):
        self.write("assets/legendcraft/items/constant.json",
                   item([{"type": "minecraft:constant", "value": coded(0x404040, 3)}]))
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("assets/legendcraft/items/constant.json", result.stdout)

        os.remove(os.path.join(self.tree, "assets", "legendcraft", "items", "constant.json"))
        self.write("legendcraft_26_2/assets/legendcraft/items/nested/default.json",
                   {"model": {"type": "minecraft:composite", "models": [item(
                       [{"type": "minecraft:custom_model_data", "index": 0,
                         "default": coded(0xFFFFFF, 9)}])["model"]]}})
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("legendcraft_26_2/assets/legendcraft/items/nested/default.json",
                      result.stdout)

        os.remove(os.path.join(self.tree, "legendcraft_26_2", "assets", "legendcraft", "items",
                               "nested", "default.json"))
        rgb = coded(0x202020, 6)
        triple = [((rgb >> shift) & 0xFF) / 255.0 for shift in (16, 8, 0)]
        self.write("assets/legendcraft/items/triple.json",
                   item([{"type": "minecraft:constant", "value": triple}]))
        result = self.gate()
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("assets/legendcraft/items/triple.json", result.stdout)

    def test_a_float_triple_is_read_as_the_game_reads_it(self):
        self.write("assets/legendcraft/items/floored.json",
                   item([{"type": "minecraft:constant", "value": [0.293, 0.263, 0.271]}]))
        result = self.gate()
        self.assertEqual(1, result.returncode, """
            [0.293, 0.263, 0.271] is 0x4A4345 in game, floored: a level-3 mark that rounding \
            misreads as 0x4B4345. """ + result.stdout + result.stderr)
        self.assertIn("4A4345", result.stdout)

        os.remove(os.path.join(self.tree, "assets", "legendcraft", "items", "floored.json"))
        self.write("assets/legendcraft/items/unmarked.json",
                   item([{"type": "minecraft:constant", "value": [0.289, 0.263, 0.271]}]))
        result = self.gate()
        self.assertEqual(0, result.returncode, """
            [0.289, 0.263, 0.271] is 0x494345 in game, no mark; rounding misreads it as the \
            mark 0x4A4345. """ + result.stdout + result.stderr)

    def test_control_unmarked_tints_pass(self):
        self.write("assets/legendcraft/items/plain.json", item([
            {"type": "minecraft:constant", "value": 0xFFFFFF},
            {"type": "minecraft:constant", "value": void_tint()},
            {"type": "minecraft:custom_model_data", "index": 0, "default": 0x8B0000},
            {"type": "minecraft:dye", "default": coded(0x404040, 0)}]))
        result = self.gate()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_the_gate_fails_when_it_checks_nothing(self):
        self.write("assets/legendcraft/items/plain.json",
                   item([{"type": "minecraft:constant", "value": 0xFFFFFF}]))
        self.assertEqual(0, self.gate().returncode, "control: a readable tree passes")

        missing = os.path.join(self.workspace, "no-such-tree")
        result = self.gate(missing)
        self.assertNotEqual(0, result.returncode, "a missing root checked nothing: " + result.stdout)

        a_file = os.path.join(self.workspace, "a-file")
        with open(a_file, "w", encoding="utf-8") as handle:
            handle.write("{}")
        result = self.gate(a_file)
        self.assertNotEqual(0, result.returncode, "a root that is a file: " + result.stdout)

        empty = os.path.join(self.workspace, "empty")
        os.makedirs(empty)
        result = self.gate(empty)
        self.assertNotEqual(0, result.returncode, "a tree with no item definition: " + result.stdout)

        locked = os.path.join(self.tree, "legendcraft_26_2", "assets", "legendcraft", "items")
        os.makedirs(locked)
        os.chmod(locked, 0)
        self.addCleanup(os.chmod, locked, stat.S_IRWXU)
        self.assertFalse(os.access(locked, os.R_OK), "control: the fixture directory is unreadable")
        result = self.gate()
        self.assertNotEqual(0, result.returncode,
                            "an unreadable directory under the root was skipped: " + result.stdout)

    def test_the_covered_item_shaders_draw_the_mark(self):
        for overlay in COVERED_OVERLAYS:
            vertex, fragment = shader_sources(overlay)
            for name, value in (("GHOST_MARK_RED", 10.0), ("GHOST_MARK_BLUE", 5.0),
                                ("GHOST_LEVELS", 16.0)):
                declared = re.search(r"const float %s = ([0-9.]+);" % name, vertex)
                self.assertIsNotNone(declared, "%s item.vsh declares %s" % (overlay, name))
                self.assertEqual(value, float(declared.group(1)), "%s item.vsh: %s" % (overlay, name))
            vs, fs = harness(vertex, fragment)
            for what, tint, colour, alpha in DRAWN:
                drawn = self.renderer.draw(vs, fs, channels(tint) + (1.0,))
                want = tuple(c / 255.0 for c in colour) + (alpha,)
                for got, expected in zip(drawn, want):
                    self.assertAlmostEqual(expected, got, delta=1e-4, msg="%s, %s: drew %s, want %s"
                                           % (overlay, what, drawn, want))

    def test_kill_arm_each_dropped_step_fails_the_shader_arm(self):
        vertex, fragment = shader_sources(COVERED_OVERLAYS[0])
        _what, tint, colour, alpha = DRAWN[0]
        want = tuple(c / 255.0 for c in colour) + (alpha,)
        vs, fs = harness(vertex, fragment)
        drawn = self.renderer.draw(vs, fs, channels(tint) + (1.0,))
        self.assertTrue(all(abs(g - w) < 1e-4 for g, w in zip(drawn, want)),
                        "control: the unmutated shaders draw the level-3 face as expected")
        for shader, original, mutant in MUTANTS:
            self.assertIn(original, vertex if shader == "item.vsh" else fragment,
                          "control: the step the mutant drops is in %s" % shader)
            mutated_vertex = vertex.replace(original, mutant) if shader == "item.vsh" else vertex
            mutated_fragment = (fragment.replace(original, mutant) if shader == "item.fsh"
                                else fragment)
            vs, fs = harness(mutated_vertex, mutated_fragment)
            drawn = self.renderer.draw(vs, fs, channels(tint) + (1.0,))
            self.assertFalse(all(abs(g - w) < 1e-4 for g, w in zip(drawn, want)),
                             "the shader arm passes with %r replaced by %r" % (original, mutant))


if __name__ == "__main__":
    unittest.main()
