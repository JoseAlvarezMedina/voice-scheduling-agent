# Voice Scheduling Agent

A real-time voice assistant that books Google Calendar events through natural conversation.
Built with VAPI, FastAPI, and the Google Calendar API. Deployed on Railway.

---

## Live demo

**Agent URL:** https://web-production-ff2be.up.railway.app

**Demo video:** https://www.loom.com/share/084e4a6da1484422988917d56ad31c82

**How to test:**
1. Open the URL above in Chrome
2. Click **Start call** and allow microphone access when prompted
3. Follow the assistant's prompts — provide your name, a date, a time, and optionally a meeting title
4. Confirm the details when the assistant reads them back
5. Check your Google Calendar — the event will appear within seconds

---

## Calendar integration

The agent uses the **Google Calendar API** with a **service account** for authentication. A service account is a non-human Google identity that can create and manage calendar events programmatically without requiring an OAuth redirect flow — making it ideal for automated agents.

**How it works:**

1. The service account credentials are stored as a base64-encoded JSON string in the `GOOGLE_CREDENTIALS_B64` environment variable
2. At runtime, `calendar_service.py` decodes this string, loads it into a `google.oauth2.service_account.Credentials` object, and builds an authenticated Google Calendar API client
3. The target calendar (`GOOGLE_CALENDAR_ID`) is a personal Google Calendar that has been shared with the service account email with "Make changes to events" permission
4. Events are created in the `America/Bogota` timezone (UTC-5) to match the user's local time

---

## How to run locally

### Prerequisites
- Python 3.11+
- A Google Cloud service account JSON key with Calendar API enabled
- A VAPI account with an assistant configured

### Setup

```bash
git clone https://github.com/JoseAlvarezMedina/voice-scheduling-agent
cd voice-scheduling-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Base64-encode your service account key and add it to `.env`:

```powershell
# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\key.json")) | Set-Clipboard
```

```bash
# macOS/Linux
base64 -i path/to/key.json | pbcopy
```

### Run

```bash
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Open `/` for the voice widget or `/docs` for the auto-generated API documentation.

To test the webhook directly without VAPI:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "type": "tool-calls",
      "toolCallList": [{
        "id": "test-001",
        "function": {
          "name": "create_calendar_event",
          "arguments": {
            "name": "Jose Alvarez",
            "date": "2026-04-06",
            "time": "14:00",
            "title": "Test Meeting"
          }
        }
      }]
    }
  }'
```

---

## Architecture

```
Browser (VAPI web widget)
        |
        | WebRTC voice stream
        v
   VAPI Platform
   ┌─────────────────────────────────┐
   │  STT (Deepgram) → LLM → TTS   │
   └─────────────────────────────────┘
        |
        | HTTP POST — tool call webhook
        v
   FastAPI backend (Railway)
   ┌──────────────────┐   ┌──────────────────┐
   │ POST /webhook    │ → │ calendar_service  │
   │ Webhook handler  │   │ Service account   │
   └──────────────────┘   └──────────────────┘
        |
        | Google Calendar REST API
        v
   Google Calendar
```

---

## Design decisions

### Custom backend over VAPI's native Google Calendar tool

VAPI offers a native Google Calendar integration that requires no backend code. I chose to build a custom FastAPI webhook instead for three reasons. First, it keeps the calendar credentials fully under my control — they never leave my infrastructure. Second, it gives me a real backend layer where I can add validation, error handling, logging, and future features like timezone detection or email confirmation. Third, it demonstrates the full integration pattern that would be used in a production system where the calendar is just one of many services the agent might need to call.

### System prompt design

The system prompt enforces a strict linear flow: collect name, collect date, collect time, collect optional title, read back all details, wait for explicit confirmation, then and only then call the tool. This prevents the common failure mode where a voice agent books an event before the user has finished speaking or before all required fields are collected.

The prompt also separates the internal data format from the spoken format — the LLM converts dates to `YYYY-MM-DD` and times to `HH:MM` before calling the tool, but always speaks them in natural language ("April 6th at 8:00 AM") to the user. This avoids the jarring experience of hearing "two zero two six zero four zero six" read aloud, which was an early issue caught during testing.

### Service account over OAuth

OAuth2 requires a redirect flow and token refresh management. For an agent that books events into a single known calendar, a service account is simpler, more reliable, and has no expiry issues. The calendar owner simply shares their calendar with the service account email once, and the agent has permanent write access.

### Railway over Hugging Face Spaces

Hugging Face Spaces goes to sleep after inactivity, introducing cold starts of 10-30 seconds. For a VAPI webhook that needs to respond within the tool call timeout window (20 seconds), a cold start is a critical failure. Railway keeps the server warm on the free tier, making it the right choice for a latency-sensitive voice agent.

---

## What I would add with more time

- Webhook signature validation using `VAPI_SECRET` to verify requests genuinely come from VAPI
- Timezone detection from the user's browser or by asking during the conversation
- Email confirmation sent to the attendee after booking
- Support for rescheduling and cancellation via voice
- Retry logic with exponential backoff on Google Calendar API failures
- A proper test suite for `calendar_service.py`

---

## Tech stack

| Layer | Technology |
|---|---|
| Voice platform | VAPI |
| LLM | GPT-4.1 (via VAPI) |
| STT | Deepgram (via VAPI) |
| TTS | VAPI voice (Elliot) |
| Backend | FastAPI + Python 3.11 |
| Calendar | Google Calendar API (service account) |
| Deployment | Railway |
| Frontend | Vanilla HTML + JS |