from chronologix.preprocessing.sentence_splitter import (
    extract_sentences_by_dates,
    protect_abbreviations,
    restore_abbreviations,
)


def test_protect_abbreviations_replaces_known_abbreviations():
    text = "Mr. Gipson met Dr. Smith."

    result = protect_abbreviations(text)

    assert result == "Mr<DOT> Gipson met Dr<DOT> Smith."


def test_restore_abbreviations_restores_known_abbreviations():
    text = "Mr<DOT> Gipson met Dr<DOT> Smith."

    result = restore_abbreviations(text)

    assert result == "Mr. Gipson met Dr. Smith."


def test_extract_sentences_by_dates_returns_sentence_with_date():
    text = (
        "USS hired Mr. Gipson on October 29, 2012 to work in its Midwest Plant. "
        "This sentence has no date."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "USS hired Mr. Gipson on October 29, 2012 to work in its Midwest Plant."
    ]


def test_extract_sentences_by_dates_handles_multiple_date_sentences():
    text = (
        "USS hired Mr. Gipson on October 29, 2012 to work in its Midwest Plant. "
        "Mr. Gipson became a member of USW on or about November 28, 2012. "
        "This is another sentence."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "USS hired Mr. Gipson on October 29, 2012 to work in its Midwest Plant.",
        "Mr. Gipson became a member of USW on or about November 28, 2012.",
    ]


def test_extract_sentences_by_dates_does_not_split_after_mr():
    text = (
        "Mr. Gipson filed a charge on June 6, 2019. "
        "This sentence has no date."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "Mr. Gipson filed a charge on June 6, 2019."
    ]


def test_extract_sentences_by_dates_returns_empty_list_for_empty_text():
    assert extract_sentences_by_dates("") == []
