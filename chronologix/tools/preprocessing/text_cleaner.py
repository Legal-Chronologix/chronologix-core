import re

ONLY_PARENTHESES_LINE = r"(?m)^[ \t]*[()]+[ \t]*$"
EXTREME_VERTICAL_SPACE = r"(?:[ \t]*\n){3,}"
TRAILING_SPACES = r"[ \t]+$"
REPEATED_INLINE_SPACES = r"[ \t]{2,}"


def clean_extracted_text(text: str | None) -> str:
    """
    Clean text extracted from PDFs.

    Main goal:
    - remove obvious PDF layout artifacts
    - normalize line endings
    - remove extreme vertical spacing
    - normalize repeated spaces/tabs inside lines
    - keep paragraph/page structure readable
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(ONLY_PARENTHESES_LINE, "", text)
    text = re.sub(TRAILING_SPACES, "", text, flags=re.MULTILINE)
    text = re.sub(REPEATED_INLINE_SPACES, " ", text)
    text = re.sub(EXTREME_VERTICAL_SPACE, "\n\n", text)

    return text.strip()


def remove_pdf_footer_noise(text: str) -> str:
    """
    Remove common court PDF footer/header artifacts.
    """
    if not text:
        return ""

    # Remove CourtListener/PACER footer lines.
    text = re.sub(
        r"(?im)^USDC\s+.*?document\s+\d+.*?page\s+\d+\s+of\s+\d+\s*$",
        "",
        text,
    )

    # Remove standalone page numbers.
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)

    return text
