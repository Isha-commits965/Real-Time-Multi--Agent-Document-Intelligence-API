from pathlib import Path

from PyPDF2 import PdfReader

from app.db.models.enums import FileType


class TextExtractionError(Exception):
    """Raised when text cannot be read from an uploaded file."""


def count_words(text: str) -> int:
    return len(text.split())


def extract_text_from_file(file_path: Path, file_type: FileType) -> str:
    if file_type == FileType.PDF:
        return _extract_text_from_pdf(file_path)
    if file_type == FileType.TXT:
        return _extract_text_from_txt(file_path)
    raise TextExtractionError(f"Unsupported file type: {file_type.value}")


def _extract_text_from_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:
        raise TextExtractionError("Unable to read PDF file") from exc

    if len(reader.pages) == 0:
        raise TextExtractionError("PDF has no pages")

    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            parts.append(page_text)

    text = "\n".join(parts).strip()
    if not text:
        raise TextExtractionError("PDF contains no extractable text")
    return text


def _extract_text_from_txt(file_path: Path) -> str:
    raw = file_path.read_bytes()
    text: str | None = None
    for encoding in ("utf-8", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise TextExtractionError("Unable to decode text file")

    text = text.strip()
    if not text:
        raise TextExtractionError("Text file is empty")
    return text
