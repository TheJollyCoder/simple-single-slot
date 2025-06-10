import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logging
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

import breeding_logic


class ShouldKeepEggTests(TestCase):
    def setUp(self):
        self.keep_stream = StringIO()
        self.destroy_stream = StringIO()
        for logger, stream in [
            (breeding_logic.kept_log, self.keep_stream),
            (breeding_logic.destroyed_log, self.destroy_stream),
        ]:
            logger.handlers.clear()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def tearDown(self):
        breeding_logic.kept_log.handlers.clear()
        breeding_logic.destroyed_log.handlers.clear()

    def test_mutations_keep(self):
        scan = {"egg": "CS Test Male", "sex": "male", "stats": {"melee": {"mutation": 3}}}
        rules = {"modes": ["mutations"], "mutation_stats": ["melee"]}
        progress = {"TestDino": {"mutation_thresholds": {"melee": 2}}}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["mutations"])
        self.assertIn("KEPT", self.keep_stream.getvalue())
        self.assertEqual("", self.destroy_stream.getvalue())

    def test_mutations_keep_better_base_same_mut(self):
        scan = {
            "egg": "CS Test Male",
            "sex": "male",
            "stats": {"melee": {"mutation": 2, "base": 6}},
        }
        rules = {"modes": ["mutations"], "mutation_stats": ["melee"]}
        progress = {
            "TestDino": {
                "mutation_thresholds": {"melee": 2},
                "mutation_stud": {"melee": 5},
            }
        }
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["mutations"])
        self.assertIn("KEPT", self.keep_stream.getvalue())

    def test_all_females_keep(self):
        scan = {"egg": "CS Test Female", "sex": "female", "stats": {}}
        rules = {"modes": ["all_females"]}
        progress = {}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["all_females"])
        self.assertIn("KEPT", self.keep_stream.getvalue())

    def test_stat_merge_keep(self):
        scan = {"egg": "CS Test Male", "sex": "male", "stats": {}, "updated_stud": True}
        rules = {"modes": ["stat_merge"], "stat_merge_stats": ["melee"]}
        progress = {}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["stat_merge"])
        self.assertIn("KEPT", self.keep_stream.getvalue())

    def test_top_stat_females_keep(self):
        scan = {
            "egg": "CS Test Female",
            "sex": "female",
            "stats": {"health": {"base": 10}},
        }
        rules = {"modes": ["top_stat_females"], "top_stat_females_stats": ["health"]}
        progress = {"TestDino": {"top_stats": {"health": 10}}}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["top_stat_females"])
        self.assertIn("KEPT", self.keep_stream.getvalue())

    def test_war_keep(self):
        scan = {
            "egg": "CS Test Male",
            "sex": "male",
            "stats": {"melee": {"base": 5, "mutation": 1}},
        }
        rules = {"modes": ["war"], "war_stats": ["melee"]}
        progress = {"TestDino": {"top_stats": {"melee": 5}}}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "keep")
        self.assertTrue(res["war"])
        self.assertIn("KEPT", self.keep_stream.getvalue())

    def test_auto_destroy_female_without_modes(self):
        scan = {"egg": "CS Test Female", "sex": "female", "stats": {}}
        rules = {"modes": ["mutations"], "mutation_stats": ["melee"]}
        progress = {}
        with patch("breeding_logic.normalize_species_name", return_value="TestDino"):
            decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "destroy")
        self.assertFalse(any(res[m] for m in [
            "mutations", "all_females", "stat_merge", "top_stat_females", "war"]))
        self.assertIn("DESTROYED", self.destroy_stream.getvalue())

    def test_invalid_species_triggers_rescan(self):
        scan = {"egg": "Bad Read", "sex": "male", "stats": {}}
        rules = {"modes": ["mutations"]}
        progress = {}
        decision, res = breeding_logic.should_keep_egg(scan, rules, progress)
        self.assertEqual(decision, "rescan")
        self.assertEqual(res["_debug"]["final"], "rescan")
