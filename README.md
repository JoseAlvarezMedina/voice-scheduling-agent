# Voice Scheduling Agent

A real-time voice assistant that books Google Calendar events through natural conversation.
Built with VAPI, FastAPI, and the Google Calendar API. Deployed on Railway.

---

## Live demo

**Agent URL:** _[add after deployment]_

**How to test:**
1. Open the URL above
2. Click "Start call"
3. Follow the assistant's prompts — provide your name, a date, a time, and optionally a meeting title
4. Confirm the details when asked
5. Check your Google Calendar — the event will appear within seconds

---

## Calendar integration

<!-- Explain here: service account setup, how credentials are loaded (base64 env var), which calendar events are created in -->
_[add after setup]_

---

## How to run locally

### Prerequisites
- Python 3.11+
- A Google Cloud service account JSON key
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

### Run

```bash
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Open `/` for the voice widget or use `/docs` for the API docs.

---

## Design decisions

<!-- Explain: why VAPI, why service account over OAuth, why Railway, why this architecture -->
_[fill in after project is complete]_

---

## What I would add with more time

- Webhook signature validation using `VAPI_SECRET`
- Timezone detection from the user's browser
- Email confirmation to the attendee after booking
- Support for rescheduling and cancellation via voice
- Proper test suite for `calendar_service.py`

---

## Screenshots / demo

<!-- Add Loom video link or screenshots here -->
_[add after recording]_
