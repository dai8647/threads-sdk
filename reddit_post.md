Title: I built threads-sdk: a modern Python SDK + CLI for Meta's Threads API

Hey r/Python! 👋

I just released **threads-sdk** — a modern Python SDK and CLI for Meta's Threads API.

## Why?

The existing options are:
- `threads-api` — unofficial, scraping-based, fragile
- `pythreads` — official API wrapper, but last updated July 2024 (2 years ago), still in beta

I wanted something production-ready with modern Python practices.

## What it does

```python
from threads_sdk import ThreadsClient, Credentials

client = ThreadsClient(credentials=Credentials(access_token="...", user_id="..."))
client.create_text_post("Hello from Python!")
posts = client.get_user_posts(limit=10)
insights = client.get_post_insights(post.id)
```

Also supports **async**:
```python
async with AsyncThreadsClient(credentials=creds) as client:
    await client.create_text_post("Async post!")
```

And a **CLI**:
```bash
threads-sdk post "Hello World!"
threads-sdk posts --limit 5
threads-sdk insights <post-id>
```

## Features

- Sync + Async support (httpx)
- Type-safe with Pydantic v2 models
- Full CLI with 6 commands
- OAuth 2.0 with automatic token refresh
- MIT licensed

## GitHub

[github.com/dai8647/threads-sdk](https://github.com/dai8647/threads-sdk)

```bash
pip install threads-sdk
```

Would love feedback! If you find it useful, consider starring the repo or supporting on [Ko-fi](https://ko-fi.com/danny8647).
