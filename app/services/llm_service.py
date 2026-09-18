"""Ollama/Qwen client isolated from the RAG workflow."""

from typing import Any
import re

import httpx


GROUNDING_SYSTEM_PROMPT = """You are Dalil AI, a multilingual document knowledge assistant.
Answer the user's question using only the supplied document context.
Always answer in the same language as the user's question, even when the document context is written in another language.
If the question is Arabic, answer in natural Arabic. If it is English, answer in English.
If the context does not contain enough information, say so in the same language as the user's question.
Do not use outside knowledge. Do not invent facts or sources.
When the context supports an answer, answer concisely and cite source labels such as [Source 1]."""

RETRIEVAL_TRANSLATION_PROMPT = """You are a strict Arabic-to-English translation engine.
Convert the user's Arabic search question into concise English for document retrieval.
Your output MUST use English words and the Latin alphabet, except for filenames, product names, codes, and numbers, which you must preserve exactly.
Do not answer the question. Do not explain. Do not use Arabic script in the output.
Example: ماذا يحتوي report.txt؟ -> What does report.txt contain?
Return only the English translation with no quotation marks."""

ARABIC_SCRIPT = re.compile(r"[\u0600-\u06ff]")


class LLMServiceError(RuntimeError):
    """Raised when Ollama or the configured model is unavailable."""


class LLMService:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = client

    def available_models(self) -> list[str]:
        try:
            response = self._request("GET", "/api/tags")
            return [str(item["name"]) for item in response.get("models", [])]
        except Exception as exc:
            if isinstance(exc, LLMServiceError):
                raise
            raise LLMServiceError("Could not list Ollama models") from exc

    def validate(self) -> None:
        models = self.available_models()
        if self.model not in models:
            raise LLMServiceError(
                f"Ollama model '{self.model}' is unavailable. Installed: "
                f"{', '.join(models) or '(none)'}"
            )

    def generate(self, question: str, context: str) -> str:
        if not question.strip():
            raise ValueError("Question cannot be empty")
        if not context.strip():
            raise ValueError("Context cannot be empty")
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION:\n{question}",
                },
            ],
            "options": {"temperature": 0},
        }
        data = self._request("POST", "/api/chat", json=payload)
        try:
            answer = str(data["message"]["content"]).strip()
        except (KeyError, TypeError) as exc:
            raise LLMServiceError("Ollama returned an unexpected response") from exc
        if not answer:
            raise LLMServiceError("Ollama returned an empty response")
        return answer

    def translate_for_retrieval(self, question: str) -> str:
        """Translate an Arabic query for an English embedding index."""
        if not question.strip():
            raise ValueError("Question cannot be empty")
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": RETRIEVAL_TRANSLATION_PROMPT},
                {"role": "user", "content": question},
            ],
            "options": {"temperature": 0},
        }
        data = self._request("POST", "/api/chat", json=payload)
        try:
            translated = str(data["message"]["content"]).strip()
        except (KeyError, TypeError) as exc:
            raise LLMServiceError("Ollama returned an unexpected translation") from exc
        if not translated or ARABIC_SCRIPT.search(translated):
            retry_payload = {
                **payload,
                "messages": [
                    {"role": "system", "content": RETRIEVAL_TRANSLATION_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Arabic input: {question}\n"
                            "English translation (Latin alphabet only):"
                        ),
                    },
                ],
            }
            retry_data = self._request("POST", "/api/chat", json=retry_payload)
            translated = str(retry_data.get("message", {}).get("content", "")).strip()
        return translated if translated and not ARABIC_SCRIPT.search(translated) else question

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            if self._client is not None:
                response = self._client.request(method, path, **kwargs)
            else:
                response = httpx.request(
                    method,
                    f"{self.base_url}{path}",
                    timeout=self.timeout,
                    **kwargs,
                )
            response.raise_for_status()
            return dict(response.json())
        except httpx.ConnectError as exc:
            raise LLMServiceError(
                f"Ollama is not reachable at {self.base_url}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise LLMServiceError(
                f"Ollama request failed with status {exc.response.status_code}"
            ) from exc
