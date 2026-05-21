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
    parser.add_argument("--interval", type=float, help="Post interval in hours (e.g. 4)")
    parser.add_argument("--max-posts", type=int, help="Max posts per day")
    parser.add_argument("--affiliate-freq", type=int, help="Affiliate link frequency (every N posts)")
    parser.add_argument("--set-provider", choices=["nvidia", "local"], help="Change default provider in config file")
    parser.add_argument("--set-persona", help="Change default persona in config file")
    parser.add_argument("--show-config", action="store_true", help="Show current config")
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Show config
    if args.show_config:
        llm = config.get("llm", {})
        schedule = config.get("schedule", {})
        affiliate = config.get("affiliate", {})
        posting = config.get("posting", {})
        print(f"LLM Provider:    {llm.get('provider', 'nvidia')}")
        print(f"  NVIDIA Model:  {llm.get('nvidia', {}).get('model', 'N/A')}")
        print(f"  Local URL:     {llm.get('local', {}).get('url', 'N/A')}")
        print(f"  Local Model:   {llm.get('local', {}).get('model', 'N/A')}")
        print(f"Interval:        {schedule.get('interval_hours', 4)}h")
        print(f"Max posts/day:   {schedule.get('max_posts_per_day', 6)}")
        print(f"Persona:         {posting.get('active_persona', 'tech_guru')}")
        print(f"Affiliate:       {'ON' if affiliate.get('enabled', False) else 'OFF'} (every {affiliate.get('frequency', 5)} posts)")
        return

    # Set provider in config
    if args.set_provider:
        with open(args.config, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        raw.setdefault("llm", {})["provider"] = args.set_provider
        with open(args.config, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False)
        print(f"Default provider set to: {args.set_provider}")
        config = load_config(args.config)

    # Set persona in config
    if args.set_persona:
        with open(args.config, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        raw.setdefault("posting", {})["active_persona"] = args.set_persona
        with open(args.config, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False)
        print(f"Default persona set to: {args.set_persona}")
        config = load_config(args.config)

    # Apply CLI overrides to config
    if args.interval:
        config.setdefault("schedule", {})["interval_hours"] = args.interval
    if args.max_posts:
        config.setdefault("schedule", {})["max_posts_per_day"] = args.max_posts
    if args.affiliate_freq:
        config.setdefault("affiliate", {})["frequency"] = args.affiliate_freq

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
