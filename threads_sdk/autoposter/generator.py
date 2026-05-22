"""LLM-powered post generation for auto-posting."""

from __future__ import annotations

import os
import random
from typing import Optional

import httpx

from threads_sdk.autoposter.persona import Persona


class PostGenerator:
    """Generates posts using LLM (9router / NVIDIA / local)."""

    def __init__(
        self,
        provider: str = "9router",
        nvidia_api_key: str = "",
        nvidia_model: str = "meta/llama-3.1-8b-instruct",
        nvidia_base_url: str = "https://integrate.api.nvidia.com/v1",
        local_url: str = "http://localhost:8080/v1",
        local_model: str = "tq3-4s-27b",
        ninerouter_url: str = "http://localhost:20128/v1",
        ninerouter_model: str = "opencode-go/kimi-k2.6",
    ) -> None:
        self.provider = provider
        self.nvidia_api_key = nvidia_api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.nvidia_model = nvidia_model
        self.nvidia_base_url = nvidia_base_url
        self.local_url = local_url
        self.local_model = local_model
        self.ninerouter_url = ninerouter_url
        self.ninerouter_model = ninerouter_model

    def generate(
        self,
        persona: Persona,
        topic: str = "",
        include_affiliate: bool = False,
        affiliate_link: str = "",
        affiliate_context: str = "",
    ) -> str:
        """Generate a post using the configured LLM."""
        prompt = self._build_prompt(
            persona, topic, include_affiliate, affiliate_link, affiliate_context
        )

        if self.provider == "nvidia":
            return self._call_api(self.nvidia_base_url, self.nvidia_model, prompt, self.nvidia_api_key)
        elif self.provider == "9router":
            return self._call_api(self.ninerouter_url, self.ninerouter_model, prompt)
        else:
            return self._call_api(self.local_url, self.local_model, prompt)

    def _build_prompt(
        self,
        persona: Persona,
        topic: str,
        include_affiliate: bool,
        affiliate_link: str,
        affiliate_context: str,
    ) -> str:
        """Build the full prompt for LLM."""
        base_prompt = persona.get_prompt(topic)

        if include_affiliate and affiliate_link:
            base_prompt += f"\n\n以下のアフィリエイトリンクを自然に組み込んでください:"
            base_prompt += f"\nリンク: {affiliate_link}"
            base_prompt += f"\nコンテキスト: {affiliate_context}"
            base_prompt += "\nリンクは投稿の最後に自然に入れてください。"

        base_prompt += "\n\n投稿文のみを出力してください。説明や前置きは不要です。"
        return base_prompt

    def _call_api(
        self,
        base_url: str,
        model: str,
        prompt: str,
        api_key: str = "",
    ) -> str:
        """Call OpenAI-compatible API for text generation."""
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "あなたはThreadsソーシャルメディアの投稿者です。短く、魅力的な投稿を生成してください。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.8,
        }

        response = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
