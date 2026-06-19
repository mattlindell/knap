from typing import Optional

from llm.base import LLMProvider, post_json


class OllamaProvider(LLMProvider):
    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    def summarize(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        timeout: float = 300.0,
        max_retries: int = 1,
    ) -> Optional[str]:
        options: dict = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if system:
            payload["system"] = system

        data = post_json(
            f"{self.base_url}/api/generate",
            payload,
            timeout=timeout,
            max_retries=max_retries,
        )
        if not data:
            return None
        return data.get("response")
