"""Checks for Ee's Wardrobe starter clothes and matching rules."""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps" / "cher-closet" / "app.py"
SPEC = importlib.util.spec_from_file_location("ees_wardrobe", APP_PATH)
WARDROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WARDROBE)


class WardrobeTests(unittest.TestCase):
    def test_starter_wardrobe_has_requested_basics(self):
        self.assertGreaterEqual(len(WARDROBE.DEMO_TOPS), 6)
        self.assertGreaterEqual(len(WARDROBE.DEMO_BOTTOMS), 6)
        self.assertIn("demo:top-black-tee", WARDROBE.DEMO_TOPS)
        self.assertIn("demo:top-white-singlet", WARDROBE.DEMO_TOPS)
        self.assertIn("demo:bottom-blue-jeans", WARDROBE.DEMO_BOTTOMS)

    def test_pixel_face_is_bundled_in_code(self):
        self.assertGreaterEqual(len(WARDROBE.PIXEL_FACE), 16)
        self.assertTrue(any("E" in row for row in WARDROBE.PIXEL_FACE))

    def test_garment_names_are_human_readable(self):
        self.assertEqual(WARDROBE.garment_name("demo:top-black-tee"), "BLACK TEE")
        self.assertEqual(WARDROBE.garment_name("demo:bottom-blue-jeans"), "BLUE JEANS")


if __name__ == "__main__":
    unittest.main()
