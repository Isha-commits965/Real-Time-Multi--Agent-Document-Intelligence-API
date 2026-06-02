from app.schemas.agent_results import SummarizerResult
from app.services.llm_client import complete_json

SYSTEM_PROMPT = """You are a legal document summarizer.
Return JSON only with this exact shape:
{
  "summary": "100-150 word concise summary",
  "key_points": ["point 1", "point 2", "point 3"],
  "confidence": 0.0
}
Rules:
- key_points must have 3 to 5 items
- confidence is between 0.0 and 1.0
- Base the summary only on the provided document text"""


async def analyze(text: str) -> dict:
    raw = await complete_json(SYSTEM_PROMPT, f"Document text:\n\n{text}")
    return SummarizerResult.model_validate(raw).model_dump(mode="json")
