from __future__ import annotations
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.outfits import generate_outfit, get_alternatives
from app.database import get_db
from app.schemas.outfit import OutfitOut
from app.schemas.product import ProductOut

router = APIRouter(prefix="/chat", tags=["chat"])

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Aria, a multilingual luxury fashion stylist at Daarvi — an exclusive curated boutique.

Your role is to ACTIVELY help customers build outfits, not just give advice. You have two tools:

1. generate_outfit — call this whenever a user mentions an occasion, style preference, or budget. Don't ask follow-up questions first — act immediately.
2. suggest_swap — call this when a user dislikes an item, mentions a specific role (jeans, top, jacket, shoes…), or asks for alternatives.

Behavior rules:
- Respond in the same language the user is writing in. Default to English if the language is unclear. NEVER infer language from product names or outfit data — only from the user's actual messages
- Be warm, brief, and action-first (call a tool, THEN explain what you did in 1-2 sentences)
- After calling a tool, describe the result naturally: "I've put together a look..." or "I've swapped that for..."
- If the user says something vague like "show me something nice", still call generate_outfit with sensible defaults
- Never describe what you are about to do — just do it (call the tool) and report back
- The current outfit context below tells you what's on screen so you can reference specific items"""

# ── GPT-4o tools (function calling) ──────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_outfit",
            "description": (
                "Generate a curated outfit from the database based on the user's preferences. "
                "Call this when the user mentions any occasion, style, or budget — even if vague."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "Style keywords extracted from the user's message (e.g. 'corporate', 'casual chic', 'dark minimalist'). Empty string if not specified.",
                    },
                    "budget": {
                        "type": "string",
                        "enum": ["<300", "300-800", "800+", ""],
                        "description": "Budget range. Parse the user's amount and pick the closest bracket. Empty if not mentioned.",
                    },
                    "occasion": {
                        "type": "string",
                        "enum": ["casual", "evening", "work", "weekend", ""],
                        "description": "Occasion type. Map 'corporate party' → 'work', 'dinner' → 'evening', etc.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_swap",
            "description": (
                "Find an alternative product for a specific role in the current outfit and apply it. "
                "Call this when the user says they don't like a specific item, mentions a garment by type "
                "(jeans, jacket, top, bag…), or asks for an alternative to something on screen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["anchor", "top", "bottom", "shoes", "bag", "accessory"],
                        "description": "The outfit role to replace. Map user's words: jeans/trousers/skirt → bottom, shirt/blouse → top, coat/jacket → anchor, etc.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for the swap (for context in the response).",
                    },
                },
                "required": ["role"],
            },
        },
    },
]

# ── Request / response schemas ────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str        # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    outfit_context: str = ""
    scope: str = "global"   # "local" | "global" — used when generating outfits


class ChatResponse(BaseModel):
    message: str
    actions: list = []      # list of action dicts the frontend should execute


# ── Main endpoint — non-streaming, uses function calling ─────────────────────

@router.post("/outfit-assistant", response_model=ChatResponse)
async def outfit_assistant(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Outfit assistant is not configured. Add OPENAI_API_KEY to the Render environment.",
        )

    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise HTTPException(status_code=503, detail="openai package not installed.")

    ai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Build messages: system + optional outfit context + conversation
    system_content = SYSTEM_PROMPT
    if body.outfit_context:
        system_content += f"\n\n[CURRENT OUTFIT ON SCREEN]\n{body.outfit_context}"

    oai_messages: list[dict] = [{"role": "system", "content": system_content}]
    for m in body.messages:
        oai_messages.append({"role": m.role, "content": m.content})

    # ── First GPT-4o call — may trigger tool calls ────────────────────────
    response = await ai.chat.completions.create(
        model="gpt-4o",
        messages=oai_messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.7,
        max_tokens=800,
    )

    msg = response.choices[0].message
    actions: list[dict] = []

    # ── Execute tool calls ────────────────────────────────────────────────
    if msg.tool_calls:
        # Append assistant message (with tool_calls) so GPT-4o can continue
        oai_messages.append(msg)

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            tool_result = "No result."

            if fn_name == "generate_outfit":
                outfit = await generate_outfit(
                    db,
                    style=args.get("style", ""),
                    budget=args.get("budget", ""),
                    occasion=args.get("occasion", ""),
                    scope=body.scope,
                )
                if outfit:
                    outfit_out = OutfitOut.from_orm_outfit(outfit)
                    actions.append({
                        "type": "DISPLAY_OUTFIT",
                        "outfit": outfit_out.model_dump(),
                    })
                    items_summary = ", ".join(
                        f"{i.role}: {i.product.name} (${i.product.price_global})"
                        for i in outfit_out.items
                    )
                    tool_result = (
                        f"Outfit generated: '{outfit_out.title}'. "
                        f"Items: {items_summary}."
                    )
                else:
                    tool_result = "No matching products found in the database for these preferences."

            elif fn_name == "suggest_swap":
                role = args.get("role", "bottom")
                products = await get_alternatives(db, role=role, scope=body.scope, limit=3)
                if products:
                    best = products[0]
                    product_out = ProductOut.from_orm_full(best)
                    brand = best.brand.name if best.brand else ""
                    price = best.price_local if body.scope == "local" else best.price_global
                    actions.append({
                        "type": "SWAP_ITEM",
                        "role": role,
                        "product": product_out.model_dump(),
                    })
                    tool_result = (
                        f"Swapped {role} to: '{best.name}' by {brand} at ${price}."
                    )
                else:
                    tool_result = f"No alternative {role} found in the current scope."

            # Feed tool result back to GPT-4o
            oai_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        # ── Second GPT-4o call — get Aria's final message ─────────────────
        final = await ai.chat.completions.create(
            model="gpt-4o",
            messages=oai_messages,
            temperature=0.7,
            max_tokens=400,
        )
        aria_message = final.choices[0].message.content or ""
    else:
        aria_message = msg.content or ""

    return ChatResponse(message=aria_message, actions=actions)
