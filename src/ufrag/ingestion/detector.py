from pathlib import Path

SUPPORTED_TYPES = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".pdf": "pdf",
}


def detect_file_type(path: Path) -> str:
    file_type = SUPPORTED_TYPES.get(path.suffix.lower())
    if file_type is None:
        raise ValueError(f"unsupported file type: {path.suffix!r}")
    return file_type
