Title: Show HN: threads-sdk – Modern Python SDK + CLI for Meta's Threads API

I built threads-sdk, a Python SDK and CLI for Meta's Threads API.

The existing options (threads-api, pythreads) are either scraping-based or abandoned (last update: 2 years ago). I wanted something production-ready with modern Python practices.

Features:
- Sync + Async support via httpx
- Type-safe with Pydantic v2
- CLI with 6 commands (post, posts, replies, insights, reply, auth)
- OAuth 2.0 with automatic token refresh
- MIT licensed

GitHub: https://github.com/dai8647/threads-sdk

pip install threads-sdk

Example usage:

    from threads_sdk import ThreadsClient, Credentials

    client = ThreadsClient(credentials=Credentials(access_token="...", user_id="..."))
    client.create_text_post("Hello from Python!")
    posts = client.get_user_posts(limit=10)
    insights = client.get_post_insights(post.id)

Feedback welcome!
