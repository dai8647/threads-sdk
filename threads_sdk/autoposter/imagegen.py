"""Image generation + upload for auto-posting."""

from __future__ import annotations

import base64
import hashlib
import os
import random
import time
from pathlib import Path
from typing import Optional

import httpx


class ImageGenerator:
    """Generates images and uploads them for Threads posting."""

    def __init__(
        self,
        provider: str = "pollinations",
        output_dir: str = "generated_images",
    ) -> None:
        self.provider = provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_and_upload(
        self,
        prompt: str,
        style: str = "",
        width: int = 1024,
        height: int = 1024,
    ) -> Optional[str]:
        """Generate image and return a public URL (fully automatic)."""
        # Generate
        image_path = self.generate(prompt, style, width, height)
        if not image_path:
            return None

        # Upload to get public URL
        url = self.upload_image(image_path)
        return url

    def generate(
        self,
        prompt: str,
        style: str = "",
        width: int = 1024,
        height: int = 1024,
    ) -> Optional[Path]:
        """Generate an image from a prompt."""
        if self.provider == "pollinations":
            return self._generate_pollinations(prompt, width, height, style)
        else:
            return self._generate_pollinations(prompt, width, height, style)

    def upload_image(self, image_path: Path) -> Optional[str]:
        """Upload image to free hosting and return public URL."""
        # Try catbox.moe first (no API key needed)
        url = self._upload_catbox(image_path)
        if url:
            return url

        # Fallback: use the pollinations URL directly (for pollinations-generated images)
        return None

    def _generate_pollinations(self, prompt: str, width: int, height: int, style: str = "") -> Optional[Path]:
        """Generate image using Pollinations.ai (free, no API key)."""
        styled_prompt = f"{prompt}, {style} style, high quality, detailed" if style else f"{prompt}, high quality, detailed"

        timestamp = int(time.time())
        hash_str = hashlib.md5(styled_prompt.encode()).hexdigest()[:8]
        filename = f"img_{timestamp}_{hash_str}.jpg"
        filepath = self.output_dir / filename

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

    def _upload_catbox(self, image_path: Path) -> Optional[str]:
        """Upload to catbox.moe (free, no API key, instant public URL)."""
        try:
            with open(image_path, "rb") as f:
                response = httpx.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (image_path.name, f, "image/jpeg")},
                    timeout=60.0,
                )
            response.raise_for_status()
            url = response.text.strip()
            if url.startswith("https://"):
                return url
            return None
        except Exception as e:
            print(f"Catbox upload failed: {e}")
            return None

    def generate_for_post(
        self,
        topic: str,
        persona_style: str = "",
    ) -> Optional[str]:
        """Generate image for a post and return public URL (fully automatic)."""
        base_prompts = [
            f"A modern, clean illustration about {topic}",
            f"A visually appealing graphic representing {topic}",
            f"An eye-catching social media image about {topic}",
            f"A professional infographic-style image about {topic}",
        ]

        prompt = random.choice(base_prompts)
        if persona_style:
            prompt += f", {persona_style} aesthetic"

        styles = ["minimalist", "flat design", "gradient", "modern", "clean"]
        chosen_style = random.choice(styles)

        return self.generate_and_upload(prompt, style=chosen_style)
