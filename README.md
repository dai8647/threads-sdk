# threads-sdk

Modern Python SDK + CLI for Meta's [Threads API](https://developers.facebook.com/docs/threads/).

[![PyPI version](https://img.shields.io/pypi/v/threads-sdk)](https://pypi.org/project/threads-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Sync + Async** — `ThreadsClient` and `AsyncThreadsClient`
- **Type-safe** — Pydantic v2 models, full type hints
- **CLI** — Post, read, and analyze from the terminal
- **Auto token refresh** — OAuth 2.0 with long-lived tokens

## Installation

```bash
pip install threads-sdk
```

## Quick Start

### Python SDK

```python
from threads_sdk import ThreadsClient, Credentials

creds = Credentials(access_token="your_token", user_id="your_user_id")
client = ThreadsClient(credentials=creds)

# Publish a post
post = client.create_text_post("Hello from threads-sdk!")

# List your posts
posts = client.get_user_posts(limit=10)

# Get insights
insights = client.get_post_insights(post.id)
print(f"Views: {insights.views}, Likes: {insights.likes}")
```

### Async

```python
import asyncio
from threads_sdk import AsyncThreadsClient, Credentials

async def main():
    creds = Credentials(access_token="your_token", user_id="your_user_id")
    async with AsyncThreadsClient(credentials=creds) as client:
        post = await client.create_text_post("Async post!")
        print(f"Posted: {post.id}")

asyncio.run(main())
```

### CLI

```bash
# First-time setup
threads-sdk auth

# Post
threads-sdk post "Hello World!"
threads-sdk post --image "https://example.com/photo.jpg" "Photo post"

# List posts
threads-sdk posts --limit 5

# View replies
threads-sdk replies <post-id>

# View insights
threads-sdk insights <post-id>
```

## API Reference

### ThreadsClient / AsyncThreadsClient

| Method | Description |
|--------|-------------|
| `create_text_post(text)` | Publish text-only post |
| `create_image_post(url, text)` | Publish image post |
| `create_video_post(url, text)` | Publish video post |
| `reply_to_post(post_id, text)` | Reply to a post |
| `get_user_posts(limit)` | List user's posts |
| `get_post_replies(post_id)` | Get post replies |
| `get_post_insights(post_id)` | Get post metrics |
| `get_user_profile(user_id)` | Get user profile |

### Models

- `ThreadsPost` — Post data (id, text, media_type, permalink, ...)
- `PostReply` — Reply data
- `PostInsights` — Metrics (views, likes, replies, reposts, quotes)
- `UserProfile` — Profile data (id, username, name, biography)
- `ContainerStatus` — Container processing status

## Getting a Threads API Token

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create an App → Add "Threads" use case
3. Generate a User Access Token with required scopes
4. Use `threads-sdk auth` for OAuth flow, or set token directly

## Contributing

```bash
git clone https://github.com/dai86/threads-sdk
cd threads-sdk
pip install -e ".[dev]"
pytest
```

## Support

If you find this useful, consider supporting:

- [GitHub Sponsors](https://github.com/sponsors/dai86)
- [Ko-fi](https://ko-fi.com/dai86)

## License

MIT
