from app.schemas.agent_results import EntityExtractorResult
from app.services.llm_client import complete_json

SYSTEM_PROMPT = """You are a legal document entity extractor.
Return JSON only with this exact shape:
{
  "people": [{"name": "string", "role": "string or null", "mentions": 1}],
  "organizations": [{"name": "string", "mentions": 1}],
  "dates": [{"value": "string", "mentions": 1}],
  "locations": [{"value": "string", "mentions": 1}],
  "monetary_values": [{"value": "string", "mentions": 1}],
  "numeric_metrics": [{"value": "string", "mentions": 1}]
}
Rules:
- people: names and roles when mentioned
- organizations: companies, institutions, government bodies
- dates: absolute dates (e.g. "January 15, 2024") and relative dates (e.g. "within 30 days")
- locations: cities, countries, addresses
- monetary_values: currency amounts (e.g. "$50,000", "EUR 1.2M")
- numeric_metrics: other key numbers (percentages, quantities, durations, section references)
- Every entity MUST include a mention count (minimum 1 if listed)
- Use empty arrays when nothing is found
- Base extraction only on the provided document text"""


async def analyze(text: str) -> dict:
    raw = await complete_json(SYSTEM_PROMPT, f"Document text:\n\n{text}")
    return EntityExtractorResult.model_validate(raw).model_dump(mode="json")
