import enum

from pydantic import BaseModel, Field


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


class SummarizerResult(BaseModel):
    summary: str
    key_points: list[str] = Field(min_length=3, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)


class EntityExtractorResult(BaseModel):
    people: list[PersonEntity] = Field(default_factory=list)
    organizations: list[OrganizationEntity] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    monetary_values: list[str] = Field(default_factory=list)


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
