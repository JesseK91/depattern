import os
import toml
import copy

DEFAULT_CONFIG = {
    "brand": {
        "name": "580 Digital Infrastructure",
        "voice": "direct, specific, local, no hype, active voice, short paragraphs"
    },
    "llm": {
        "provider": "gemini",
        "model": "gemini-2.5-flash"
    },
    "rules": {
        "banned_phrases": [
            "furthermore", "in conclusion", "moreover", "it is important to note",
            "delve", "tapestry", "beacon", "testament", "game-changer",
            "seamless", "unlocked", "not only", "journey", "elevate",
            "revolutionize", "cutting-edge"
        ],
        "vague_intensifiers": [
            "very", "extremely", "incredibly", "highly", "significantly",
            "absolutely", "totally"
        ],
        "abstract_nouns": [
            "synergy", "solutions", "paradigm", "ecosystem", "alignment",
            "optimization", "innovation"
        ],
        "sentence_length_variance_threshold": 12.0,
        "banned_transition_density_threshold": 0.02,
        "answer_first_word_count_min": 50,
        "answer_first_word_count_max": 80
    }
}

class Config:
    def __init__(self, config_path=None):
        self.data = copy.deepcopy(DEFAULT_CONFIG)
        
        # Search path order: explicit path -> current directory -> user home directory
        search_paths = []
        if config_path:
            search_paths.append(config_path)
        else:
            search_paths.append(os.path.join(os.getcwd(), "depattern.toml"))
            search_paths.append(os.path.expanduser("~/depattern.toml"))
            
        for path in search_paths:
            if os.path.exists(path):
                try:
                    loaded = toml.load(path)
                    self._merge(self.data, loaded)
                    break
                except Exception as e:
                    print(f"Warning: Failed to load config from {path}: {e}")
                    
    def _merge(self, base, override):
        for key, val in override.items():
            if isinstance(val, dict) and key in base and isinstance(base[key], dict):
                self._merge(base[key], val)
            else:
                base[key] = val
                
    @property
    def brand_name(self):
        return self.data["brand"]["name"]
        
    @property
    def brand_voice(self):
        return self.data["brand"]["voice"]
        
    @property
    def llm_provider(self):
        return self.data["llm"]["provider"]
        
    @property
    def llm_model(self):
        return self.data["llm"]["model"]
        
    @property
    def banned_phrases(self):
        return self.data["rules"]["banned_phrases"]
        
    @property
    def vague_intensifiers(self):
        return self.data["rules"]["vague_intensifiers"]
        
    @property
    def abstract_nouns(self):
        return self.data["rules"]["abstract_nouns"]
        
    @property
    def sentence_length_variance_threshold(self):
        return float(self.data["rules"]["sentence_length_variance_threshold"])
        
    @property
    def banned_transition_density_threshold(self):
        return float(self.data["rules"]["banned_transition_density_threshold"])
        
    @property
    def answer_first_word_count_min(self):
        return int(self.data["rules"]["answer_first_word_count_min"])
        
    @property
    def answer_first_word_count_max(self):
        return int(self.data["rules"]["answer_first_word_count_max"])
