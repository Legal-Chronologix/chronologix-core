from textwrap import dedent

from chronologix.steps.preprocessing.text_cleaner import clean_extracted_text


def test_clean_extracted_text_returns_empty_string_for_empty_input():
    assert clean_extracted_text("") == ""
    assert clean_extracted_text(None) == ""


def test_clean_extracted_text_normalizes_line_endings():
    text = "Line one\r\nLine two\rLine three"

    result = clean_extracted_text(text)

    assert result == "Line one\nLine two\nLine three"


def test_clean_extracted_text_removes_trailing_spaces():
    text = "Line one   \nLine two\t\t\nLine three"

    result = clean_extracted_text(text)

    assert result == "Line one\nLine two\nLine three"


def test_clean_extracted_text_collapses_extreme_vertical_spacing():
    text = "Paragraph one\n\n\n\n\nParagraph two"

    result = clean_extracted_text(text)

    assert result == "Paragraph one\n\nParagraph two"


def test_clean_extracted_text_collapses_blank_lines_with_spaces():
    text = "Paragraph one\n   \n\t\n   \nParagraph two"

    result = clean_extracted_text(text)

    assert result == "Paragraph one\n\nParagraph two"


def test_clean_extracted_text_strips_outer_whitespace():
    text = "   \n\nParagraph one\n\n   "

    result = clean_extracted_text(text)

    assert result == "Paragraph one"


def test_clean_extracted_text_removes_parentheses_only_lines():
    text = dedent(
        """
        Saladin J. Gipson,
        )
        )
        Plaintiff,
        )
        )
        Case No. 21-cv-00071 JTM-JEM
        v.
        )
        )
        United States Steel
        Corporation and United Steelworkers
        Local 6103,
        )
        """
    )

    result = clean_extracted_text(text)

    assert ")" not in result.splitlines()
    assert result == (
        "Saladin J. Gipson,\n\n"
        "Plaintiff,\n\n"
        "Case No. 21-cv-00071 JTM-JEM\n"
        "v.\n\n"
        "United States Steel\n"
        "Corporation and United Steelworkers\n"
        "Local 6103,"
    )
