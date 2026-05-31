import unittest
from depattern.schema import SchemaGenerator

class TestSchema(unittest.TestCase):
    def setUp(self):
        self.generator = SchemaGenerator()

    def test_parse_metadata(self):
        text = (
            "---\n"
            "title: 'Canna Cure Strategy'\n"
            "author: Jesse\n"
            "organization: 580 Digital Infrastructure\n"
            "---\n"
            "Document content here."
        )
        meta = self.generator.parse_metadata(text)
        self.assertEqual(meta.get("title"), "Canna Cure Strategy")
        self.assertEqual(meta.get("author"), "Jesse")
        self.assertEqual(meta.get("organization"), "580 Digital Infrastructure")

    def test_extract_faqs_markdown(self):
        text = (
            "## Frequently Asked Questions\n\n"
            "### Q: What are the weekend hours?\n"
            "The storefront is closed on Sundays. Saturday hours are 9:00 AM to 9:00 PM.\n\n"
            "### How do I redeem deals?\n"
            "Present this screen to your budtender in person to redeem any special deals."
        )
        faqs = self.generator.extract_faqs(text)
        self.assertEqual(len(faqs), 2)
        self.assertEqual(faqs[0][0], "What are the weekend hours?")
        self.assertEqual(faqs[0][1], "The storefront is closed on Sundays. Saturday hours are 9:00 AM to 9:00 PM.")
        self.assertEqual(faqs[1][0], "How do I redeem deals?")
        self.assertEqual(faqs[1][1], "Present this screen to your budtender in person to redeem any special deals.")

    def test_generate_local_business(self):
        text = (
            "---\n"
            "organization: Sugar Shack\n"
            "organization_url: https://sugarshack.example.com\n"
            "same_as: https://twitter.com/sugarshack, https://facebook.com/sugarshack\n"
            "description: Organic dispensary in Lawton.\n"
            "---\n"
            "Content"
        )
        schema = self.generator.generate(text, "LocalBusiness")
        self.assertEqual(schema["@type"], "LocalBusiness")
        self.assertEqual(schema["name"], "Sugar Shack")
        self.assertEqual(schema["url"], "https://sugarshack.example.com")
        self.assertEqual(schema["description"], "Organic dispensary in Lawton.")
        self.assertEqual(len(schema["sameAs"]), 2)

if __name__ == '__main__':
    unittest.main()
