from abc import ABC, abstractmethod
from typing import Protocol


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:  # pragma: no cover - interface only
        ...


class TransformationEngine:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def generate_diff(self, prompt: str) -> str:
        response = self.client.generate(prompt)
        if not isinstance(response, str):
            raise TypeError("LLM response must be string containing unified diff")
        return response.strip()


class EchoLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
