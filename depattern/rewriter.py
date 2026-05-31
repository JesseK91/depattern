import os
import difflib
from depattern.config import Config
from depattern.providers import BaseProvider

class Rewriter:
    def __init__(self, config: Config, provider: BaseProvider):
        self.config = config
        self.provider = provider
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
        
    def _read_prompt(self, filename):
        path = os.path.join(self.prompts_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required prompt file missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def split_frontmatter(self, text):
        frontmatter = ""
        content = text
        
        # Check if text starts with YAML frontmatter markers
        if text.startswith("---"):
            # Split by frontmatter boundary
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = "---" + parts[1] + "---\n\n"
                content = parts[2].strip()
        return frontmatter, content

    def process(self, text: str, voice: str = None, answer_first: bool = False) -> str:
        frontmatter, content = self.split_frontmatter(text)
        
        # 1. Load the deslop system prompt
        deslop_prompt = self._read_prompt("deslop.md")
        
        # Override brand voice if explicitly specified
        active_voice = voice if voice else self.config.brand_voice
        voice_instruction = f"\n\nActive Brand Voice Guidelines:\n- Name: {self.config.brand_name}\n- Style: {active_voice}"
        system_instruction = deslop_prompt + voice_instruction
        
        # First rewrite pass (de-patterning & slop scrubbing)
        rewritten_content = self.provider.generate(content, system_instruction=system_instruction)
        
        # 2. Answer-first pass (optional)
        if answer_first:
            answer_first_prompt = self._read_prompt("answer_first.md")
            rewritten_content = self.provider.generate(
                rewritten_content, 
                system_instruction=answer_first_prompt
            )
            
        # Re-attach frontmatter
        return frontmatter + rewritten_content.strip()

    def get_diff(self, old_text: str, new_text: str) -> str:
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        diff = difflib.unified_diff(
            old_lines, 
            new_lines, 
            fromfile="Original Draft", 
            tofile="Polished Output", 
            lineterm=""
        )
        
        colorized = []
        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                # Green
                colorized.append(f"\033[92m{line}\033[0m")
            elif line.startswith("-") and not line.startswith("---"):
                # Red
                colorized.append(f"\033[91m{line}\033[0m")
            elif line.startswith("@@"):
                # Cyan
                colorized.append(f"\033[36m{line}\033[0m")
            else:
                colorized.append(line)
                
        return "\n".join(colorized)
