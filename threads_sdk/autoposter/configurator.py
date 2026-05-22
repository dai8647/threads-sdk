"""Interactive configurator for Threads Auto-Poster."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table

console = Console()

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"
PERSONAS_FILE = CONFIG_DIR / "personas.yaml"
ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def load_yaml(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def save_env(env: dict) -> None:
    lines = [f"{k}={v}" for k, v in env.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Configurator:
    """Interactive configuration manager."""

    def __init__(self) -> None:
        self.settings = load_yaml(SETTINGS_FILE)
        self.personas = load_yaml(PERSONAS_FILE)
        self.env = load_env()

    def save_all(self) -> None:
        save_yaml(SETTINGS_FILE, self.settings)
        save_yaml(PERSONAS_FILE, self.personas)
        save_env(self.env)

    def show_menu(self) -> None:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Threads Auto-Poster[/bold cyan]\n"
            "[dim]設定・管理ツール[/dim]",
            border_style="cyan",
        ))
        console.print()
        console.print("  [bold]1.[/bold] 現在の設定を表示")
        console.print("  [bold]2.[/bold] LLM設定（NVIDIA / ローカル）")
        console.print("  [bold]3.[/bold] Threads API設定")
        console.print("  [bold]4.[/bold] キャラ（ペルソナ）設定")
        console.print("  [bold]5.[/bold] アフィリエイト設定")
        console.print("  [bold]6.[/bold] 投稿スケジュール設定")
        console.print("  [bold]7.[/bold] 投稿を開始（1回）")
        console.print("  [bold]8.[/bold] 投稿を開始（ループ）")
        console.print("  [bold]9.[/bold] 投稿履歴を表示")
        console.print("  [bold]0.[/bold] 終了")
        console.print()

    def run(self) -> None:
        while True:
            self.show_menu()
            choice = Prompt.ask("選択", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

            if choice == "0":
                console.print("[dim]終了[/dim]")
                break
            elif choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.configure_llm()
            elif choice == "3":
                self.configure_threads()
            elif choice == "4":
                self.configure_personas()
            elif choice == "5":
                self.configure_affiliate()
            elif choice == "6":
                self.configure_schedule()
            elif choice == "7":
                self.post_once()
            elif choice == "8":
                self.post_loop()
            elif choice == "9":
                self.show_history()

    def show_current_config(self) -> None:
        llm = self.settings.get("llm", {})
        threads = self.settings.get("threads", {})
        schedule = self.settings.get("schedule", {})
        posting = self.settings.get("posting", {})
        affiliate = self.settings.get("affiliate", {})

        table = Table(title="現在の設定", show_lines=True)
        table.add_column("項目", style="cyan")
        table.add_column("値")

        table.add_row("LLMプロバイダー", llm.get("provider", "nvidia"))
        table.add_row("NVIDIAモデル", llm.get("nvidia", {}).get("model", "N/A"))
        table.add_row("ローカルURL", llm.get("local", {}).get("url", "N/A"))
        table.add_row("ローカルモデル", llm.get("local", {}).get("model", "N/A"))
        table.add_row("Threads User ID", threads.get("user_id", "未設定"))
        table.add_row("Threads Token", "設定済み" if self.env.get("THREADS_TOKEN") else "未設定")
        table.add_row("デフォルトキャラ", posting.get("active_persona", "未設定"))
        table.add_row("投稿間隔", f"{schedule.get('interval_hours', 4)}時間")
        table.add_row("1日最大投稿数", str(schedule.get("max_posts_per_day", 6)))
        table.add_row("アフィリンク", "ON" if affiliate.get("enabled") else "OFF")
        table.add_row("アフィ頻度", f"{affiliate.get('frequency', 5)}回に1回")

        console.print(table)

        # Personas
        personas = self.personas.get("personas", {})
        if personas:
            console.print()
            pt = Table(title="登録キャラ")
            pt.add_column("ID", style="cyan")
            pt.add_column("名前")
            pt.add_column("スタイル")
            for pid, p in personas.items():
                pt.add_row(pid, p.get("name", ""), p.get("style", ""))
            console.print(pt)

    def configure_llm(self) -> None:
        console.print()
        console.print("[bold]LLM設定[/bold]")
        current = self.settings.get("llm", {}).get("provider", "nvidia")
        console.print(f"現在: [cyan]{current}[/cyan]")
        console.print()
        console.print("  1. NVIDIA API（高品質・有料）")
        console.print("  2. ローカルLLM（無料・localhost:8080）")
        console.print()

        choice = Prompt.ask("選択", choices=["1", "2"])

        if choice == "1":
            self.settings.setdefault("llm", {})["provider"] = "nvidia"
            api_key = Prompt.ask("NVIDIA APIキー", default=self.env.get("NVIDIA_API_KEY", ""))
            if api_key:
                self.env["NVIDIA_API_KEY"] = api_key
            model = Prompt.ask("モデル", default="meta/llama-3.1-8b-instruct")
            self.settings["llm"].setdefault("nvidia", {})["model"] = model
            console.print("[green]NVIDIA API設定完了[/green]")

        elif choice == "2":
            self.settings.setdefault("llm", {})["provider"] = "local"
            url = Prompt.ask("ローカルLLM URL", default="http://localhost:8080/v1")
            model = Prompt.ask("モデル名", default="tq3-4s-27b")
            self.settings["llm"].setdefault("local", {})["url"] = url
            self.settings["llm"]["local"]["model"] = model
            console.print("[green]ローカルLLM設定完了[/green]")

        self.save_all()

    def configure_threads(self) -> None:
        console.print()
        console.print("[bold]Threads API設定[/bold]")

        token = Prompt.ask("アクセストークン", default=self.env.get("THREADS_TOKEN", "")[:20] + "..." if self.env.get("THREADS_TOKEN") else "")
        if token and "..." not in token:
            self.env["THREADS_TOKEN"] = token

        user_id = Prompt.ask("User ID", default=self.settings.get("threads", {}).get("user_id", ""))
        if user_id:
            self.settings.setdefault("threads", {})["user_id"] = user_id

        self.save_all()
        console.print("[green]Threads API設定完了[/green]")

    def configure_personas(self) -> None:
        console.print()
        console.print("[bold]キャラ（ペルソナ）設定[/bold]")
        console.print()

        personas = self.personas.get("personas", {})
        for pid, p in personas.items():
            console.print(f"  [cyan]{pid}[/cyan]: {p.get('name', '')} - {p.get('style', '')}")

        console.print()
        console.print("  [bold]1.[/bold] キャラを追加")
        console.print("  [bold]2.[/bold] キャラを編集")
        console.print("  [bold]3.[/bold] キャラを削除")
        console.print("  [bold]0.[/bold] 戻る")
        console.print()

        choice = Prompt.ask("選択", choices=["0", "1", "2", "3"])

        if choice == "1":
            self._add_persona()
        elif choice == "2":
            self._edit_persona()
        elif choice == "3":
            self._delete_persona()

    def _add_persona(self) -> None:
        console.print()
        console.print("[bold]新しいキャラを追加[/bold]")

        pid = Prompt.ask("ID（英数字）")
        name = Prompt.ask("名前")
        description = Prompt.ask("説明")
        style = Prompt.ask("スタイル（例: カジュアルで親しみやすい）")
        topics_str = Prompt.ask("トピック（カンマ区切り）")
        topics = [t.strip() for t in topics_str.split(",")]
        tone = Prompt.ask("トーン（例: 熱意のある）")
        hashtags_str = Prompt.ask("ハッシュタグ（カンマ区切り、#付き）")
        hashtags = [h.strip() for h in hashtags_str.split(",")]
        emoji = Confirm.ask("絵文字を使う？", default=True)
        post_format = Prompt.ask(
            "投稿フォーマット",
            default="{topic}について投稿して。200文字以内で、読みやすく、実用的なTipsを1つ教えて。"
        )

        self.personas.setdefault("personas", {})[pid] = {
            "name": name,
            "description": description,
            "style": style,
            "topics": topics,
            "tone": tone,
            "hashtags": hashtags,
            "emoji": emoji,
            "post_format": post_format,
        }
        self.save_all()
        console.print(f"[green]キャラ '{name}' を追加しました[/green]")

    def _edit_persona(self) -> None:
        pid = Prompt.ask("編集するキャラのID")
        personas = self.personas.get("personas", {})
        if pid not in personas:
            console.print("[red]キャラが見つかりません[/red]")
            return

        p = personas[pid]
        console.print(f"編集: [cyan]{p.get('name', pid)}[/cyan]")

        p["name"] = Prompt.ask("名前", default=p.get("name", ""))
        p["style"] = Prompt.ask("スタイル", default=p.get("style", ""))
        topics_str = Prompt.ask("トピック", default=", ".join(p.get("topics", [])))
        p["topics"] = [t.strip() for t in topics_str.split(",")]
        p["tone"] = Prompt.ask("トーン", default=p.get("tone", ""))
        hashtags_str = Prompt.ask("ハッシュタグ", default=", ".join(p.get("hashtags", [])))
        p["hashtags"] = [h.strip() for h in hashtags_str.split(",")]
        p["emoji"] = Confirm.ask("絵文字を使う？", default=p.get("emoji", True))
        p["post_format"] = Prompt.ask("投稿フォーマット", default=p.get("post_format", ""))

        self.save_all()
        console.print(f"[green]キャラ '{p['name']}' を更新しました[/green]")

    def _delete_persona(self) -> None:
        pid = Prompt.ask("削除するキャラのID")
        personas = self.personas.get("personas", {})
        if pid not in personas:
            console.print("[red]キャラが見つかりません[/red]")
            return

        if Confirm.ask(f"'{personas[pid].get('name', pid)}' を削除しますか？"):
            del personas[pid]
            self.save_all()
            console.print("[green]削除しました[/green]")

    def configure_affiliate(self) -> None:
        console.print()
        console.print("[bold]アフィリエイト設定[/bold]")

        enabled = Confirm.ask("アフィリンクを有効にする？", default=self.settings.get("affiliate", {}).get("enabled", True))
        self.settings.setdefault("affiliate", {})["enabled"] = enabled

        if enabled:
            freq = IntPrompt.ask("何回に1回リンクを貼る？", default=self.settings.get("affiliate", {}).get("frequency", 5))
            self.settings["affiliate"]["frequency"] = freq

            console.print()
            console.print("[bold]アフィリンク一覧[/bold]")
            links = self.settings.get("affiliate", {}).get("links", [])
            for i, link in enumerate(links):
                console.print(f"  {i+1}. {link.get('url', '')} ({link.get('context', '')})")

            console.print()
            console.print("  [bold]1.[/bold] リンクを追加")
            console.print("  [bold]2.[/bold] リンクを削除")
            console.print("  [bold]0.[/bold] 戻る")
            console.print()

            choice = Prompt.ask("選択", choices=["0", "1", "2"])

            if choice == "1":
                url = Prompt.ask("アフィリンクURL")
                context = Prompt.ask("説明（例: AI関連書籍）")
                keywords_str = Prompt.ask("関連キーワード（カンマ区切り）")
                keywords = [k.strip() for k in keywords_str.split(",")]
                links.append({"url": url, "context": context, "keywords": keywords})
                self.settings["affiliate"]["links"] = links
                console.print("[green]リンクを追加しました[/green]")

            elif choice == "2":
                idx = IntPrompt.ask("削除する番号") - 1
                if 0 <= idx < len(links):
                    links.pop(idx)
                    self.settings["affiliate"]["links"] = links
                    console.print("[green]削除しました[/green]")

        self.save_all()

    def configure_schedule(self) -> None:
        console.print()
        console.print("[bold]投稿スケジュール設定[/bold]")

        interval = IntPrompt.ask(
            "投稿間隔（時間）",
            default=self.settings.get("schedule", {}).get("interval_hours", 4)
        )
        max_posts = IntPrompt.ask(
            "1日最大投稿数",
            default=self.settings.get("schedule", {}).get("max_posts_per_day", 6)
        )
        randomize = IntPrompt.ask(
            "ランダム化（±分）",
            default=self.settings.get("schedule", {}).get("randomize_minutes", 30)
        )

        self.settings.setdefault("schedule", {})["interval_hours"] = interval
        self.settings["schedule"]["max_posts_per_day"] = max_posts
        self.settings["schedule"]["randomize_minutes"] = randomize

        self.save_all()
        console.print("[green]スケジュール設定完了[/green]")

    def post_once(self) -> None:
        console.print()
        console.print("[bold]1回投稿[/bold]")

        personas = self.personas.get("personas", {})
        console.print("キャラを選択:")
        for i, (pid, p) in enumerate(personas.items()):
            console.print(f"  {i+1}. {p.get('name', pid)}")

        choice = IntPrompt.ask("番号", default=1)
        persona_id = list(personas.keys())[choice - 1] if 0 < choice <= len(personas) else list(personas.keys())[0]

        topic = Prompt.ask("トピック（空欄でランダム）", default="")

        console.print("[dim]投稿中...[/dim]")

        try:
            from threads_sdk.autoposter.generator import PostGenerator
            from threads_sdk.autoposter.persona import PersonaManager
            from threads_sdk.auth import Credentials
            from threads_sdk.client import ThreadsClient

            pm = PersonaManager(PERSONAS_FILE)
            persona = pm.get(persona_id)

            llm_config = self.settings.get("llm", {})
            provider = llm_config.get("provider", "nvidia")

            gen = PostGenerator(
                provider=provider,
                nvidia_api_key=self.env.get("NVIDIA_API_KEY", ""),
                nvidia_model=llm_config.get("nvidia", {}).get("model", "meta/llama-3.1-8b-instruct"),
                local_url=llm_config.get("local", {}).get("url", "http://localhost:8080/v1"),
                local_model=llm_config.get("local", {}).get("model", "tq3-4s-27b"),
            )

            text = gen.generate(persona=persona, topic=topic)
            console.print()
            console.print(Panel(text, title="生成された投稿", border_style="green"))

            creds = Credentials(
                access_token=self.env.get("THREADS_TOKEN", ""),
                user_id=self.settings.get("threads", {}).get("user_id", ""),
            )
            client = ThreadsClient(credentials=creds)
            post = client.create_text_post(text)

            console.print(f"[green]投稿成功！ ID: {post.id}[/green]")

            # Save to history
            history_file = CONFIG_DIR / "post_history.json"
            history = []
            if history_file.exists():
                history = json.loads(history_file.read_text(encoding="utf-8"))
            history.append({
                "post_id": post.id,
                "text": text[:100],
                "persona_id": persona_id,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
            })
            history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

        except Exception as e:
            console.print(f"[red]エラー: {e}[/red]")

    def post_loop(self) -> None:
        console.print()
        console.print("[bold]自動投稿ループ開始[/bold]")
        console.print("[dim]Ctrl+C で停止[/dim]")
        console.print()

        try:
            from threads_sdk.autoposter.generator import PostGenerator
            from threads_sdk.autoposter.persona import PersonaManager
            from threads_sdk.autoposter.scheduler import AutoScheduler
            from threads_sdk.auth import Credentials
            from threads_sdk.client import ThreadsClient

            pm = PersonaManager(PERSONAS_FILE)
            llm_config = self.settings.get("llm", {})
            provider = llm_config.get("provider", "nvidia")

            gen = PostGenerator(
                provider=provider,
                nvidia_api_key=self.env.get("NVIDIA_API_KEY", ""),
                nvidia_model=llm_config.get("nvidia", {}).get("model", "meta/llama-3.1-8b-instruct"),
                local_url=llm_config.get("local", {}).get("url", "http://localhost:8080/v1"),
                local_model=llm_config.get("local", {}).get("model", "tq3-4s-27b"),
            )

            creds = Credentials(
                access_token=self.env.get("THREADS_TOKEN", ""),
                user_id=self.settings.get("threads", {}).get("user_id", ""),
            )
            client = ThreadsClient(credentials=creds)

            scheduler = AutoScheduler(
                generator=gen,
                persona_manager=pm,
                threads_client=client,
                config=self.settings,
            )
            scheduler.run_loop()

        except KeyboardInterrupt:
            console.print("\n[green]停止しました[/green]")
        except Exception as e:
            console.print(f"[red]エラー: {e}[/red]")

    def show_history(self) -> None:
        history_file = CONFIG_DIR / "post_history.json"
        if not history_file.exists():
            console.print("[dim]投稿履歴なし[/dim]")
            return

        history = json.loads(history_file.read_text(encoding="utf-8"))
        if not history:
            console.print("[dim]投稿履歴なし[/dim]")
            return

        table = Table(title="投稿履歴")
        table.add_column("#", style="dim")
        table.add_column("日時")
        table.add_column("キャラ")
        table.add_column("テキスト")
        table.add_column("ID")

        for i, post in enumerate(history[-20:], 1):
            table.add_row(
                str(i),
                post.get("timestamp", "")[:16],
                post.get("persona_id", ""),
                post.get("text", "")[:40],
                post.get("post_id", ""),
            )

        console.print(table)
        console.print(f"[dim]全{len(history)}件[/dim]")
