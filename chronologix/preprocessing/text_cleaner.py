import re

ONLY_PARENTHESES_LINE = r"(?m)^[ \t]*[()]+[ \t]*$"
EXTREME_VERTICAL_SPACE = r"(?:[ \t]*\n){3,}"
TRAILING_SPACES = r"[ \t]+$"

def clean_extracted_text(text: str) -> str:
    """
    Clean text extracted from PDFs.

    Main goal:
    - remove extreme vertical spacing
    - normalize repeated spaces/tabs
    - keep paragraph breaks readable
    """
    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove lines that only contain court-caption parentheses.
    text = re.sub(ONLY_PARENTHESES_LINE, "", text)


    # Remove trailing spaces on each line.
    text = re.sub(TRAILING_SPACES, "", text, flags=re.MULTILINE)

    # Collapse extreme vertical spacing:
    # 3+ newline groups, even if spaces/tabs are between them, become 2 newlines.
    text = re.sub(EXTREME_VERTICAL_SPACE, "\n\n", text)

    return text.strip()
