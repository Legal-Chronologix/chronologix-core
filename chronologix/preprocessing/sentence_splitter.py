"""
sentence_splitter.py

Text preprocessing helpers for extracting date-containing sentences.

This module does NOT build event objects.
It only:
- protects abbreviations from bad sentence splitting
- removes inline legal citation noise for extraction
- splits text into sentence-like chunks
- returns sentences that contain written dates
"""

import re

REGEX_DATE_PATTERN = (
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?"
    r"|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?"
    r"|Dec(?:ember)?)"
    r"\s+\d{1,2},\s+\d{4}\b"
)

SENTENCE_SPLIT_PATTERN = r"(?<=[.!?])\s+"

ABBREVIATIONS = {
    "Mr.": "Mr<DOT>",
    "Ms.": "Ms<DOT>",
    "Mrs.": "Mrs<DOT>",
    "Dr.": "Dr<DOT>",
    "Prof.": "Prof<DOT>",
    "No.": "No<DOT>",
    "Id.": "Id<DOT>",
    "Inc.": "Inc<DOT>",
    "Corp.": "Corp<DOT>",
    "Co.": "Co<DOT>",
    "U.S.C.": "U<DOT>S<DOT>C<DOT>",
    "U.S.": "U<DOT>S<DOT>",
    "Fed.": "Fed<DOT>",
    "Civ.": "Civ<DOT>",
}


def normalize_whitespace_for_extraction(text: str) -> str:
    """
    Collapse PDF line breaks and repeated whitespace for extraction only.

    This should not overwrite source text. It only makes sentence splitting
    easier.

    >>> normalize_whitespace_for_extraction("On January 22, 2020\\nMr. Gipson")
    'On January 22, 2020 Mr. Gipson'
    """
    if not text:
        return ""

    return " ".join(text.split())


def remove_inline_citation_noise(text: str) -> str:
    """
    Remove common legal/docket citation parentheticals for extraction.

    Examples removed:
    - (DE # 47.)
    - (DE ## 98, 104.)
    - (DE # 115 at 8.)
    - (Id.)
    - (Pl. Dep. 74.)

    >>> remove_inline_citation_noise("The court adopted it. (DE # 47.)")
    'The court adopted it. '
    >>> remove_inline_citation_noise("Plaintiff testified. (Pl. Dep. 74.)")
    'Plaintiff testified. '
    """
    if not text:
        return ""

    citation_patterns = [
        r"\(DE\s+##?\s*[^)]*\)",
        r"\(Dkt\.\s*[^)]*\)",
        r"\(ECF\s+No\.\s*[^)]*\)",
        r"\(Id\.\)",
        r"\(id\.\)",
        r"\(Pl\.\s+Dep\.[^)]*\)",
        r"\(Pl\.\s+Aff\.[^)]*\)",
        r"\([A-Za-z]+\.\s+Dep\.[^)]*\)",
        r"\([A-Za-z]+\.\s+Aff\.[^)]*\)",
    ]

    for pattern in citation_patterns:
        text = re.sub(pattern, "", text)

    return text


def protect_abbreviations(text: str) -> str:
    """
    Temporarily replace periods in common abbreviations.

    This prevents sentence splitting from breaking after things like:
    - Mr.
    - No.
    - Id.
    - U.S.

    It also protects middle initials like "James T. Moody".

    >>> protect_abbreviations("Mr. Gipson filed Charge No. 123.")
    'Mr<DOT> Gipson filed Charge No<DOT> 123.'
    >>> protect_abbreviations("Judge James T. Moody entered an order.")
    'Judge James T<DOT> Moody entered an order.'
    """
    if not text:
        return ""

    for abbreviation, replacement in ABBREVIATIONS.items():
        text = text.replace(abbreviation, replacement)

    # Protect middle initials like "James T. Moody" or "Saladin J. Gipson".
    text = re.sub(
        r"\b([A-Z])\.(?=\s+[A-Z][a-z])",
        r"\1<DOT>",
        text,
    )

    return text


def restore_abbreviations(text: str) -> str:
    """
    Restore abbreviation placeholders back to normal text.

    >>> restore_abbreviations("Mr<DOT> Gipson met James T<DOT> Moody.")
    'Mr. Gipson met James T. Moody.'
    """
    if not text:
        return ""

    for abbreviation, replacement in ABBREVIATIONS.items():
        text = text.replace(replacement, abbreviation)

    return text.replace("<DOT>", ".")


def clean_sentence_candidate(sentence: str) -> str:
    """
    Remove common artifacts from the start of a sentence candidate.

    Examples:
    - ") On January 22, 2020..." -> "On January 22, 2020..."
    - "3 On March 22, 2022..." -> "On March 22, 2022..."

    >>> clean_sentence_candidate(") On January 22, 2020 plaintiff was suspended.")
    'On January 22, 2020 plaintiff was suspended.'
    >>> clean_sentence_candidate("3 On March 22, 2022 plaintiff missed deposition.")
    'On March 22, 2022 plaintiff missed deposition.'
    """
    if not sentence:
        return ""

    sentence = sentence.strip()

    # Remove page number / footnote artifact at the beginning.
    sentence = re.sub(r"^\d+\s+", "", sentence)

    # Remove leftover closing parenthesis artifacts from citations like "(Id.)".
    sentence = re.sub(r"^\)+\s*", "", sentence)

    # Remove leading citation remnants.
    sentence = re.sub(r"^\(?Id\.\)?\s*", "", sentence)

    return sentence.strip()


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentence-like chunks.

    This is regex-based and intentionally simple for MVP. It protects common
    legal/name abbreviations before splitting, then restores them after.

    >>> split_into_sentences("Mr. Gipson filed a charge. This has no date.")
    ['Mr. Gipson filed a charge.', 'This has no date.']
    >>> split_into_sentences("Judge James T. Moody entered an order. Done.")
    ['Judge James T. Moody entered an order.', 'Done.']
    """
    if not text:
        return []

    text = normalize_whitespace_for_extraction(text)
    text = remove_inline_citation_noise(text)
    protected_text = protect_abbreviations(text)

    raw_sentences = re.split(SENTENCE_SPLIT_PATTERN, protected_text)

    sentences = []
    for raw_sentence in raw_sentences:
        sentence = restore_abbreviations(raw_sentence)
        sentence = clean_sentence_candidate(sentence)

        if sentence:
            sentences.append(sentence)

    return sentences


def extract_sentences_by_dates(text: str) -> list[str]:
    """
    Return sentences containing written dates like "January 22, 2020".

    This does not create events yet. It only finds date-containing sentences.

    >>> text = "USS hired Mr. Gipson on October 29, 2012. This has no date."
    >>> extract_sentences_by_dates(text)
    ['USS hired Mr. Gipson on October 29, 2012.']

    >>> text = "(Id.) USW filed a grievance on January 23, 2020."
    >>> extract_sentences_by_dates(text)
    ['USW filed a grievance on January 23, 2020.']
    """
    sentences = split_into_sentences(text)

    return [
        sentence
        for sentence in sentences
        if re.search(REGEX_DATE_PATTERN, sentence, flags=re.IGNORECASE)
    ]


# if __name__ == "__main__":
#     sample = (
#         "(Id.) USW Local 6103 filed a grievance regarding the suspension "
#         "on plaintiff’s behalf, which resulted in a hearing on January 23, 2020. "
#         "On May 3, 2022, District Court Judge James T. Moody entered an Order. "
#         "This sentence has no date."
#     )

#     for sentence in extract_sentences_by_dates(sample):
#         print("-", sentence)