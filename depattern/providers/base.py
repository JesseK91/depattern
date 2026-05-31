class BaseProvider:
    def generate(self, prompt: str, system_instruction: str = None) -> str:
        """
        Sends a prompt to the LLM provider and returns the raw text response.
        """
        raise NotImplementedError("Providers must implement the generate method.")
