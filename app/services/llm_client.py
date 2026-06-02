import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings


class LLMError(Exception):
    pass


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
    )


async def complete_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    client = _client()
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception as exc:
        raise LLMError(str(exc)) from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("Empty response from LLM")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM returned invalid JSON") from exc
