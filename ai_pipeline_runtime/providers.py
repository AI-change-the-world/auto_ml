from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import re
import uuid
from io import BytesIO
from typing import Any
from urllib.request import urlopen

from config import ProviderConfig, RuntimeConfig
from models import ImagePayload
from storage import upload_bytes_to_s3
from utils import (
    content_to_text,
    extract_json_block,
    image_bytes_to_data_url,
    image_size,
    load_image_bytes,
    payload_to_data_url,
)

logger = logging.getLogger(__name__)
_LOG_TEXT_LIMIT = max(200, int(os.getenv("AI_PIPELINE_RUNTIME_LOG_TEXT_LIMIT", "4000")))


def _preview_for_log(value: Any, *, limit: int = _LOG_TEXT_LIMIT) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False)
        except Exception:
            text = str(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...(truncated {len(text) - limit} chars)"


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
        json_mode: bool = False,
        json_response_type: str | None = None,
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
                raise ProviderError(
                    "openai package is required for openai_compatible providers") from exc

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
            raise ProviderError(
                f"provider `{self.name}` is missing model configuration")

        user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image is not None:
            user_content.append(
                {"type": "image_url", "image_url": {
                    "url": payload_to_data_url(image)}}
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
        content = content_to_text(response.choices[0].message.content).strip()
        logger.info(
            "Provider text response provider=%s model=%s content=%s",
            self.name,
            self.config.model,
            _preview_for_log(content),
        )
        return content

    def generate_json(
        self,
        *,
        prompt: str,
        image: ImagePayload | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        json_response_type: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        if not self.config.model:
            raise ProviderError(
                f"provider `{self.name}` is missing model configuration")

        user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image is not None:
            user_content.append(
                {"type": "image_url", "image_url": {
                    "url": payload_to_data_url(image)}}
            )

        if not json_mode:
            return super().generate_json(
                prompt=prompt,
                image=image,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
                json_response_type=json_response_type,
            )

        try:
            request_kwargs: dict[str, Any] = {}
            if json_response_type:
                request_kwargs["response_format"] = {
                    "type": json_response_type}
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
                **request_kwargs,
            )
            content = content_to_text(response.choices[0].message.content).strip()
            logger.info(
                "Provider raw JSON response provider=%s model=%s content=%s",
                self.name,
                self.config.model,
                _preview_for_log(content),
            )
            try:
                parsed = json.loads(content)
                logger.info(
                    "Provider parsed JSON response provider=%s model=%s payload=%s",
                    self.name,
                    self.config.model,
                    _preview_for_log(parsed),
                )
                return parsed
            except json.JSONDecodeError:
                logger.warning(
                    "provider `%s` returned invalid JSON in native JSON mode, falling back to block extraction",
                    self.name,
                )
                extracted = extract_json_block(content)
                logger.info(
                    "Provider extracted JSON block provider=%s model=%s payload=%s",
                    self.name,
                    self.config.model,
                    _preview_for_log(extracted),
                )
                return extracted
        except Exception as exc:
            logger.warning(
                "provider `%s` native JSON mode failed (%s), falling back to text parsing",
                self.name,
                exc,
            )
            return super().generate_json(
                prompt=prompt,
                image=image,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=False,
                json_response_type=None,
            )

    def edit_image(
        self,
        *,
        prompt: str,
        image: ImagePayload,
        size: str | None = None,
        background: str | None = None,
    ) -> ImagePayload:
        if not self.config.model:
            raise ProviderError(
                f"provider `{self.name}` is missing model configuration")

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
            raise ProviderError(
                f"image edit request failed for provider `{self.name}`: {exc}") from exc

        if not getattr(response, "data", None):
            raise ProviderError(
                f"provider `{self.name}` returned empty image edit result")

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


class DashScopeMultimodalProvider(BaseMultimodalProvider):
    def __init__(self, name: str, config: ProviderConfig) -> None:
        super().__init__(name=name, config=config)
        self._last_generated_image_s3_key: str | None = None

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
            raise ProviderError(
                f"provider `{self.name}` is missing model configuration")
        if image is None:
            raise ProviderError(
                f"provider `{self.name}` requires an image for multimodal generation")

        try:
            import dashscope
            from dashscope import MultiModalConversation
        except ImportError as exc:
            raise ProviderError(
                "dashscope package is required for dashscope_multimodal providers") from exc

        if self.config.base_url:
            dashscope.base_http_api_url = self.config.base_url

        full_prompt = prompt.strip()
        if system_prompt and system_prompt.strip():
            full_prompt = f"{system_prompt.strip()}\n\n{full_prompt}"
        logger.info(
            "DashScope multimodal request provider=%s model=%s prompt=%s",
            self.name,
            self.config.model,
            full_prompt,
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"image": payload_to_data_url(image)},
                    {"text": full_prompt},
                ],
            }
        ]

        try:
            response = MultiModalConversation.call(
                api_key=self.config.api_key,
                model=self.config.model,
                messages=messages,
                stream=False,
                temperature=self.config.temperature if temperature is None else temperature,
                max_tokens=self.config.max_tokens if max_tokens is None else max_tokens,
                **self.config.extra,
            )
        except Exception as exc:
            raise ProviderError(
                f"dashscope request failed for provider `{self.name}`: {exc}") from exc

        status_code = getattr(response, "status_code", None)
        if status_code != 200:
            raise ProviderError(
                f"dashscope request failed for provider `{self.name}`: status={status_code}, "
                f"code={getattr(response, 'code', None)}, message={getattr(response, 'message', None)}"
            )

        output = getattr(response, "output", None)
        choices = getattr(output, "choices",
                          None) if output is not None else None
        if not choices:
            raise ProviderError(
                f"provider `{self.name}` returned empty multimodal result")

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content",
                          None) if message is not None else None
        text = content_to_text(content).strip()
        logger.info(
            "DashScope multimodal response provider=%s model=%s content=%s",
            self.name,
            self.config.model,
            _preview_for_log(text),
        )
        return text

    def edit_image(
        self,
        *,
        prompt: str,
        image: ImagePayload,
        size: str | None = None,
        background: str | None = None,
    ) -> ImagePayload:
        if not self.config.model:
            raise ProviderError(
                f"provider `{self.name}` is missing model configuration")

        try:
            import dashscope
            from dashscope import MultiModalConversation
        except ImportError as exc:
            raise ProviderError(
                "dashscope package is required for dashscope_multimodal providers") from exc

        if self.config.base_url:
            dashscope.base_http_api_url = self.config.base_url

        request_kwargs = dict(self.config.extra)
        if size is not None:
            request_kwargs["size"] = size
        if background is not None:
            request_kwargs["background"] = background

        edit_prompt = prompt.strip()
        logger.info(
            "DashScope image edit request provider=%s model=%s prompt=%s",
            self.name,
            self.config.model,
            edit_prompt,
        )

        try:
            response = MultiModalConversation.call(
                api_key=self.config.api_key,
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": payload_to_data_url(image)},
                            {"text": edit_prompt},
                        ],
                    }
                ],
                stream=False,
                **request_kwargs,
            )
        except Exception as exc:
            raise ProviderError(
                f"dashscope image edit failed for provider `{self.name}`: {exc}") from exc

        status_code = getattr(response, "status_code", None)
        if status_code != 200:
            raise ProviderError(
                f"dashscope image edit failed for provider `{self.name}`: status={status_code}, "
                f"code={getattr(response, 'code', None)}, message={getattr(response, 'message', None)}"
            )

        output = getattr(response, "output", None)
        choices = getattr(output, "choices",
                          None) if output is not None else None
        if not choices:
            raise ProviderError(
                f"provider `{self.name}` returned empty image edit result")

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content",
                          None) if message is not None else None
        generated_image = self._extract_image_content(content)
        if generated_image is None:
            raise ProviderError(
                f"provider `{self.name}` did not return generated image content")

        image_bytes, mime_type = self._load_generated_image_bytes(
            generated_image)
        result_payload = ImagePayload(
            base64_data=image_bytes_to_data_url(
                image_bytes, mime_type=mime_type),
            mime_type=mime_type,
        )
        s3_key = f"auto_augment/overlay_results/{uuid.uuid4().hex}.png"
        try:
            upload_bytes_to_s3(image_bytes, s3_key)
            self._last_generated_image_s3_key = s3_key
            logger.info(
                "Uploaded DashScope edited image to MinIO: %s",
                s3_key,
            )
        except Exception as exc:
            self._last_generated_image_s3_key = None
            logger.warning(
                "Failed to upload DashScope edited image to MinIO: %s", exc)

        return ImagePayload(
            base64_data=result_payload.base64_data,
            mime_type=result_payload.mime_type,
        )

    def _extract_image_content(self, content: Any) -> dict[str, str] | None:
        if isinstance(content, dict):
            image_value = content.get("image")
            if isinstance(image_value, str) and image_value:
                return self._classify_generated_image(image_value)
            return None
        if not isinstance(content, list):
            return None
        for item in content:
            if not isinstance(item, dict):
                continue
            image_value = item.get("image")
            if isinstance(image_value, str) and image_value:
                return self._classify_generated_image(image_value)
        return None

    def _classify_generated_image(self, image_value: str) -> dict[str, str]:
        stripped = image_value.strip()
        if stripped.startswith("data:"):
            return {
                "kind": "data_url",
                "value": stripped,
                "mime_type": self._mime_type_from_data_url(stripped) or "image/png",
            }
        if stripped.startswith("http://") or stripped.startswith("https://"):
            return {
                "kind": "url",
                "value": stripped,
                "mime_type": "image/png",
            }
        return {
            "kind": "base64",
            "value": stripped,
            "mime_type": "image/png",
        }

    def _load_generated_image_bytes(self, generated_image: dict[str, str]) -> tuple[bytes, str]:
        kind = generated_image.get("kind")
        value = generated_image.get("value", "")
        mime_type = generated_image.get("mime_type", "image/png")
        if kind == "url":
            return self._download_image_bytes(value, fallback_mime_type=mime_type)
        if kind == "data_url":
            return load_image_bytes(
                ImagePayload(
                    base64_data=value,
                    mime_type=mime_type,
                )
            ), mime_type
        if kind == "base64":
            try:
                return self._decode_base64_bytes(value), mime_type
            except binascii.Error as exc:
                raise ProviderError(
                    f"provider `{self.name}` returned an invalid base64 image payload"
                ) from exc
        raise ProviderError(
            f"provider `{self.name}` returned unsupported image payload kind `{kind}`"
        )

    def _download_image_bytes(self, url: str, fallback_mime_type: str) -> tuple[bytes, str]:
        try:
            with urlopen(url, timeout=self.config.timeout_seconds) as response:
                image_bytes = response.read()
                content_type = response.headers.get_content_type()
        except Exception as exc:
            raise ProviderError(
                f"failed to download generated image from DashScope url: {url}"
            ) from exc
        mime_type = content_type or fallback_mime_type or "image/png"
        return image_bytes, mime_type

    def _decode_base64_bytes(self, value: str) -> bytes:
        padded = value + ("=" * (-len(value) % 4))
        return base64.b64decode(padded, validate=False)

    def _mime_type_from_data_url(self, value: str) -> str | None:
        match = re.match(r"^data:([^;,]+)", value)
        if not match:
            return None
        return match.group(1)


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
        json_mode: bool = False,
        json_response_type: str | None = None,
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
        match = re.search(
            r"allowed_classes\s*=\s*\[(.*?)\]", prompt, flags=re.DOTALL)
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

    @staticmethod
    def build_provider(name: str, config: ProviderConfig) -> BaseMultimodalProvider:
        if config.kind == "openai_compatible":
            return OpenAICompatibleProvider(name=name, config=config)
        if config.kind == "dashscope_multimodal":
            return DashScopeMultimodalProvider(name=name, config=config)
        if config.kind == "mock":
            return MockProvider(name=name, config=config)
        raise ProviderError(f"unsupported provider kind `{config.kind}`")

    @classmethod
    def from_config(cls, config: RuntimeConfig) -> "ProviderRegistry":
        providers: dict[str, BaseMultimodalProvider] = {}
        for name, item in config.providers.items():
            try:
                providers[name] = cls.build_provider(name=name, config=item)
            except ProviderError:
                logger.warning(
                    "Unsupported provider kind `%s`, skipping `%s`", item.kind, name)
        return cls(providers)

    def get(self, name: str) -> BaseMultimodalProvider:
        if name not in self._providers:
            raise ProviderError(f"provider `{name}` is not configured")
        return self._providers[name]

    def names(self) -> list[str]:
        return sorted(self._providers.keys())
