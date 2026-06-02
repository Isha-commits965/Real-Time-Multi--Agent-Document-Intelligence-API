import secrets


def _generate_prefixed_id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(12)}"


def generate_document_id() -> str:
    return _generate_prefixed_id("doc_")


def generate_job_id() -> str:
    return _generate_prefixed_id("job_")
