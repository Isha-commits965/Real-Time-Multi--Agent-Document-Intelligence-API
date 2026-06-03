import enum

from pydantic import BaseModel, Field, field_validator


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ToneLabel(str, enum.Enum):
    FORMAL = "formal"
    INFORMAL = "informal"
    PERSUASIVE = "persuasive"
    INFORMATIONAL = "informational"


class UrgencyLabel(str, enum.Enum):
    URGENT = "urgent"
    ROUTINE = "routine"


class DocumentCategory(str, enum.Enum):
    CONTRACT = "Contract"
    LEGAL_BRIEF = "Legal Brief"
    RESEARCH_MEMO = "Research Memo"
    CORRESPONDENCE = "Correspondence"
    REPORT = "Report"
    INVOICE = "Invoice"
    OTHER = "Other"


class PersonEntity(BaseModel):
    name: str
    role: str | None = None
    mentions: int = Field(ge=0)


class OrganizationEntity(BaseModel):
    name: str
    mentions: int = Field(ge=0)


class CountedEntity(BaseModel):
    value: str
    mentions: int = Field(ge=1)


class SummarizerResult(BaseModel):
    summary: str
    key_points: list[str] = Field(min_length=3, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def validate_summary_word_count(cls, value: str) -> str:
        word_count = len(value.split())
        if word_count < 100 or word_count > 150:
            raise ValueError(
                f"summary must be 100-150 words, got {word_count}"
            )
        return value


class EntityExtractorResult(BaseModel):
    people: list[PersonEntity] = Field(default_factory=list)
    organizations: list[OrganizationEntity] = Field(default_factory=list)
    dates: list[CountedEntity] = Field(default_factory=list)
    locations: list[CountedEntity] = Field(default_factory=list)
    monetary_values: list[CountedEntity] = Field(default_factory=list)
    numeric_metrics: list[CountedEntity] = Field(default_factory=list)


class SentimentAnalyzerResult(BaseModel):
    sentiment: SentimentLabel
    tone: ToneLabel
    urgency: UrgencyLabel
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_excerpts: list[str] = Field(min_length=1, max_length=2)


class DocumentClassifierResult(BaseModel):
    category: DocumentCategory
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str

    @field_validator("rationale")
    @classmethod
    def validate_single_line_rationale(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("rationale must not be empty")
        if "\n" in cleaned:
            raise ValueError("rationale must be a single line")
        return cleaned
