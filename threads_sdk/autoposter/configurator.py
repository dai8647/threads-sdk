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

# 9router経由で利用可能なモデル一覧
NINEROUTER_MODELS = {
    "1": {"id": "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1", "name": "Nemotron Super 49B（高品質）"},
    "2": {"id": "nvidia/deepseek-ai/deepseek-v4-flash", "name": "DeepSeek V4 Flash（高速）"},
    "3": {"id": "nvidia/deepseek-ai/deepseek-v4-pro", "name": "DeepSeek V4 Pro（高品質）"},
    "4": {"id": "opencode-go/kimi-k2.6", "name": "Kimi K2.6（無料）"},
    "5": {"id": "opencode-go/kimi-k2.5", "name": "Kimi K2.5（無料）"},
    "6": {"id": "opencode-go/glm-5.1", "name": "GLM 5.1（無料）"},
    "7": {"id": "opencode-go/glm-5", "name": "GLM 5（無料）"},
    "8": {"id": "opencode-go/qwen3.5-plus", "name": "Qwen 3.5 Plus（無料）"},
    "9": {"id": "opencode-go/qwen3.6-plus", "name": "Qwen 3.6 Plus（無料）"},
    "10": {"id": "opencode-go/mimo-v2-pro", "name": "Mimo V2 Pro（無料）"},
    "11": {"id": "opencode-go/mimo-v2-omni", "name": "Mimo V2 Omni（無料）"},
    "12": {"id": "opencode-go/minimax-m2.7", "name": "MiniMax M2.7（無料）"},
}


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
        console.print("  [bold]2.[/bold] LLM設定（9router / NVIDIA / ローカル）")
        console.print("  [bold]3.[/bold] Threads API設定")
        console.print("  [bold]4.[/bold] キャラ（ペルソナ）管理")
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

        provider = llm.get("provider", "9router")
        model = ""
        if provider == "9router":
            model = llm.get("9router", {}).get("model", "未設定")
        elif provider == "nvidia":
            model = llm.get("nvidia", {}).get("model", "未設定")
        elif provider == "local":
            model = llm.get("local", {}).get("model", "未設定")

        table = Table(title="現在の設定", show_lines=True)
        table.add_column("項目", style="cyan")
        table.add_column("値")

        table.add_row("LLMプロバイダー", provider)
        table.add_row("モデル", model)
        table.add_row("9router URL", llm.get("9router", {}).get("url", "http://localhost:20128/v1"))
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
            pt.add_column("トピック")
            for pid, p in personas.items():
                topics = ", ".join(p.get("topics", [])[:3])
                if len(p.get("topics", [])) > 3:
                    topics += "..."
                pt.add_row(pid, p.get("name", ""), p.get("style", ""), topics)
            console.print(pt)

    def configure_llm(self) -> None:
        console.print()
        console.print("[bold]LLM設定[/bold]")
        current = self.settings.get("llm", {}).get("provider", "9router")
        console.print(f"現在: [cyan]{current}[/cyan]")
        console.print()
        console.print("  [bold]1.[/bold] 9router（無料・推奨）")
        console.print("     → localhost:20128 経由で多数のモデルを利用可能")
        console.print("     → OpenCode, NVIDIA NIM 等")
        console.print("  [bold]2.[/bold] NVIDIA API直接（有料・高品質）")
        console.print("  [bold]3.[/bold] ローカルLLM（無料・localhost:8080）")
        console.print()

        choice = Prompt.ask("選択", choices=["1", "2", "3"])

        if choice == "1":
            self._configure_9router()
        elif choice == "2":
            self._configure_nvidia_direct()
        elif choice == "3":
            self._configure_local()

        self.save_all()

    def _configure_9router(self) -> None:
        self.settings.setdefault("llm", {})["provider"] = "9router"
        url = Prompt.ask("9router URL", default="http://localhost:20128/v1")
        self.settings["llm"].setdefault("9router", {})["url"] = url

        console.print()
        console.print("[bold]利用可能なモデル:[/bold]")
        for key, model in NINEROUTER_MODELS.items():
            console.print(f"  [cyan]{key}[/cyan]. {model['name']}")
        console.print()

        model_choice = Prompt.ask("モデルを選択", choices=list(NINEROUTER_MODELS.keys()), default="4")
        selected = NINEROUTER_MODELS[model_choice]
        self.settings["llm"]["9router"]["model"] = selected["id"]
        console.print(f"[green]9router設定完了: {selected['name']}[/green]")

    def _configure_nvidia_direct(self) -> None:
        self.settings.setdefault("llm", {})["provider"] = "nvidia"
        api_key = Prompt.ask("NVIDIA APIキー", default=self.env.get("NVIDIA_API_KEY", ""))
        if api_key:
            self.env["NVIDIA_API_KEY"] = api_key
        model = Prompt.ask("モデル", default="meta/llama-3.1-8b-instruct")
        self.settings["llm"].setdefault("nvidia", {})["model"] = model
        console.print("[green]NVIDIA API設定完了[/green]")

    def _configure_local(self) -> None:
        self.settings.setdefault("llm", {})["provider"] = "local"
        url = Prompt.ask("ローカルLLM URL", default="http://localhost:8080/v1")
        model = Prompt.ask("モデル名", default="tq3-4s-27b")
        self.settings["llm"].setdefault("local", {})["url"] = url
        self.settings["llm"]["local"]["model"] = model
        console.print("[green]ローカルLLM設定完了[/green]")

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
        console.print("[bold]キャラ（ペルソナ）管理[/bold]")
        console.print()

        personas = self.personas.get("personas", {})
        if personas:
            for pid, p in personas.items():
                topics = ", ".join(p.get("topics", [])[:3])
                console.print(f"  [cyan]{pid}[/cyan]: {p.get('name', '')} - {p.get('style', '')} [{topics}]")
        else:
            console.print("  [dim]キャラ未登録[/dim]")

        console.print()
        console.print("  [bold]1.[/bold] 新しいキャラを作成")
        console.print("  [bold]2.[/bold] キャラを編集")
        console.print("  [bold]3.[/bold] キャラを削除")
        console.print("  [bold]4.[/bold] テンプレートから作成")
        console.print("  [bold]0.[/bold] 戻る")
        console.print()

        choice = Prompt.ask("選択", choices=["0", "1", "2", "3", "4"])

        if choice == "1":
            self._create_persona()
        elif choice == "2":
            self._edit_persona()
        elif choice == "3":
            self._delete_persona()
        elif choice == "4":
            self._create_from_template()

    def _create_persona(self) -> None:
        console.print()
        console.print(Panel("[bold]新しいキャラを作成[/bold]", border_style="cyan"))
        console.print()

        pid = Prompt.ask("ID（英数字）")
        name = Prompt.ask("名前")

        console.print()
        console.print("[bold]スタイルを選択:[/bold]")
        console.print("  1. カジュアル（親しみやすい）")
        console.print("  2. フレンドリー（ストーリー調）")
        console.print("  3. 丁寧（フォーマル）")
        console.print("  4. 熱意のある（情熱的）")
        console.print("  5. 知的（専門的）")
        console.print("  6. ユーモア（面白い）")
        console.print("  7. 自分で入力")
        style_choice = Prompt.ask("選択", choices=["1", "2", "3", "4", "5", "6", "7"], default="1")
        styles = {"1": "カジュアルで親しみやすい", "2": "フレンドリーでストーリー調", "3": "丁寧でフォーマル", "4": "熱意のある、情熱的", "5": "知的で専門的", "6": "ユーモアがあって面白い"}
        if style_choice == "7":
            style = Prompt.ask("スタイルを入力")
        else:
            style = styles[style_choice]

        console.print()
        console.print("[bold]トピックを選択（複数選択可）:[/bold]")
        console.print("  1. テック（Python/AI/OSS）")
        console.print("  2. ビジネス（起業/マーケ）")
        console.print("  3. 生活（ライフハック/時短）")
        console.print("  4. エンタメ（映画/音楽/ゲーム）")
        console.print("  5. 美容/ファッション")
        console.print("  6. 食べ物/グルメ")
        console.print("  7. 旅行/アウトドア")
        console.print("  8. 健康/フィットネス")
        console.print("  9. 自分で入力")
        console.print("  0. 上記を全て選択")
        topic_choice = Prompt.ask("選択（カンマ区切りで複数可、例: 1,2,5）")
        topic_map = {
            "1": ["Python", "AI", "OSS", "プログラミング"],
            "2": ["ビジネス", "起業", "マーケティング", "副業"],
            "3": ["ライフハック", "時短", "生産性", "整理整頓"],
            "4": ["エンタメ", "映画", "音楽", "ゲーム"],
            "5": ["美容", "ファッション", "スキンケア"],
            "6": ["食べ物", "グルメ", "料理", "レストラン"],
            "7": ["旅行", "アウトドア", "観光"],
            "8": ["健康", "フィットネス", "トレーニング"],
        }
        topics = []
        if "0" in topic_choice:
            for v in topic_map.values():
                topics.extend(v)
        else:
            for c in topic_choice.split(","):
                c = c.strip()
                if c in topic_map:
                    topics.extend(topic_map[c])
                elif c == "9":
                    custom = Prompt.ask("トピックを入力（カンマ区切り）")
                    topics.extend([t.strip() for t in custom.split(",")])
        if not topics:
            topics = ["一般"]

        hashtags_str = Prompt.ask("ハッシュタグ（カンマ区切り、#付き）", default="#Threads")
        emoji = Confirm.ask("絵文字を使う？", default=True)

        console.print()
        console.print("[bold]投稿ルール:[/bold]")
        console.print("  1. 200文字以内（標準）")
        console.print("  2. 140文字以内（短文）")
        console.print("  3. 500文字以内（長文）")
        console.print("  4. 自分で入力")
        rule_choice = Prompt.ask("選択", choices=["1", "2", "3", "4"], default="1")
        rule_map = {
            "1": "200文字以内で投稿して。ハッシュタグは3-5個つけて。",
            "2": "140文字以内で簡潔に投稿して。ハッシュタグは2-3個つけて。",
            "3": "500文字以内で詳しく投稿して。ハッシュタグは5-7個つけて。",
        }
        if rule_choice == "4":
            rules = Prompt.ask("ルールを入力")
        else:
            rules = rule_map[rule_choice]

        self.personas.setdefault("personas", {})[pid] = {
            "name": name,
            "description": "",
            "style": style,
            "topics": topics,
            "tone": style,
            "hashtags": [h.strip() for h in hashtags_str.split(",") if h.strip()],
            "emoji": emoji,
            "post_format": f"{{topic}}について投稿して。{rules}",
        }
        self.save_all()
        console.print(f"\n[green]キャラ '{name}' を作成しました！[/green]")

    def _create_from_template(self) -> None:
        console.print()
        console.print("[bold]テンプレートから作成[/bold]")
        console.print()
        console.print("  [bold]1.[/bold] テック系エンジニア（Python/AI/OSS）")
        console.print("  [bold]2.[/bold] AI研究者（機械学習/深層学習）")
        console.print("  [bold]3.[/bold] カジュアルコーダー（日常開発）")
        console.print("  [bold]4.[/bold] ビジネス系（起業/マーケティング）")
        console.print("  [bold]5.[/bold] 生活系（ライフハック/生産性）")
        console.print()

        choice = Prompt.ask("テンプレートを選択", choices=["1", "2", "3", "4", "5"])

        templates = {
            "1": {
                "name": "テックエンジニア",
                "description": "Python/AI/OSSのTipsを発信",
                "style": "カジュアルで親しみやすい",
                "topics": ["Python", "AI", "OSS", "プログラミング", "CLIツール", "開発効率化"],
                "tone": "熱意のある、時にユーモアを交えて",
                "hashtags": ["#Python", "#AI", "#OpenSource", "#プログラミング"],
                "emoji": True,
                "post_format": "{topic}について投稿して。200文字以内で、読みやすく、実用的なTipsを1つ教えて。ハッシュタグは3-5個つけて。",
            },
            "2": {
                "name": "AI研究者",
                "description": "機械学習・深層学習の最新情報を発信",
                "style": "丁寧で専門的",
                "topics": ["機械学習", "深層学習", "LLM", "データサイエンス", "AI倫理"],
                "tone": "知的で冷静、時折ネタを交えて",
                "hashtags": ["#機械学習", "#AI", "#LLM", "#データサイエンス"],
                "emoji": False,
                "post_format": "{topic}について投稿して。200文字以内で、専門的だけど分かりやすく解説して。ハッシュタグは3-5個つけて。",
            },
            "3": {
                "name": "カジュアルコーダー",
                "description": "日常の開発エピソードや学びを共有",
                "style": "フレンドリーでストーリー調",
                "topics": ["日常開発", "学習記録", "ツール紹介", "エピソード", "生産性"],
                "tone": "親しみやすく、共感を呼ぶ",
                "hashtags": ["#エンジニア", "#開発", "#プログラミング"],
                "emoji": True,
                "post_format": "{topic}について投稿して。200文字以内で、共感できるような体験談やTipsを教えて。ハッシュタグは3-5個つけて。",
            },
            "4": {
                "name": "ビジネス系",
                "description": "起業・マーケティング・ビジネスTips",
                "style": "プロフェッショナルだけど親しみやすい",
                "topics": ["起業", "マーケティング", "SNS運用", "副業", "ビジネス", "投資"],
                "tone": "信頼感のある、具体的な数字を使う",
                "hashtags": ["#ビジネス", "#起業", "#マーケティング", "#副業"],
                "emoji": True,
                "post_format": "{topic}について投稿して。200文字以内で、具体的なアクションアイテム付きで教えて。ハッシュタグは3-5個つけて。",
            },
            "5": {
                "name": "生活系",
                "description": "ライフハック・生産性・日常Tips",
                "style": "温かみのある、共感型",
                "topics": ["ライフハック", "生産性", "健康管理", "節約", "時短", "整理整頓"],
                "tone": "優しく、実践的な",
                "hashtags": ["#ライフハック", "#生産性", "#日常"],
                "emoji": True,
                "post_format": "{topic}について投稿して。200文字以内で、今日からできる実践的なTipsを1つ教えて。ハッシュタグは3-5個つけて。",
            },
        }

        template = templates[choice]
        pid = Prompt.ask("ID（英数字）", default=f"custom_{choice}")
        name = Prompt.ask("名前", default=template["name"])

        # カスタマイズ
        console.print()
        console.print("[dim]そのままEnterでテンプレートのまま。変更したい場合は入力。[/dim]")
        style = Prompt.ask("スタイル", default=template["style"])
        topics_str = Prompt.ask("トピック", default=", ".join(template["topics"]))
        tone = Prompt.ask("トーン", default=template["tone"])
        hashtags_str = Prompt.ask("ハッシュタグ", default=", ".join(template["hashtags"]))
        emoji = Confirm.ask("絵文字を使う？", default=template["emoji"])

        self.personas.setdefault("personas", {})[pid] = {
            "name": name,
            "description": template["description"],
            "style": style,
            "topics": [t.strip() for t in topics_str.split(",") if t.strip()],
            "tone": tone,
            "hashtags": [h.strip() for h in hashtags_str.split(",") if h.strip()],
            "emoji": emoji,
            "post_format": template["post_format"],
        }
        self.save_all()
        console.print(f"\n[green]キャラ '{name}' を作成しました！[/green]")

    def _edit_persona(self) -> None:
        personas = self.personas.get("personas", {})
        if not personas:
            console.print("[red]キャラが登録されていません[/red]")
            return

        console.print()
        persona_list = list(personas.items())
        for i, (pid, p) in enumerate(persona_list):
            console.print(f"  {i+1}. {p.get('name', pid)} ({pid})")
        console.print()

        choice = IntPrompt.ask("編集するキャラの番号")
        if choice < 1 or choice > len(persona_list):
            console.print("[red]無効な選択です[/red]")
            return

        pid = persona_list[choice - 1][0]
        p = personas[pid]
        console.print(f"\n編集: [cyan]{p.get('name', pid)}[/cyan]")
        console.print("[dim]そのままEnterで現在の値を維持[/dim]")
        console.print()

        p["name"] = Prompt.ask("名前", default=p.get("name", ""))
        p["description"] = Prompt.ask("説明", default=p.get("description", ""))
        p["style"] = Prompt.ask("スタイル", default=p.get("style", ""))
        topics_str = Prompt.ask("トピック", default=", ".join(p.get("topics", [])))
        p["topics"] = [t.strip() for t in topics_str.split(",") if t.strip()]
        p["tone"] = Prompt.ask("トーン", default=p.get("tone", ""))
        hashtags_str = Prompt.ask("ハッシュタグ", default=", ".join(p.get("hashtags", [])))
        p["hashtags"] = [h.strip() for h in hashtags_str.split(",") if h.strip()]
        p["emoji"] = Confirm.ask("絵文字を使う？", default=p.get("emoji", True))
        p["post_format"] = Prompt.ask("投稿フォーマット", default=p.get("post_format", ""))

        self.save_all()
        console.print(f"\n[green]キャラ '{p['name']}' を更新しました[/green]")

    def _delete_persona(self) -> None:
        personas = self.personas.get("personas", {})
        if not personas:
            console.print("[red]キャラが登録されていません[/red]")
            return

        console.print()
        persona_list = list(personas.items())
        for i, (pid, p) in enumerate(persona_list):
            console.print(f"  {i+1}. {p.get('name', pid)} ({pid})")
        console.print()

        choice = IntPrompt.ask("削除するキャラの番号")
        if choice < 1 or choice > len(persona_list):
            console.print("[red]無効な選択です[/red]")
            return

        pid = persona_list[choice - 1][0]
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
        if not personas:
            console.print("[red]キャラが未登録です。まずキャラを登録してください。[/red]")
            return

        console.print("キャラを選択:")
        persona_list = list(personas.items())
        for i, (pid, p) in enumerate(persona_list):
            console.print(f"  {i+1}. {p.get('name', pid)} - {p.get('style', '')}")
        console.print(f"  [cyan]n.[/cyan] 新しいキャラを作成して使う")
        console.print()

        choice = Prompt.ask("番号")

        if choice == "n":
            self._create_persona()
            persona_list = list(self.personas.get("personas", {}).items())
            persona_id = persona_list[-1][0]
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(persona_list):
                persona_id = persona_list[idx][0]
            else:
                console.print("[red]無効な選択です[/red]")
                return

        topic = Prompt.ask("トピック（空欄でランダム）", default="")

        # 画像投稿オプション
        console.print()
        console.print("投稿タイプ:")
        console.print("  1. テキストのみ")
        console.print("  2. 画像＋テキスト（AI画像生成）")
        console.print("  3. 画像＋テキスト（URL指定）")
        post_type = Prompt.ask("選択", choices=["1", "2", "3"], default="1")

        image_url = None
        if post_type == "2":
            console.print("[dim]画像を生成してアップロード中...[/dim]")
            try:
                from threads_sdk.autoposter.imagegen import ImageGenerator
                img_gen = ImageGenerator(output_dir=str(CONFIG_DIR / "generated_images"))
                image_url = img_gen.generate_for_post(topic or "technology", persona.style)
                if image_url:
                    console.print(f"[green]画像URL: {image_url}[/green]")
                else:
                    console.print("[red]画像生成/アップロードに失敗しました[/red]")
                    image_url = ""
            except Exception as e:
                console.print(f"[red]画像生成エラー: {e}[/red]")
                image_url = ""
        elif post_type == "3":
            image_url = Prompt.ask("画像URL")

        console.print("[dim]投稿中...[/dim]")

        try:
            from threads_sdk.autoposter.generator import PostGenerator
            from threads_sdk.autoposter.persona import PersonaManager
            from threads_sdk.auth import Credentials
            from threads_sdk.client import ThreadsClient

            pm = PersonaManager(PERSONAS_FILE)
            persona = pm.get(persona_id)

            llm_config = self.settings.get("llm", {})
            provider = llm_config.get("provider", "9router")

            gen = PostGenerator(
                provider=provider,
                nvidia_api_key=self.env.get("NVIDIA_API_KEY", ""),
                nvidia_model=llm_config.get("nvidia", {}).get("model", "meta/llama-3.1-8b-instruct"),
                nvidia_base_url=llm_config.get("nvidia", {}).get("base_url", "https://integrate.api.nvidia.com/v1"),
                local_url=llm_config.get("local", {}).get("url", "http://localhost:8080/v1"),
                local_model=llm_config.get("local", {}).get("model", "tq3-4s-27b"),
                ninerouter_url=llm_config.get("9router", {}).get("url", "http://localhost:20128/v1"),
                ninerouter_model=llm_config.get("9router", {}).get("model", "opencode-go/kimi-k2.6"),
            )

            text = gen.generate(persona=persona, topic=topic)
            console.print()
            console.print(Panel(text, title="生成された投稿", border_style="green"))

            creds = Credentials(
                access_token=self.env.get("THREADS_TOKEN", ""),
                user_id=self.settings.get("threads", {}).get("user_id", ""),
            )
            client = ThreadsClient(credentials=creds)

            if image_url:
                post = client.create_image_post(image_url, text)
            else:
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
            provider = llm_config.get("provider", "9router")

            gen = PostGenerator(
                provider=provider,
                nvidia_api_key=self.env.get("NVIDIA_API_KEY", ""),
                nvidia_model=llm_config.get("nvidia", {}).get("model", "meta/llama-3.1-8b-instruct"),
                nvidia_base_url=llm_config.get("nvidia", {}).get("base_url", "https://integrate.api.nvidia.com/v1"),
                local_url=llm_config.get("local", {}).get("url", "http://localhost:8080/v1"),
                local_model=llm_config.get("local", {}).get("model", "tq3-4s-27b"),
                ninerouter_url=llm_config.get("9router", {}).get("url", "http://localhost:20128/v1"),
                ninerouter_model=llm_config.get("9router", {}).get("model", "opencode-go/kimi-k2.6"),
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
