import os
import re
from depattern.config import Config
from depattern.providers import BaseProvider
from depattern.schema import SchemaGenerator

class Exporter:
    def __init__(self, config: Config, provider: BaseProvider = None):
        self.config = config
        self.provider = provider
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")

    def _read_prompt(self, filename):
        path = os.path.join(self.prompts_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required prompt file missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_slides(self, text: str) -> str:
        # Check if provider is available for LLM slide design
        if self.provider:
            try:
                slides_prompt = self._read_prompt("slides.md")
                # Remove YAML frontmatter before sending to LLM for layout
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        text = parts[2].strip()
                        
                system_instruction = slides_prompt + f"\n\nContext: Brand name is {self.config.brand_name}"
                return self.provider.generate(text, system_instruction=system_instruction)
            except Exception as e:
                print(f"Warning: LLM slide generation failed, falling back to offline compiler. Error: {e}")

        # Fallback to local programmatic markdown slide compiler
        return self._compile_slides_offline(text)

    def _compile_slides_offline(self, text: str) -> str:
        schema_gen = SchemaGenerator()
        metadata = schema_gen.parse_metadata(text)
        
        # Strip frontmatter
        content = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        # Build Marp configuration header
        slides = []
        slides.append(
            "---\n"
            "marp: true\n"
            "theme: default\n"
            "paginate: true\n"
            f"header: {self.config.brand_name}\n"
            "footer: Confidential Strategy Deck\n"
            "---"
        )

        # Slide 1: Cover Slide
        title = metadata.get("title") or "Business Optimization Strategy"
        description = metadata.get("description") or "Local SEO and Authority Audits"
        author = metadata.get("author") or "Agency Staff"
        org = metadata.get("organization") or self.config.brand_name
        
        cover = (
            f"# {title}\n\n"
            f"**{description}**\n\n"
            f"Prepared by: {author}\n"
            f"For: {org}"
        )
        slides.append(cover)

        # Parse sections based on header matching
        sections = re.split(r'\n(?=#+\s+)', content)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            lines = section.splitlines()
            header_line = lines[0]
            header_text = re.sub(r'^#+\s+', '', header_line).strip()
            
            # Skip high level title headers if they duplicate cover
            if header_line.startswith("# ") and title.lower() in header_text.lower():
                continue
                
            body_lines = lines[1:]
            body_paragraphs = []
            current_para = []
            
            for line in body_lines:
                line_strip = line.strip()
                if not line_strip:
                    if current_para:
                        body_paragraphs.append(" ".join(current_para))
                        current_para = []
                else:
                    current_para.append(line_strip)
            if current_para:
                body_paragraphs.append(" ".join(current_para))
                
            # Construct bullet points from body content
            bullets = []
            for para in body_paragraphs[:4]: # Limit to first 4 points to avoid overflow
                if para.startswith("-") or para.startswith("*"):
                    # Existing bullet point
                    bullets.append(para)
                else:
                    # Convert paragraph to brief summary bullet
                    # Split sentences and take the first one or two
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    summary = sentences[0]
                    if len(summary) > 100:
                        summary = summary[:97] + "..."
                    bullets.append(f"- {summary}")
                    
            if bullets:
                slide_content = f"## {header_text}\n\n" + "\n\n".join(bullets)
                slides.append(slide_content)

        return "\n\n---\n\n".join(slides)
