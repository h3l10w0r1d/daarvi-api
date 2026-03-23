from __future__ import annotations
import json
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aria, a multilingual luxury fashion stylist at Daarvi — an exclusive curated boutique for discerning customers. Your purpose is to help customers choose and build the perfect outfit from our curated collections.

Key guidelines:
- Detect the language the customer writes in and always respond in that same language
- Be warm, confident, and elegantly concise — never verbose
- Reference specific items from the outfit context when giving advice
- When asked for recommendations, suggest which items to keep, swap, or add
- Explain briefly why something works for the customer's occasion, style preference, or budget
- If the customer is unsure, ask one focused question to understand their needs
- Keep responses to 2–4 sentences unless more detail is genuinely needed
- Never discuss topics unrelated to fashion, style, and the Daarvi collection
- You may reference international style cities, designers, and occasions naturally"""


# ── Request / response schemas ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str         # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    outfit_context: str = ""   # stringified outfit snapshot from the frontend


# ── Streaming endpoint ────────────────────────────────────────────────────────

@router.post("/outfit-assistant")
async def outfit_assistant(body: ChatRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Outfit assistant is not configured. Add OPENAI_API_KEY to the environment.",
        )

    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise HTTPException(status_code=503, detail="openai package not installed.")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Build message list — system prompt + optional outfit context + conversation
    system_content = SYSTEM_PROMPT
    if body.outfit_context:
        system_content += f"\n\n[CURRENT OUTFIT CONTEXT]\n{body.outfit_context}"

    openai_messages = [{"role": "system", "content": system_content}]
    for m in body.messages:
        openai_messages.append({"role": m.role, "content": m.content})

    async def generate():
        try:
            stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages,
                stream=True,
                max_tokens=600,
                temperature=0.75,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"data: {json.dumps({'content': delta})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering on Render
        },
    )
