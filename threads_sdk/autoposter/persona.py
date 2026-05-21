"""Persona management for auto-posting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Persona:
    """A posting persona with style and topic configuration."""

    id: str
    name: str
    description: str
    style: str
    topics: list[str]
    tone: str
    hashtags: list[str]
    emoji: bool
    post_format: str

    def get_prompt(self, topic: str = "") -> str:
        """Generate a prompt for LLM based on this persona."""
        if not topic:
            import random
            topic = random.choice(self.topics)

        prompt = self.post_format.format(topic=topic)
        prompt += f"\n\nスタイル: {self.style}"
        prompt += f"\nトーン: {self.tone}"
        if self.hashtags:
            prompt += f"\nハッシュタグ: {', '.join(self.hashtags)}"
        if not self.emoji:
            prompt += "\n絵文字は使わないこと。"
        return prompt


class PersonaManager:
    """Manages multiple personas from YAML config."""

    def __init__(self, config_path: str | Path = "config/personas.yaml") -> None:
        self.config_path = Path(config_path)
        self.personas: dict[str, Persona] = {}
        self._load()

    def _load(self) -> None:
        """Load personas from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Persona config not found: {self.config_path}")

        with open(self.config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for persona_id, config in data.get("personas", {}).items():
            self.personas[persona_id] = Persona(
                id=persona_id,
                name=config["name"],
                description=config.get("description", ""),
                style=config["style"],
                topics=config.get("topics", []),
                tone=config.get("tone", ""),
                hashtags=config.get("hashtags", []),
                emoji=config.get("emoji", True),
                post_format=config.get("post_format", "{topic}について投稿して。"),
            )

    def get(self, persona_id: str) -> Optional[Persona]:
        """Get a persona by ID."""
        return self.personas.get(persona_id)

    def list_personas(self) -> list[Persona]:
        """List all available personas."""
        return list(self.personas.values())

    def get_random_persona(self) -> Persona:
        """Get a random persona."""
        import random
        return random.choice(list(self.personas.values()))
