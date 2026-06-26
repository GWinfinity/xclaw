# xClaw Tesla Browser AI

AI copilot for Tesla vehicles that runs entirely in the browser — no CAN
hardware, no OBD-II cables, no risk of VIN bans from bus injection.

It connects to your own xClaw backend, which talks to Tesla's official Fleet
API and your preferred LLM API.

## Two ways to use it

### 1. Tesla In-Car Browser (recommended)

1. Start the xClaw backend:
   ```bash
   cd /path/to/xClaw
   python -m packages.tesla_client.browser_server
   ```
2. Make sure the backend is reachable from your car (same WiFi, tailscale,
   public domain with HTTPS, etc.).
3. In your Tesla, open the browser and go to:
   ```
   http://<your-backend-ip>:8080/dashboard/
   ```
4. Bookmark the page.

### 2. Chrome Browser Extension

1. Open Chrome → Extensions → Developer mode → Load unpacked.
2. Select this `extensions/tesla_browser` folder.
3. Click the extension icon, set your backend URL.
4. Open any `tesla.com` page to see the floating xClaw button, or click
   "Open Dashboard" in the popup.

## Backend Configuration

Create a `.env` file in the project root or export these variables:

```bash
# Tesla Fleet API
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
TESLA_REDIRECT_URI=https://your-domain.com/callback
TESLA_REGION=cn
TESLA_ACCESS_TOKEN=your_access_token
TESLA_REFRESH_TOKEN=your_refresh_token
TESLA_VIN=your_vin_optional

# LLM (example: OpenAI)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

To get Tesla tokens, use the OAuth flow in `packages.tesla_client.client` or
any Tesla Fleet API onboarding tool.

## Architecture

```
┌─────────────────┐      HTTPS/WSS       ┌──────────────────────┐
│  Tesla Browser  │ ◄──────────────────► │  xClaw Backend       │
│  (dashboard)    │                      │  (browser_server.py) │
└─────────────────┘                      └──────────┬───────────┘
                                                    │
                       ┌────────────────────────────┘
                       ▼
            ┌─────────────────────┐
            │  Tesla Fleet API    │
            │  (official, safe)   │
            └─────────────────────┘
                       ▲
                       │
            ┌─────────────────────┐
            │  User LLM API       │
            │  (OpenAI/Kimi/etc.) │
            └─────────────────────┘
```

## Limitations

- The browser approach cannot access the car's CAN bus directly.
- Command latency is higher than a CAN-based solution (goes through Tesla
  servers).
- Tesla Fleet API has rate limits.

## Safety

- No vehicle commands are executed automatically; user approval is required.
- Backend defaults to read-only Fleet API calls unless `/api/command` is
  explicitly invoked.
