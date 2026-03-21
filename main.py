import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from calendar_service import create_event, CalendarError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Voice Scheduling Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    html = Path("static/index.html").read_text()
    return HTMLResponse(content=html)


@app.post("/webhook")
async def vapi_webhook(request: Request) -> dict:
    body = await request.json()
    logger.info("Webhook received: %s", body)

    message = body.get("message", {})
    if message.get("type") != "tool-calls":
        return {"status": "ignored"}

    tool_calls = message.get("toolCallList", [])
    results = []

    for call in tool_calls:
        call_id = call.get("id")
        function = call.get("function", {})
        name = function.get("name")
        args = function.get("arguments", {})

        if name == "create_calendar_event":
            result_text = await handle_create_event(args)
        else:
            result_text = f"Unknown tool: {name}"

        results.append({"toolCallId": call_id, "result": result_text})

    return {"results": results}


async def handle_create_event(args: dict) -> str:
    attendee_name: str = args.get("name", "Guest")
    date: str = args.get("date", "")
    time: str = args.get("time", "")
    title: str = args.get("title", "Meeting")

    if not date or not time:
        return "I'm missing the date or time. Could you provide those again?"

    try:
        event_link = create_event(
            attendee_name=attendee_name,
            date=date,
            time=time,
            title=title,
        )
        logger.info("Event created: %s", event_link)
        return (
            f"Done! I've booked '{title}' for {attendee_name} on {date} at {time}. "
            f"You can view it here: {event_link}"
        )
    except CalendarError as e:
        logger.error("Calendar error: %s", e)
        return "I wasn't able to create the event due to a calendar error. Please try again."
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return "Something went wrong on my end. Please try again in a moment."
