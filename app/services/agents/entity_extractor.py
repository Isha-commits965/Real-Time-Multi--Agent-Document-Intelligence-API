from app.schemas.agent_results import EntityExtractorResult
from app.services.llm_client import complete_json

SYSTEM_PROMPT = """You are a legal document entity extractor.
Return JSON only with this exact shape:
{
  "people": [{"name": "string", "role": "string or null", "mentions": 0}],
  "organizations": [{"name": "string", "mentions": 0}],
  "dates": ["string"],
  "locations": ["string"],
  "monetary_values": ["string"]
}
Rules:
- Include mention counts for people and organizations
- Use empty arrays when nothing is found
- Base extraction only on the provided document text"""


async def analyze(text: str) -> dict:
    raw = await complete_json(SYSTEM_PROMPT, f"Document text:\n\n{text}")
    return EntityExtractorResult.model_validate(raw).model_dump(mode="json")
