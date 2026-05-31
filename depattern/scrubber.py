import re
import math
from depattern.config import Config

class Scrubber:
    def __init__(self, config: Config):
        self.config = config
        
    def clean_text(self, text):
        # Remove markdown symbols for statistical analysis
        text = re.sub(r'#+\s+', '', text)
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        return text

    def get_sentences(self, text):
        cleaned = self.clean_text(text)
        # Split sentences by period, question mark, or exclamation mark followed by whitespace
        raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        return sentences

    def get_paragraphs(self, text):
        # Paragraphs are separated by double newlines or single newlines with blank space
        raw_paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in raw_paragraphs if p.strip()]

    def get_content_paragraphs(self, text):
        """Return content paragraphs, ignoring markdown frontmatter and headings."""
        content = text
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        paragraphs = []
        for paragraph in self.get_paragraphs(content):
            stripped = paragraph.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if stripped.startswith("---"):
                continue
            if stripped.lower().startswith(("marp:", "theme:", "paginate:", "header:", "footer:")):
                continue
            paragraphs.append(stripped)
        return paragraphs

    def count_words(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    def analyze(self, text):
        sentences = self.get_sentences(text)
        paragraphs = self.get_paragraphs(text)
        words = self.count_words(text)
        
        total_words = len(words)
        total_sentences = len(sentences)
        total_paragraphs = len(paragraphs)
        
        if total_words == 0:
            return {"error": "Text contains no words."}

        # 1. Sentence length variance (standard deviation)
        sentence_word_counts = [len(self.count_words(s)) for s in sentences]
        if total_sentences > 1:
            mean_sentence_len = sum(sentence_word_counts) / total_sentences
            sentence_variance = sum((x - mean_sentence_len) ** 2 for x in sentence_word_counts) / (total_sentences - 1)
            sentence_std_dev = math.sqrt(sentence_variance)
        else:
            mean_sentence_len = total_words
            sentence_std_dev = 0.0

        # 2. Paragraph rhythm
        paragraph_word_counts = [len(self.count_words(p)) for p in paragraphs]
        if total_paragraphs > 1:
            mean_paragraph_len = sum(paragraph_word_counts) / total_paragraphs
            paragraph_std_dev = math.sqrt(
                sum((x - mean_paragraph_len) ** 2 for x in paragraph_word_counts) / (total_paragraphs - 1)
            )
        else:
            mean_paragraph_len = total_words
            paragraph_std_dev = 0.0

        # 3. Banned transition density
        banned_matches = []
        text_lower = text.lower()
        for phrase in self.config.banned_phrases:
            # Match phrase with word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(phrase.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                banned_matches.append((phrase, len(matches)))
                
        total_banned = sum(count for _, count in banned_matches)
        banned_density = total_banned / total_words

        # 4. Vague intensifiers
        intensifier_matches = []
        for intensifier in self.config.vague_intensifiers:
            pattern = r'\b' + re.escape(intensifier.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                intensifier_matches.append((intensifier, len(matches)))
        total_intensifiers = sum(count for _, count in intensifier_matches)

        # 5. Abstract nouns
        abstract_matches = []
        for noun in self.config.abstract_nouns:
            pattern = r'\b' + re.escape(noun.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                abstract_matches.append((noun, len(matches)))
        total_abstract = sum(count for _, count in abstract_matches)
        abstract_density = total_abstract / total_words

        # 6. Repeated sentence openers
        openers = {}
        for s in sentences:
            s_words = self.count_words(s)
            if len(s_words) >= 2:
                opener = " ".join(s_words[:2])
                openers[opener] = openers.get(opener, 0) + 1
        repeated_openers = {k: v for k, v in openers.items() if v > 1}

        # 7. Answer-first score
        # Checks if the first real content paragraph matches AEO sizing.
        non_header_paras = self.get_content_paragraphs(text)
        answer_first_words = 0
        answer_first_ok = False
        if non_header_paras:
            first_para = non_header_paras[0]
            first_para_word_count = len(self.count_words(first_para))
            answer_first_words = first_para_word_count
            if (self.config.answer_first_word_count_min <= first_para_word_count <= 
                    self.config.answer_first_word_count_max):
                # Ensure it doesn't start with banned phrases
                has_banned_lead = any(first_para.lower().startswith(p) for p in self.config.banned_phrases)
                if not has_banned_lead:
                    answer_first_ok = True

        # 8. Pattern risk score calculation.
        # Low variance, banned transitions, repeated openers, and abstract filler all add risk.
        risk_score = 0
        
        # Sentence variance penalty (lower variance = higher risk)
        if sentence_std_dev < 6.0:
            risk_score += 3
        elif sentence_std_dev < 10.0:
            risk_score += 2
            
        # Banned transitions penalty
        if total_banned >= 8 or banned_density > 0.03:
            risk_score += 3
        elif total_banned >= 5:
            risk_score += 2
        elif total_banned >= 3 or banned_density > 0.01:
            risk_score += 1
            
        # Abstract nouns penalty
        if total_abstract >= 8 or abstract_density > 0.04:
            risk_score += 2
        elif total_abstract >= 5 or abstract_density > 0.02:
            risk_score += 1
            
        # Intensifiers penalty
        if total_intensifiers > 5:
            risk_score += 1

        # Repeated opener penalty. Cap to avoid penalizing long notes too harshly.
        repeated_openers_count = sum(v - 1 for v in repeated_openers.values())
        repeated_opener_density = repeated_openers_count / total_sentences if total_sentences else 0
        if repeated_openers_count >= 8 and repeated_opener_density >= 0.08:
            risk_score += 2
        elif repeated_openers_count >= 3 and repeated_opener_density >= 0.05:
            risk_score += 1

        if risk_score >= 6:
            slop_risk = "HIGH"
        elif risk_score >= 3:
            slop_risk = "MEDIUM"
        else:
            slop_risk = "LOW"

        return {
            "summary": {
                "total_words": total_words,
                "total_sentences": total_sentences,
                "total_paragraphs": total_paragraphs,
                "slop_risk": slop_risk,
                "pattern_artifact_score": risk_score # Out of 9 max
            },
            "metrics": {
                "sentence_length_variance": round(sentence_std_dev, 2),
                "paragraph_rhythm_variance": round(paragraph_std_dev, 2),
                "banned_transition_density": round(banned_density, 4),
                "abstract_noun_density": round(abstract_density, 4),
                "vague_intensifier_count": total_intensifiers,
                "answer_first_ok": answer_first_ok,
                "answer_first_words": answer_first_words,
                "repeated_opener_count": repeated_openers_count,
                "repeated_opener_density": round(repeated_opener_density, 4)
            },
            "details": {
                "banned_phrases_found": banned_matches,
                "vague_intensifiers_found": intensifier_matches,
                "abstract_nouns_found": abstract_matches,
                "repeated_openers": repeated_openers
            }
        }

    def suggest(self, text):
        """Generate offline editorial suggestions from analyzer findings."""
        res = self.analyze(text)
        if "error" in res:
            return []

        suggestions = []
        metrics = res["metrics"]
        details = res["details"]

        if details["banned_phrases_found"]:
            phrases = ", ".join(f"{phrase} ({count})" for phrase, count in details["banned_phrases_found"][:8])
            suggestions.append({
                "severity": "high",
                "title": "Replace formulaic transition language",
                "detail": f"Found: {phrases}. Cut the transition or replace it with a concrete claim."
            })

        if details["abstract_nouns_found"]:
            nouns = ", ".join(f"{noun} ({count})" for noun, count in details["abstract_nouns_found"][:8])
            suggestions.append({
                "severity": "medium",
                "title": "Trade abstract nouns for visible actions",
                "detail": f"Found: {nouns}. Name the actual tool, action, result, or decision instead."
            })

        if metrics["sentence_length_variance"] < self.config.sentence_length_variance_threshold:
            suggestions.append({
                "severity": "medium",
                "title": "Vary sentence rhythm",
                "detail": "The draft has a flat sentence pattern. Mix short assertions with longer explanatory sentences."
            })

        if metrics["repeated_opener_count"] >= 3:
            openers = ", ".join(f"{opener} ({count})" for opener, count in list(details["repeated_openers"].items())[:8])
            suggestions.append({
                "severity": "medium",
                "title": "Break repeated sentence openings",
                "detail": f"Repeated openers: {openers}. Recast some sentences so the rhythm feels less templated."
            })

        if metrics["vague_intensifier_count"] > 0:
            intensifiers = ", ".join(f"{word} ({count})" for word, count in details["vague_intensifiers_found"][:8])
            suggestions.append({
                "severity": "low",
                "title": "Remove vague intensifiers",
                "detail": f"Found: {intensifiers}. Replace intensity with evidence, numbers, or a sharper noun."
            })

        if not metrics["answer_first_ok"]:
            suggestions.append({
                "severity": "medium",
                "title": "Add an answer-first opening",
                "detail": f"First content paragraph is {metrics['answer_first_words']} words. Aim for {self.config.answer_first_word_count_min}-{self.config.answer_first_word_count_max} words that answer the main question directly."
            })

        if not suggestions:
            suggestions.append({
                "severity": "low",
                "title": "No major pattern artifacts found",
                "detail": "The draft has varied rhythm and low formulaic language density. Focus edits on specificity and proof."
            })

        return suggestions
