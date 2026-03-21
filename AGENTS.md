# AGENTS.md — Voice Scheduling Agent
## Read this before touching any file.

This document is the ground truth for this project. Every decision made here was deliberate. Do not deviate from the architecture, stack, or constraints described below without explicit instruction.

---

## What this project is

A real-time voice assistant that:
1. Initiates a conversation with the user
2. Collects their name, preferred date & time, and optional meeting title
3. Confirms the details before acting
4. Creates a real Google Calendar event
5. Is deployed and accessible via a public URL

---

## Stack decisions (final, not up for debate)

| Layer | Choice | Reason |
|---|---|---|
| Voice platform | VAPI | Handles STT + LLM + TTS pipeline, provides hosted agent link, has webhook tool-calling |
| LLM | GPT-4o (via VAPI) | Best instruction-following for conversational flows |
| Backend | FastAPI (Python) | Async, fast, clean OpenAPI docs auto-generated, Railway-compatible |
| Calendar | Google Calendar API (service account) | No OAuth redirect flow needed, cleaner for a demo |
| Deployment | Railway | Stays warm on free tier — critical for VAPI webhooks. NOT Hugging Face Spaces (goes to sleep, cold starts break voice agent mid-conversation) |
| Frontend | Single HTML file with VAPI web SDK embed | Shows frontend awareness without wasting hours on React |

---

## Architecture overview

```
Browser (VAPI embed)
        |
        | WebRTC voice stream
        v
   VAPI Platform
   ┌─────────────────────────────────────┐
   │  STT (Deepgram) → LLM → TTS (EL)  │
   └─────────────────────────────────────┘
        |
        | HTTP POST — tool call webhook
        v
   FastAPI backend (Railway)
   ┌──────────────────┐   ┌──────────────────┐
   │ Webhook handler  │ → │ Calendar client  │
   │ POST /webhook    │   │ Service account  │
   └──────────────────┘   └──────────────────┘
        |
        | Google Calendar REST API
        v
   Google Calendar
```

---

## Conversation flow

```
Session starts
      ↓
Info gathering — name, date/time, title (optional)
      ↓
Confirmation — bot reads back all details, user confirms
      ↓ (retry loop if user wants changes)
Tool call fires — create_calendar_event()
      ↓
FastAPI webhook → Google Calendar API
      ↓
Success message — "Your event is booked. Check your calendar."
```

---

## File structure

```
voice-scheduling-agent/
├── main.py                  # FastAPI app — /webhook and /health routes only
├── calendar_service.py      # Google Calendar API client — create_event() only
├── requirements.txt
├── Procfile                 # Railway start command
├── .env                     # Never committed
├── .env.example             # Always committed — shows required vars without values
├── static/
│   └── index.html           # VAPI web widget embed page
├── AGENTS.md                # This file
└── README.md                # Submission README — written last
```

---

## What decides pass or fail

### Automatic disqualifiers (do not let these happen)
- Missing any of the 5 core requirements listed above
- Deployed URL returns an error or is unreachable
- Calendar event is not actually created in a real calendar
- Secrets committed to the repo (`.env`, `*.json` service account key)
- Code cannot be run from the README instructions alone

### What hiring managers evaluate (in order of weight)
1. **Functionality** — does it work end to end, live, right now
2. **Code quality** — readable, modular, no dead code, meaningful variable names
3. **README quality** — treated as seriously as the code itself
4. **Git history** — meaningful commit messages, not one giant commit
5. **Design decisions** — can you explain every choice you made

---

## Code quality rules — apply to every file

- Use Python type hints on every function signature
- Every function has a single responsibility — no god functions
- Environment variables are never hardcoded — always loaded from `.env` via `python-dotenv`
- Errors are handled gracefully — no bare `except:` blocks
- No `print()` statements in production code — use Python `logging`
- Keep functions short — if a function is more than 30 lines, split it
- FastAPI routes contain no business logic — they call service functions
- Use `async def` on all FastAPI route handlers

---

## Environment variables required

Document these in `.env.example` with empty values:

```
GOOGLE_CREDENTIALS_B64=        # Base64-encoded service account JSON key
GOOGLE_CALENDAR_ID=            # Calendar ID to create events in
VAPI_SECRET=                   # Webhook secret for request validation (optional but good practice)
```

---

## VAPI tool call contract

VAPI will POST to `/webhook` when the LLM calls `create_calendar_event`. The payload shape is:

```json
{
  "message": {
    "type": "tool-calls",
    "toolCallList": [
      {
        "id": "call_abc123",
        "function": {
          "name": "create_calendar_event",
          "arguments": {
            "name": "Jose Alvarez",
            "date": "2026-03-25",
            "time": "14:00",
            "title": "Project sync"
          }
        }
      }
    ]
  }
}
```

The `/webhook` response must return:

```json
{
  "results": [
    {
      "toolCallId": "call_abc123",
      "result": "Event created successfully for Jose Alvarez on March 25 at 2:00 PM."
    }
  ]
}
```

VAPI reads the `result` string aloud to the user. Write it like a human would say it.

---

## What NOT to build (waste of time for this deadline)

- Unit tests — no complex logic to test and they weren't asked for
- Database — VAPI manages conversation state, Google Calendar stores the event
- User authentication — not needed for a demo
- React frontend — a plain HTML page is enough
- Docker — Railway handles it natively
- Retry logic / queuing — out of scope
- Multi-timezone support — keep it simple, use the calendar's default timezone
- Fancy error recovery in the voice flow — one clean path is enough

---

## README must include (written last, after everything works)

- [ ] Deployed URL with exact instructions on how to test
- [ ] How the calendar integration works (service account explanation)
- [ ] How to run locally (`.env` setup, `uvicorn` command)
- [ ] Screenshot or Loom video of a real event being created
- [ ] Design decisions section — why VAPI, why service account, why Railway
- [ ] "What I would add with more time" section — shows product thinking

---

## Commit message format

```
type: short description

Types: scaffold, feat, fix, config, docs, deploy
Examples:
  scaffold: add project structure
  feat: add VAPI webhook handler
  feat: integrate Google Calendar API
  config: add Railway deployment config
  fix: handle missing optional meeting title
  docs: write README
```

---

## Definition of done

- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /webhook` correctly parses VAPI tool call and creates a real calendar event
- [ ] Calendar event appears in Google Calendar within 5 seconds of confirmation
- [ ] VAPI agent speaks a success confirmation after event is created
- [ ] Deployed Railway URL is live and reachable
- [ ] VAPI agent link or embed page is publicly accessible
- [ ] `.env` is not in the repo — `.env.example` is
- [ ] No `*.json` files in the repo
- [ ] README covers all submission requirements
- [ ] Loom video recorded showing full end-to-end flow