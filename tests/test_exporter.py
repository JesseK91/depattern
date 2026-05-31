import unittest
from depattern.config import Config
from depattern.exporter import Exporter

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.exporter = Exporter(self.config)

    def test_offline_slide_generation(self):
        text = (
            "---\n"
            "title: Canna Cure Growth Audit\n"
            "description: Operational and Local SEO Overhaul\n"
            "author: Jesse\n"
            "organization: Canna Cure\n"
            "---\n"
            "\n"
            "# Operational Bottlenecks\n"
            "The storefront portal faces high latency. Next.js Turbopack scanning took longer because of stray parent files. This led to slower client page loads.\n"
            "\n"
            "# Search Engine Authority\n"
            "The storefront lacks local schema markup. Search engines in 2026 penalize pages without verifiable entity definitions."
        )
        
        slides = self.exporter.generate_slides(text)
        
        # Verify Marp frontmatter structure
        self.assertIn("marp: true", slides)
        self.assertIn("theme: default", slides)
        
        # Verify metadata is translated into cover slide
        self.assertIn("Canna Cure Growth Audit", slides)
        self.assertIn("Prepared by: Jesse", slides)
        self.assertIn("For: Canna Cure", slides)
        
        # Verify sections are compiled as separate slides
        self.assertIn("## Operational Bottlenecks", slides)
        self.assertIn("## Search Engine Authority", slides)
        
        # Verify paragraph conversion to bullet points
        self.assertIn("- The storefront portal faces high latency.", slides)
