"""Image generation for auto-posting."""

from __future__ import annotations

import hashlib
import os
import random
import time
from pathlib import Path
from typing import Optional

import httpx


class ImageGenerator:
    """Generates images using free APIs."""

    def __init__(
        self,
        provider: str = "pollinations",
        output_dir: str = "generated_images",
    ) -> None:
        self.provider = provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        prompt: str,
        style: str = "anime",
        width: int = 1024,
        height: int = 1024,
    ) -> Optional[Path]:
        """Generate an image from a prompt."""
        if self.provider == "pollinations":
            return self._generate_pollinations(prompt, width, height, style)
        elif self.provider == "cloudflare":
            return self._generate_cloudflare(prompt, width, height)
        else:
            return self._generate_pollinations(prompt, width, height, style)

    def _generate_pollinations(self, prompt: str, width: int, height: int, style: str = "") -> Optional[Path]:
        """Generate image using Pollinations.ai (free, no API key)."""
        # Add style to prompt
        styled_prompt = f"{prompt}, {style} style, high quality, detailed" if style else f"{prompt}, high quality, detailed"

        # Create unique filename
        timestamp = int(time.time())
        hash_str = hashlib.md5(styled_prompt.encode()).hexdigest()[:8]
        filename = f"img_{timestamp}_{hash_str}.jpg"
        filepath = self.output_dir / filename

        # URL encode the prompt
        encoded_prompt = httpx.URL(f"https://image.pollinations.ai/prompt/{styled_prompt}")

        try:
            response = httpx.get(
                str(encoded_prompt),
                params={"width": width, "height": height, "nologo": "true"},
                timeout=120.0,
                follow_redirects=True,
            )
            response.raise_for_status()

            filepath.write_bytes(response.content)
            return filepath

        except Exception as e:
            print(f"Image generation failed: {e}")
            return None

    def _generate_cloudflare(self, prompt: str, width: int, height: int) -> Optional[Path]:
        """Generate image using Cloudflare Workers AI (free tier)."""
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        api_token = os.environ.get("CLOUDFLARE_API_TOKEN", "")

        if not account_id or not api_token:
            print("Cloudflare credentials not set")
            return None

        timestamp = int(time.time())
        hash_str = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filename = f"img_{timestamp}_{hash_str}.jpg"
        filepath = self.output_dir / filename

        try:
            response = httpx.post(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell",
                headers={"Authorization": f"Bearer {api_token}"},
                json={"prompt": prompt},
                timeout=120.0,
            )
            response.raise_for_status()

            # Response is raw image bytes
            filepath.write_bytes(response.content)
            return filepath

        except Exception as e:
            print(f"Cloudflare image generation failed: {e}")
            return None

    def generate_for_post(
        self,
        topic: str,
        persona_style: str = "",
        include_affiliate: bool = False,
    ) -> Optional[Path]:
        """Generate an image that matches a post topic."""
        # Build image prompt based on topic and style
        base_prompts = [
            f"A modern, clean illustration about {topic}",
            f"A visually appealing graphic representing {topic}",
            f"An eye-catching social media image about {topic}",
            f"A professional infographic-style image about {topic}",
        ]

        prompt = random.choice(base_prompts)

        if persona_style:
            prompt += f", {persona_style} aesthetic"

        # Choose style based on content
        styles = ["minimalist", "flat design", "gradient", "modern", "clean"]
        chosen_style = random.choice(styles)

        return self.generate(prompt, style=chosen_style)
