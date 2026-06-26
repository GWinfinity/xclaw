"""
Tesla Browser AI Server Example

Starts the xClaw backend that serves the Tesla browser AI dashboard.

Prerequisites:
1. Set environment variables (see .env.example):
   - TESLA_CLIENT_ID, TESLA_CLIENT_SECRET
   - TESLA_ACCESS_TOKEN, TESLA_REFRESH_TOKEN (or run OAuth flow first)
   - LLM_PROVIDER and corresponding API key
2. Run: python examples/tesla_browser_server.py
3. Open http://localhost:8080/dashboard/ in your Tesla browser or Chrome.
"""

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from packages.tesla_client.browser_server import main

if __name__ == "__main__":
    main()
