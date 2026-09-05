import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from bilingual import bilingual_block


class BilingualTests(unittest.TestCase):
    def test_places_chinese_translation_before_english_original(self):
        result = bilingual_block("中文标题", "English headline", "中文摘要", "English summary")
        self.assertEqual(
            result,
            "中文：中文标题\nEnglish: English headline\n中文摘要：中文摘要\nEnglish summary：English summary",
        )


if __name__ == "__main__":
    unittest.main()
