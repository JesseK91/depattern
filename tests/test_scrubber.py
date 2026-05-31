import unittest
from click.testing import CliRunner
from depattern.config import Config
from depattern.cli import cli
from depattern.scrubber import Scrubber

class TestScrubber(unittest.TestCase):
    def setUp(self):
        # Set up default configuration
        self.config = Config()
        self.scrubber = Scrubber(self.config)

    def test_clean_text(self):
        text = "# Title\nThis is a **bold** text with [link](http://example.com)."
        cleaned = self.scrubber.clean_text(text)
        # Verify markdown stripping works correctly
        self.assertEqual(cleaned, "Title\nThis is a bold text with link.")
        
    def test_sentence_segmentation(self):
        text = "This is a sentence. And another! Is this one?"
        sentences = self.scrubber.get_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "This is a sentence.")
        self.assertEqual(sentences[1], "And another!")
        self.assertEqual(sentences[2], "Is this one?")

    def test_analyze_empty(self):
        res = self.scrubber.analyze("")
        self.assertIn("error", res)

    def test_analyze_banned_phrases(self):
        # Text with specific banned terms
        text = "Furthermore, we must delve into solutions to optimize our system in conclusion."
        res = self.scrubber.analyze(text)
        
        found_phrases = [p for p, _ in res["details"]["banned_phrases_found"]]
        self.assertIn("furthermore", found_phrases)
        self.assertIn("delve", found_phrases)
        self.assertIn("in conclusion", found_phrases)

    def test_repeated_openers_add_pattern_risk(self):
        text = (
            "This is the first claim. This is the second claim. This is the third claim. "
            "This is the fourth claim. The customer needs proof before calling."
        )
        res = self.scrubber.analyze(text)
        self.assertGreaterEqual(res["metrics"]["repeated_opener_count"], 3)
        self.assertGreater(res["summary"]["pattern_artifact_score"], 0)

    def test_answer_first_validation(self):
        # Check answer-first score
        # Text starting with a paragraph of 60 words (within 50-80 limit)
        first_para = "This strategy document details how we will optimize your digital storefront to capture local traffic. We focus specifically on removing high-friction lead capture forms, implementing entity-dense schema markup, and establishing a proprietary content moat. By resolving Turbopack compiler errors and deploying on high-speed static networks, your local business will gain a verifiable authority rating."
        sentences = first_para.split()
        self.assertTrue(50 <= len(sentences) <= 80)
        
        res = self.scrubber.analyze(first_para)
        self.assertTrue(res["metrics"]["answer_first_ok"])

    def test_suggest_returns_offline_actions(self):
        text = "Furthermore, this solution will revolutionize the ecosystem. It is important to note that this is highly useful."
        suggestions = self.scrubber.suggest(text)
        titles = [item["title"] for item in suggestions]
        self.assertIn("Replace formulaic transition language", titles)
        self.assertIn("Remove vague intensifiers", titles)

    def test_cli_max_risk_fails_when_threshold_exceeded(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("draft.md", "w", encoding="utf-8") as f:
                f.write("Furthermore, we must delve into this cutting-edge ecosystem. In conclusion, this is highly important.")

            result = runner.invoke(cli, ["analyze", "draft.md", "--max-risk", "low"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("exceeds --max-risk", result.output)

if __name__ == '__main__':
    unittest.main()
