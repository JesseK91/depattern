import json
import re

class SchemaGenerator:
    def __init__(self):
        pass

    def parse_metadata(self, text):
        metadata = {}
        # Parse YAML frontmatter if it exists
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                yaml_block = parts[1]
                for line in yaml_block.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        # Strip strings and clean up quotes
                        metadata[k.strip().lower()] = v.strip().strip('"').strip("'")
        return metadata

    def extract_faqs(self, text):
        # Look for headings containing a question mark or starting with Q:, and take the following paragraph as answer
        faqs = []
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            # Check for header indicator
            if line.startswith("##") or line.startswith("###"):
                header_text = re.sub(r'^#+\s+', '', line).strip()
                # Check if it looks like a question
                if header_text.endswith("?") or header_text.lower().startswith("q:"):
                    question = header_text
                    if header_text.lower().startswith("q:"):
                        question = question[2:].strip()
                        
                    # Find subsequent paragraph as answer
                    answer_lines = []
                    for next_line in lines[idx + 1:]:
                        if next_line.startswith("#"):
                            break # Reached next header
                        if next_line.strip():
                            answer_lines.append(next_line.strip())
                        elif answer_lines:
                            break # Empty line after content
                            
                    if answer_lines:
                        answer = " ".join(answer_lines)
                        faqs.append((question, answer))
        return faqs

    def generate(self, text: str, schema_type: str) -> dict:
        metadata = self.parse_metadata(text)
        
        # Build base context
        schema = {
            "@context": "https://schema.org"
        }
        
        type_lower = schema_type.lower()
        
        if type_lower == "localbusiness":
            schema["@type"] = "LocalBusiness"
            schema["name"] = metadata.get("organization") or metadata.get("title") or "Unnamed Local Business"
            schema["description"] = metadata.get("description") or "Local Business Profile"
            if "url" in metadata:
                schema["url"] = metadata["url"]
            elif "organization_url" in metadata:
                schema["url"] = metadata["organization_url"]
                
            if "area_served" in metadata:
                schema["areaServed"] = [a.strip() for a in metadata["area_served"].split(",")]
            if "same_as" in metadata:
                schema["sameAs"] = [s.strip() for s in metadata["same_as"].split(",")]
                
        elif type_lower == "person":
            schema["@type"] = "Person"
            schema["name"] = metadata.get("author") or "Unnamed Author"
            if "author_url" in metadata:
                schema["url"] = metadata["author_url"]
            if "same_as" in metadata:
                schema["sameAs"] = [s.strip() for s in metadata["same_as"].split(",")]
                
        elif type_lower == "article":
            schema["@type"] = "Article"
            schema["headline"] = metadata.get("title") or "Untitled Article"
            schema["description"] = metadata.get("description") or ""
            
            author_name = metadata.get("author") or "Staff"
            schema["author"] = {
                "@type": "Person",
                "name": author_name
            }
            if "author_url" in metadata:
                schema["author"]["url"] = metadata["author_url"]
                
            org_name = metadata.get("organization") or "Agency Client"
            schema["publisher"] = {
                "@type": "Organization",
                "name": org_name
            }
            if "organization_url" in metadata:
                schema["publisher"]["url"] = metadata["organization_url"]
                
        elif type_lower == "faqpage":
            schema["@type"] = "FAQPage"
            faqs = self.extract_faqs(text)
            main_entities = []
            for question, answer in faqs:
                main_entities.append({
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": answer
                    }
                })
            schema["mainEntity"] = main_entities
            
        else:
            # Generic fallback schema
            schema["@type"] = schema_type
            for k, v in metadata.items():
                schema[k] = v
                
        return schema
