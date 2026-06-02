from app.schemas.agent_results import DocumentClassifierResult
from app.services.llm_client import complete_json

SYSTEM_PROMPT = """You are a legal document classifier.
Classify the document into exactly one category:
Contract, Legal Brief, Research Memo, Correspondence, Report, Invoice, Other

Return JSON only with this exact shape:
{
  "category": "Contract",
  "confidence": 0.0,
  "rationale": "one line explanation"
}
Rules:
- category must be one of the listed values exactly
- confidence is between 0.0 and 1.0
- Base classification only on the provided document text"""


async def analyze(text: str) -> dict:
    raw = await complete_json(SYSTEM_PROMPT, f"Document text:\n\n{text}")
    return DocumentClassifierResult.model_validate(raw).model_dump(mode="json")
