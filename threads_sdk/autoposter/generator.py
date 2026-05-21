"""LLM-powered post generation for auto-posting."""

from __future__ import annotations

import os
import random
from typing import Optional

import httpx

from threads_sdk.autoposter.persona import Persona


class PostGenerator:
    """Generates posts using LLM (NVIDIA API or local)."""

    def __init__(
        self,
        provider: str = "nvidia",
        nvidia_api_key: str = "",
        nvidia_model: str = "meta/llama-3.1-8b-instruct",
        nvidia_base_url: str = "https://integrate.api.nvidia.com/v1",
        local_url: str = "http://localhost:8080/v1",
        local_model: str = "tq3-4s-27b",
    ) -> None:
        self.provider = provider
        self.nvidia_api_key = nvidia_api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.nvidia_model = nvidia_model
        self.nvidia_base_url = nvidia_base_url
        self.local_url = local_url
        self.local_model = local_model

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
            return self._call_nvidia(prompt)
        else:
            return self._call_local(prompt)

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

    def _call_nvidia(self, prompt: str) -> str:
        """Call NVIDIA API for text generation."""
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.nvidia_model,
            "messages": [
                {"role": "system", "content": "あなたはThreadsソーシャルメディアの投稿者です。短く、魅力的な投稿を生成してください。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.8,
        }

        response = httpx.post(
            f"{self.nvidia_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    def _call_local(self, prompt: str) -> str:
        """Call local LLM for text generation."""
        payload = {
            "model": self.local_model,
            "messages": [
                {"role": "system", "content": "あなたはThreadsソーシャルメディアの投稿者です。短く、魅力的な投稿を生成してください。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.8,
        }

        response = httpx.post(
            f"{self.local_url}/chat/completions",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
