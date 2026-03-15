import html
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException

from app.config import settings
from app.models import SubmitRequest, SubmitResponse
from app.db import create_submission, init_db, delete_submission_by_id

def format_alcohol(data: dict) -> str:
    labels = {
        "whiteWine": "Белое вино",
        "redWine": "Красное вино",
        "champagne": "Шампанское",
        "beer": "Пиво",
        "whiskey": "Виски",
        "tinctures": "Настойки",
    }

    selected = [label for key, label in labels.items() if data.get(key)]
    return ", ".join(selected) if selected else "Ничего"


async def send_telegram_message(text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            },
        )
        response.raise_for_status()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Event Form Backend", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/submit", response_model=SubmitResponse)
async def submit_form(
    payload: SubmitRequest,
    x_api_secret: str | None = Header(default=None),
) -> SubmitResponse:
    if x_api_secret != settings.API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API secret")

    submission_id = create_submission(
        name=payload.name.strip(),
        allergy=(payload.allergy or "").strip(),
        alcohol=payload.alcohol.model_dump(),
    )

    text = (
        "🆕 <b>Новая заявка</b>\n\n"
        f"<b>ID:</b> {submission_id}\n"
        f"<b>Имя:</b> {html.escape(payload.name)}\n"
        f"<b>Аллергия:</b> {html.escape(payload.allergy or '—')}\n"
        f"<b>Алкоголь:</b> {html.escape(format_alcohol(payload.alcohol.model_dump()))}"
    )

    await send_telegram_message(text)

    return SubmitResponse(
        ok=True,
        id=submission_id,
        message="Submission saved successfully",
    )

@app.delete("/submissions/{submission_id}")
async def delete_submission(
    submission_id: int,
    x_api_secret: str | None = Header(default=None),
) -> dict:
    if x_api_secret != settings.API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API secret")

    deleted = delete_submission_by_id(submission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {
        "ok": True,
        "id": submission_id,
        "message": "Submission deleted successfully",
    }