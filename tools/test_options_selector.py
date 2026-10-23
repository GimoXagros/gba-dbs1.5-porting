#!/usr/bin/env python3
"""Controlled selector font, native-resource and partial-write boundary checks."""
import struct
import unittest

from build_options_selector import selector_glyphs, text_pixels, branch
from verify_options_selector import decode_layouts, branch_target, failure_model


FONT = b"""STARTFONT 2.1
STARTCHAR A
ENCODING 65
DWIDTH 3 0
BBX 2 2 1 0
BITMAP
C0
40
ENDCHAR
ENDFONT
"""


class SelectorContracts(unittest.TestCase):
    def test_bearing_preserved_and_invalid_glyphs_rejected(self):
        self.assertEqual(selector_glyphs(FONT, {"A"}), {"A": (3, {(1,-2),(2,-2),(2,-1)})})
        for font, chars in ((FONT,{"B"}), (FONT.replace(b"DWIDTH 3",b"DWIDTH 2"),{"A"}),
                            (FONT.replace(b"C0\n40",b"C0"),{"A"}),
                            (FONT.replace(b"C0\n40",b"00\n00"),{"A"})):
            with self.subTest(chars=chars), self.assertRaises(ValueError):
                selector_glyphs(font,chars)

    def test_native_resource_boundary_and_pixel_order(self):
        data=bytearray(0x200)
        struct.pack_into("<II4H",data,0x100,0x08000110,0x0800011C,5,0,0,8)
        struct.pack_into("<II",data,0x110,1,0x08000118)
        struct.pack_into("<Hbb",data,0x118,0,2,1)
        struct.pack_into("<II",data,0x11C,32,0x08000124)
        data[0x124]=0x21
        result,end=decode_layouts(data,0x100,1)
        self.assertEqual((result[0][1],end),({(1,2):1,(2,2):2},0x144))
        for at,value in ((0x118,256),(0x110,0),(0x11C,0)):
            broken=bytearray(data)
            struct.pack_into("<I",broken,at,value)
            with self.subTest(at=at),self.assertRaises(ValueError):
                decode_layouts(broken,0x100,1)

    def test_branch_final_placement_and_invalid_targets(self):
        for destination in (0, 8, 0x633400):
            self.assertEqual(branch_target(branch(0,destination),0),destination)
        for destination in (1,0x2000008,-0x2000000):
            with self.assertRaises(ValueError):
                branch(0,destination)

    def test_all_partial_native_writes_and_repairs(self):
        failure_model()


if __name__=="__main__":
    unittest.main()
