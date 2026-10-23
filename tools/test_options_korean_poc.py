#!/usr/bin/env python3
"""Small controlled checks for BDF boundaries and native 4bpp ordering."""
import unittest

from build_options_korean_poc import font_glyphs, pack_tile, text_pixels


FONT = b"""STARTFONT 2.1
STARTCHAR A
ENCODING 65
DWIDTH 3 0
BBX 2 2 0 0
BITMAP
C0
40
ENDCHAR
STARTCHAR SPACE
ENCODING 32
DWIDTH 3 0
BBX 0 0 0 0
BITMAP
ENDCHAR
ENDFONT
"""


class NativeFontTests(unittest.TestCase):
    def test_bdf_msb_padding_and_baseline(self):
        glyphs = font_glyphs(FONT, {"A", " "})
        self.assertEqual(glyphs["A"], (3, {(0, -2), (1, -2), (1, -1)}))
        image, width = text_pixels("A A", glyphs)
        self.assertEqual(width, 10)
        self.assertEqual({point for point, color in image.items() if color == 1},
                         {(1, -2), (2, -2), (2, -1), (7, -2), (8, -2), (8, -1)})
        self.assertEqual(image[0, -3], 2)
        self.assertNotIn((5, -2), image)

    def test_missing_empty_and_truncated_input_fail(self):
        for font, characters in ((FONT, {"B"}), (FONT.replace(b"C0\n40", b"C0"), {"A"}),
                                 (FONT.replace(b"C0\n40", b"00\n00"), {"A"})):
            with self.subTest(characters=characters), self.assertRaises(ValueError):
                font_glyphs(font, characters)
        with self.assertRaises(ValueError):
            text_pixels("B", font_glyphs(FONT, {"A"}))
        with self.assertRaises(ValueError):
            text_pixels(" ", font_glyphs(FONT, {" "}))

    def test_native_low_nibble_is_left_pixel(self):
        tile = pack_tile({(3, -4): 1, (4, -4): 2, (10, 3): 15}, 3, -4)
        self.assertEqual(tile, bytes([0x21]) + bytes(30) + bytes([0xF0]))


if __name__ == "__main__":
    unittest.main()
