from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TokenManager:
    """Estimates token usage and checks context limits."""

    def __init__(self, max_tokens: int = 4096, model_name: str = "gpt-3.5-turbo") -> None:
        self.max_tokens = max_tokens
        self.model_name = model_name
        self._encoder = self._load_encoder(model_name)

    def _load_encoder(self, model_name: str) -> Any | None:
        try:
            import tiktoken  # type: ignore

            try:
                return tiktoken.encoding_for_model(model_name)
            except KeyError:
                logger.info(
                    "No direct tokenizer for model '%s'; using cl100k_base.",
                    model_name,
                )
                return tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            logger.info("tiktoken unavailable, using fallback estimation: %s", exc)
            return None

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for text using tiktoken or fallback rule."""
        if not text:
            return 0

        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text))
            except Exception as exc:
                logger.warning("Tokenizer failed, using fallback estimation: %s", exc)

        # Fallback rule from spec: 1 token ~= 4 characters.
        return max(1, (len(text) + 3) // 4)

    def count_tokens(self, messages: list[dict[str, str]] | None = None, text: str | None = None) -> int:
        """Count tokens for either chat messages or plain text."""
        if text is not None:
            return self.estimate_tokens(text)

        if not messages:
            return 0

        total = 0
        for message in messages:
            role = str(message.get("role", ""))
            content = str(message.get("content", ""))
            total += self.estimate_tokens(role)
            total += self.estimate_tokens(content)

        return total

    def check_limit(self, token_count: int, reserve_tokens: int = 0) -> bool:
        """Return True when token count is within the configured limit."""
        return (token_count + reserve_tokens) <= self.max_tokens

    def usage_ratio(self, token_count: int) -> float:
        """Return token usage ratio in range [0.0, +inf)."""
        if self.max_tokens <= 0:
            return 0.0
        return token_count / self.max_tokens

    def set_max_tokens(self, max_tokens: int) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")
        self.max_tokens = max_tokens
