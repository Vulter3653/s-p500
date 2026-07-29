import unittest
from scripts.measure_passive_voice import measure_passive


class PassiveTests(unittest.TestCase):
    def test_no_be_participle_substitute_without_parser(self):
        result = measure_passive(["The model was developed."])
        self.assertEqual(result["passive_voice_status"], "blocked_model_missing")
        self.assertIsNone(result["ai_passive_sentence_count"])
