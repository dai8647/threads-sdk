"""Scheduler for auto-posting."""

from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from threads_sdk.autoposter.generator import PostGenerator
from threads_sdk.autoposter.persona import Persona, PersonaManager
from threads_sdk.client import ThreadsClient
from threads_sdk.auth import Credentials

logger = logging.getLogger(__name__)


class PostHistory:
    """Manages post history to prevent duplicates."""

    def __init__(self, history_file: str = "config/post_history.json") -> None:
        self.history_file = Path(history_file)
        self.posts: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            with open(self.history_file, encoding="utf-8") as f:
                self.posts = json.load(f)

    def _save(self) -> None:
        """Save history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.posts, f, ensure_ascii=False, indent=2)

    def add(self, post_id: str, text: str, persona_id: str) -> None:
        """Add a post to history."""
        self.posts.append({
            "post_id": post_id,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "persona_id": persona_id,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_count_today(self) -> int:
        """Get number of posts today."""
        today = datetime.now().date()
        return sum(
            1 for p in self.posts
            if datetime.fromisoformat(p["timestamp"]).date() == today
        )

    def get_total_count(self) -> int:
        """Get total number of posts."""
        return len(self.posts)


class AutoScheduler:
    """Schedules and executes auto-posting."""

    def __init__(
        self,
        generator: PostGenerator,
        persona_manager: PersonaManager,
        threads_client: ThreadsClient,
        config: dict,
    ) -> None:
        self.generator = generator
        self.persona_manager = persona_manager
        self.client = threads_client
        self.config = config
        self.history = PostHistory(config.get("posting", {}).get("history_file", "config/post_history.json"))
        self.running = False

    def should_include_affiliate(self) -> bool:
        """Determine if this post should include an affiliate link."""
        affiliate_config = self.config.get("affiliate", {})
        if not affiliate_config.get("enabled", False):
            return False
        frequency = affiliate_config.get("frequency", 5)
        total = self.history.get_total_count()
        return (total + 1) % frequency == 0

    def get_affiliate_link(self, text: str) -> Optional[dict]:
        """Get an affiliate link that matches the post content."""
        links = self.config.get("affiliate", {}).get("links", [])
        if not links:
            return None

        # Try to find a link matching keywords
        for link in links:
            keywords = link.get("keywords", [])
            if any(kw.lower() in text.lower() for kw in keywords):
                return link

        # Return random link if no match
        return random.choice(links)

    def post_once(self, persona_id: str = "", topic: str = "") -> Optional[str]:
        """Generate and publish a single post."""
        # Select persona
        if persona_id:
            persona = self.persona_manager.get(persona_id)
            if not persona:
                logger.error(f"Persona not found: {persona_id}")
                return None
        else:
            persona = self.persona_manager.get(
                self.config.get("posting", {}).get("active_persona", "tech_guru")
            )
            if not persona:
                persona = self.persona_manager.get_random_persona()

        # Check daily limit
        max_posts = self.config.get("schedule", {}).get("max_posts_per_day", 6)
        if self.history.get_count_today() >= max_posts:
            logger.info(f"Daily limit reached ({max_posts})")
            return None

        # Determine affiliate
        include_affiliate = self.should_include_affiliate()
        affiliate_link = ""
        affiliate_context = ""
        if include_affiliate:
            link_info = self.get_affiliate_link(topic or persona.topics[0])
            if link_info:
                affiliate_link = link_info["url"]
                affiliate_context = link_info["context"]

        # Generate post
        try:
            text = self.generator.generate(
                persona=persona,
                topic=topic,
                include_affiliate=include_affiliate,
                affiliate_link=affiliate_link,
                affiliate_context=affiliate_context,
            )
            logger.info(f"Generated post ({len(text)} chars): {text[:50]}...")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None

        # Publish
        try:
            post = self.client.create_text_post(text)
            self.history.add(post.id, text, persona.id)
            logger.info(f"Published: {post.id}")
            return post.id
        except Exception as e:
            logger.error(f"Publish failed: {e}")
            return None

    def run_loop(self) -> None:
        """Run the auto-posting loop."""
        self.running = True
        interval_hours = self.config.get("schedule", {}).get("interval_hours", 4)
        randomize = self.config.get("schedule", {}).get("randomize_minutes", 30)

        logger.info(f"Starting auto-poster (interval: {interval_hours}h, randomize: ±{randomize}min)")

        while self.running:
            # Post
            self.post_once()

            # Calculate next run time
            base_interval = interval_hours * 3600
            jitter = random.randint(-randomize * 60, randomize * 60)
            wait_seconds = base_interval + jitter

            logger.info(f"Next post in {wait_seconds // 60} minutes")
            time.sleep(wait_seconds)

    def stop(self) -> None:
        """Stop the auto-posting loop."""
        self.running = False
        logger.info("Auto-poster stopped")
