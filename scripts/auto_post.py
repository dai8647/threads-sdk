#!/usr/bin/env python3
"""Threads Auto-Poster: AI-powered automatic posting system."""

import argparse
import logging
import os
import sys
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from threads_sdk.auth import Credentials
from threads_sdk.client import ThreadsClient
from threads_sdk.autoposter.persona import PersonaManager
from threads_sdk.autoposter.generator import PostGenerator
from threads_sdk.autoposter.scheduler import AutoScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Resolve environment variables
    def resolve_env(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.environ.get(env_var, value)
        return value

    def resolve_nested(d):
        if isinstance(d, dict):
            return {k: resolve_nested(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [resolve_nested(i) for i in d]
        else:
            return resolve_env(d)

    return resolve_nested(config)


def main():
    parser = argparse.ArgumentParser(description="Threads Auto-Poster")
    parser.add_argument("--config", default="config/settings.yaml", help="Config file path")
    parser.add_argument("--persona", default="", help="Persona ID to use")
    parser.add_argument("--topic", default="", help="Specific topic to post about")
    parser.add_argument("--once", action="store_true", help="Post once and exit")
    parser.add_argument("--loop", action="store_true", help="Run in loop mode")
    parser.add_argument("--list-personas", action="store_true", help="List available personas")
    parser.add_argument("--provider", choices=["nvidia", "local"], help="LLM provider to use")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # List personas
    if args.list_personas:
        persona_manager = PersonaManager(config.get("personas_file", "config/personas.yaml"))
        for p in persona_manager.list_personas():
            print(f"  {p.id}: {p.name} - {p.description}")
        return

    # Initialize components
    persona_manager = PersonaManager(config.get("personas_file", "config/personas.yaml"))

    llm_config = config.get("llm", {})
    provider = args.provider or llm_config.get("provider", "nvidia")

    generator = PostGenerator(
        provider=provider,
        nvidia_api_key=llm_config.get("nvidia", {}).get("api_key", ""),
        nvidia_model=llm_config.get("nvidia", {}).get("model", "meta/llama-3.1-8b-instruct"),
        nvidia_base_url=llm_config.get("nvidia", {}).get("base_url", "https://integrate.api.nvidia.com/v1"),
        local_url=llm_config.get("local", {}).get("url", "http://localhost:8080/v1"),
        local_model=llm_config.get("local", {}).get("model", "tq3-4s-27b"),
    )

    # Initialize Threads client
    threads_config = config.get("threads", {})
    credentials = Credentials(
        access_token=threads_config.get("token", ""),
        user_id=threads_config.get("user_id", ""),
    )
    client = ThreadsClient(credentials=credentials)

    # Create scheduler
    scheduler = AutoScheduler(
        generator=generator,
        persona_manager=persona_manager,
        threads_client=client,
        config=config,
    )

    if args.once:
        # Post once
        post_id = scheduler.post_once(
            persona_id=args.persona,
            topic=args.topic,
        )
        if post_id:
            print(f"Posted successfully: {post_id}")
        else:
            print("Failed to post")
            sys.exit(1)
    elif args.loop:
        # Run in loop mode
        try:
            scheduler.run_loop()
        except KeyboardInterrupt:
            scheduler.stop()
            print("\nStopped")
    else:
        # Default: post once
        post_id = scheduler.post_once(
            persona_id=args.persona,
            topic=args.topic,
        )
        if post_id:
            print(f"Posted successfully: {post_id}")
        else:
            print("Failed to post")
            sys.exit(1)


if __name__ == "__main__":
    main()
