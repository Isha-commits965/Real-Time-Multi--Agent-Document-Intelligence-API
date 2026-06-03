from app.schemas.agent_results import SentimentAnalyzerResult
from app.services.llm_client import complete_json

SYSTEM_PROMPT = """You are a legal document sentiment and tone analyzer.
Return JSON only with this exact shape:
{
  "sentiment": "positive|negative|neutral|mixed",
  "tone": "formal|informal|persuasive|informational",
  "urgency": "urgent|routine",
  "confidence": 0.0,
  "supporting_excerpts": ["excerpt 1", "excerpt 2"]
}
Rules:
- supporting_excerpts must have 1 to 2 brief quotes from the document
- confidence is between 0.0 and 1.0
- Base analysis only on the provided document text"""


async def analyze(text: str) -> dict:
    raw = await complete_json(SYSTEM_PROMPT, f"Document text:\n\n{text}")
    return SentimentAnalyzerResult.model_validate(raw).model_dump(mode="json")
