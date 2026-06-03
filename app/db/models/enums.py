import enum


class FileType(str, enum.Enum):
    PDF = "pdf"
    TXT = "txt"


class DocumentStatus(str, enum.Enum):
    READY = "ready"
    PROCESSING = "processing"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_FAILED = "partially_failed"
    FAILED = "failed"


class AgentName(str, enum.Enum):
    SUMMARIZER = "summarizer"
    ENTITY_EXTRACTOR = "entity_extractor"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    DOCUMENT_CLASSIFIER = "document_classifier"


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
