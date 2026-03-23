from __future__ import annotations

import logging
import re
from io import BytesIO
from typing import Any

from .config import ProviderConfig, RuntimeConfig
from .models import ImagePayload
from .utils import (
    content_to_text,
    extract_json_block,
    image_size,
    load_image_bytes,
    payload_to_data_url,
)

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    pass


class BaseMultimodalProvider:
    def __init__(self, name: str, config: ProviderConfig) -> None:
        self.name = name
        self.config = config

    @property
    def role(self) -> str:
        return self.config.role

    def generate_text(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        raise NotImplementedError

    def generate_json(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        text = self.generate_text(
            prompt=prompt,
            image=image,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return extract_json_block(text)

    def edit_image(
        self,
        *,
        prompt: str,
        image: ImagePayload,
        size: str | None = None,
        background: str | None = None,
    ) -> ImagePayload:
        raise NotImplementedError


class OpenAICompatibleProvider(BaseMultimodalProvider):
    def __init__(self, name: str, config: ProviderConfig) -> None:
        super().__init__(name=name, config=config)
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ProviderError("openai package is required for openai_compatible providers") from exc

            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout_seconds,
                default_headers=self.config.extra_headers or None,
            )
        return self._client

    def generate_text(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not self.config.model:
            raise ProviderError(f"provider `{self.name}` is missing model configuration")

        user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image is not None:
            user_content.append(
                {"type": "image_url", "image_url": {"url": payload_to_data_url(image)}}
            )

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt or "You are a careful multimodal annotation assistant.",
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            temperature=self.config.temperature if temperature is None else temperature,
            max_tokens=self.config.max_tokens if max_tokens is None else max_tokens,
        )
        return content_to_text(response.choices[0].message.content).strip()

    def edit_image(
        self,
        *,
        prompt: str,
        image: ImagePayload,
        size: str | None = None,
        background: str | None = None,
    ) -> ImagePayload:
        if not self.config.model:
            raise ProviderError(f"provider `{self.name}` is missing model configuration")

        image_buffer = BytesIO(load_image_bytes(image))
        image_buffer.name = "annotation_input.png"

        extra = dict(self.config.extra)
        response_format = str(extra.pop("response_format", "b64_json"))

        try:
            response = self.client.images.edit(
                model=self.config.model,
                image=image_buffer,
                prompt=prompt,
                size=size or extra.pop("size", None),
                background=background or extra.pop("background", None),
                response_format=response_format,
                **extra,
            )
        except Exception as exc:
            raise ProviderError(f"image edit request failed for provider `{self.name}`: {exc}") from exc

        if not getattr(response, "data", None):
            raise ProviderError(f"provider `{self.name}` returned empty image edit result")

        first_item = response.data[0]
        b64_json = getattr(first_item, "b64_json", None)
        if not b64_json:
            raise ProviderError(
                f"provider `{self.name}` did not return `b64_json`; configure image edit provider to return base64 data"
            )
        return ImagePayload(
            base64_data=f"data:image/png;base64,{b64_json}",
            mime_type="image/png",
        )


class MockProvider(BaseMultimodalProvider):
    def generate_text(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        lowered = prompt.lower()
        if "label text" in lowered or "ocr" in lowered or "read the short object label" in lowered:
            return "mock-label"
        if image is not None:
            width, height = image_size(image)
            return f"Mock summary for image {width}x{height}."
        return "Mock multimodal response."

    def generate_json(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        width, height = (1000, 1000)
        if image is not None:
            width, height = image_size(image)
        allowed_classes = self._extract_allowed_classes(prompt)
        label = allowed_classes[0] if allowed_classes else "mock-object"
        return {
            "annotations": [
                {
                    "label": label,
                    "bbox": {
                        "x1": int(width * 0.1),
                        "y1": int(height * 0.1),
                        "x2": int(width * 0.6),
                        "y2": int(height * 0.7),
                    },
                    "label_anchor": {
                        "x": int(width * 0.1) + 4,
                        "y": max(0, int(height * 0.1) - 8),
                    },
                    "confidence": 0.9,
                }
            ],
            "summary": "Mock annotation draft.",
        }

    def _extract_allowed_classes(self, prompt: str) -> list[str]:
        match = re.search(r"allowed_classes\s*=\s*\[(.*?)\]", prompt, flags=re.DOTALL)
        if not match:
            return []
        return [item.strip().strip("\"'") for item in match.group(1).split(",") if item.strip()]

    def edit_image(
        self,
        *,
        prompt: str,
        image: ImagePayload,
        size: str | None = None,
        background: str | None = None,
    ) -> ImagePayload:
        # Mock provider just passes the original image through so the pipeline can be smoke-tested locally.
        return image.model_copy(deep=True)


class ProviderRegistry:
    def __init__(self, providers: dict[str, BaseMultimodalProvider]) -> None:
        self._providers = providers

    @classmethod
    def from_config(cls, config: RuntimeConfig) -> "ProviderRegistry":
        providers: dict[str, BaseMultimodalProvider] = {}
        for name, item in config.providers.items():
            if item.kind == "openai_compatible":
                providers[name] = OpenAICompatibleProvider(name=name, config=item)
            elif item.kind == "mock":
                providers[name] = MockProvider(name=name, config=item)
            else:
                logger.warning("Unsupported provider kind `%s`, skipping `%s`", item.kind, name)
        return cls(providers)

    def get(self, name: str) -> BaseMultimodalProvider:
        if name not in self._providers:
            raise ProviderError(f"provider `{name}` is not configured")
        return self._providers[name]

    def names(self) -> list[str]:
        return sorted(self._providers.keys())
