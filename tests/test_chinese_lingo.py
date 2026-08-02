#!/usr/bin/env python3

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT.parent / "apps" / "chinese-lingo"
SPEC = importlib.util.spec_from_file_location("chinese_lingo_app", APP_DIR / "app.py")
HANZI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HANZI)


class AssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (APP_DIR / "hanzi_assets.json").open(encoding="utf-8") as handle:
            cls.bundle = json.load(handle)

    def test_starter_course_has_twenty_unique_characters(self):
        course_chars = [
            char
            for level in self.bundle["course"]
            for char, _ in level["characters"]
        ]
        self.assertEqual(20, len(course_chars))
        self.assertEqual(20, len(set(course_chars)))
        self.assertEqual(set(course_chars), set(self.bundle["characters"]))

    def test_every_stroke_has_a_matching_median_and_valid_spans(self):
        size = self.bundle["asset_size"]
        for char, data in self.bundle["characters"].items():
            self.assertEqual(len(data["strokes"]), len(data["medians"]), char)
            self.assertGreater(len(data["strokes"]), 0, char)
            for spans in data["strokes"]:
                self.assertGreater(len(spans), 0, char)
                for y, x1, x2 in spans:
                    self.assertTrue(0 <= y < size, (char, y))
                    self.assertTrue(0 <= x1 < x2 <= size, (char, x1, x2))


class StrokeGradingTests(unittest.TestCase):
    def setUp(self):
        with (APP_DIR / "hanzi_assets.json").open(encoding="utf-8") as handle:
            self.bundle = json.load(handle)
        self.target = self.bundle["characters"]["你"]["medians"][0]

    def test_exact_stroke_passes(self):
        passed, _ = HANZI.grade_stroke(self.target, self.target)
        self.assertTrue(passed)

    def test_reversed_stroke_fails(self):
        passed, _ = HANZI.grade_stroke(list(reversed(self.target)), self.target)
        self.assertFalse(passed)

    def test_shifted_stroke_fails(self):
        shifted = [(x + 90, y + 70) for x, y in self.target]
        passed, _ = HANZI.grade_stroke(shifted, self.target)
        self.assertFalse(passed)

    def test_reasonable_stylus_jitter_passes(self):
        jittered = [
            (x + (2 if index % 2 else -2), y + (1 if index % 3 else -1))
            for index, (x, y) in enumerate(self.target)
        ]
        passed, _ = HANZI.grade_stroke(jittered, self.target)
        self.assertTrue(passed)

    def test_guided_mode_accepts_an_imperfect_mouth_corner(self):
        target = self.bundle["characters"]["口"]["medians"][1]
        stylus_path = [(62, 71), (116, 69), (184, 75), (181, 132), (180, 178)]
        normal, _ = HANZI.grade_stroke(stylus_path, target)
        guided, _ = HANZI.grade_stroke(stylus_path, target, forgiving=True)
        self.assertFalse(normal)
        self.assertTrue(guided)

    def test_guided_mode_does_not_require_exact_mouth_endpoint(self):
        target = self.bundle["characters"]["口"]["medians"][1]
        stylus_path = [(70, 76), (118, 73), (181, 78), (181, 115)]
        passed, _ = HANZI.grade_stroke(stylus_path, target, forgiving=True)
        self.assertTrue(passed)

    def test_guided_mode_still_rejects_wrong_direction(self):
        passed, _ = HANZI.grade_stroke(
            list(reversed(self.target)), self.target, forgiving=True
        )
        self.assertFalse(passed)


class ProgressTests(unittest.TestCase):
    def test_finishing_level_unlocks_next_level(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "progress.json")
            progress = HANZI.Progress(path, 5)
            for char in "一二三十":
                progress.complete_character(0, "first_strokes", char)
            self.assertEqual(1, progress.data["unlocked"])
            self.assertEqual(40, progress.data["xp"])
            reloaded = HANZI.Progress(path, 5)
            self.assertEqual(1, reloaded.data["unlocked"])
            self.assertEqual(4, reloaded.level_score("first_strokes"))


if __name__ == "__main__":
    unittest.main()
