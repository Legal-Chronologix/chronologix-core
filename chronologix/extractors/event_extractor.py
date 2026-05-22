import re

REGEX_DATE_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)"
    r"\s+\d{1,2},\s+\d{4}"
)

REGEX_SENTENCE_WITH_DATE = (
    rf"[^.!?]*{REGEX_DATE_PATTERN}[^.!?]*[.!?]"
)

ABBREVIATIONS = {
    "Mr.": "Mr<DOT>",
    "Ms.": "Ms<DOT>",
    "Mrs.": "Mrs<DOT>",
    "Dr.": "Dr<DOT>",
    "Prof.": "Prof<DOT>",
}


def protect_abbreviations(text: str) -> str:
    """
    Temporarily replace periods in common abbreviations.

    This prevents sentence extraction from incorrectly splitting on
    abbreviations like "Mr." or "Dr.".

    >>> protect_abbreviations("Mr. Gipson filed a charge.")
    'Mr<DOT> Gipson filed a charge.'
    """
    for abbreviation, replacement in ABBREVIATIONS.items():
        text = text.replace(abbreviation, replacement)

    return text


def restore_abbreviations(text: str) -> str:
    """
    Restore protected abbreviation placeholders back to normal text.

    >>> restore_abbreviations("Mr<DOT> Gipson filed a charge.")
    'Mr. Gipson filed a charge.'
    """
    for abbreviation, replacement in ABBREVIATIONS.items():
        text = text.replace(replacement, abbreviation)

    return text


def extract_sentences_with_dates(text: str) -> list[str]:
    """
    Extract full sentences that contain a written date.

    This is the first simple event-candidate extractor:
    it does not decide whether the sentence is legally important yet.
    It only finds sentences that contain dates like "October 29, 2012".

    >>> text = "USS hired Mr. Gipson on October 29, 2012. This has no date."
    >>> extract_sentences_with_dates(text)
    ['USS hired Mr. Gipson on October 29, 2012.']

    >>> text = "Mr. Gipson joined USW on November 28, 2012. Dr. Smith testified."
    >>> extract_sentences_with_dates(text)
    ['Mr. Gipson joined USW on November 28, 2012.']
    """
    if not text:
        return []

    # Protect abbreviation periods before regex sentence matching.
    protected_text = protect_abbreviations(text)

    # Find sentences that contain a date pattern.
    matches = re.findall(REGEX_SENTENCE_WITH_DATE, protected_text)

    # Restore abbreviations and clean whitespace.
    return [
        restore_abbreviations(match).strip()
        for match in matches
        if match.strip()
    ]


if __name__ == "__main__":
    text = (
        "USS hired Mr. Gipson on October 29, 2012 to work in its Midwest Plant. "
        "Mr. Gipson became a member of USW on or about November 28, 2012. "
        "This is another sentence."
    )

    result = extract_sentences_with_dates(text)

    print("Sentences with dates:")
    for sentence in result:
        print("-", sentence)
