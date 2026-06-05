from chronologix.tools.preprocessing.sentence_splitter import (
    clean_sentence_candidate,
    extract_sentences_by_dates,
    normalize_whitespace_for_extraction,
    protect_abbreviations,
    remove_inline_citation_noise,
    restore_abbreviations,
    split_into_sentences,
)


def test_normalize_whitespace_for_extraction_collapses_line_breaks():
    text = "On January 22, 2020\nMr. Gipson was sent home."

    result = normalize_whitespace_for_extraction(text)

    assert result == "On January 22, 2020 Mr. Gipson was sent home."


def test_remove_inline_citation_noise_removes_de_citation():
    text = "The court adopted the recommendation. (DE # 47.)"

    result = remove_inline_citation_noise(text)

    assert result == "The court adopted the recommendation. "


def test_remove_inline_citation_noise_removes_de_double_hash_citation():
    text = "The motions are granted. (DE ## 98, 104.)"

    result = remove_inline_citation_noise(text)

    assert result == "The motions are granted. "


def test_remove_inline_citation_noise_removes_id_citation():
    text = "USS converted the suspension to termination. (Id.)"

    result = remove_inline_citation_noise(text)

    assert result == "USS converted the suspension to termination. "


def test_remove_inline_citation_noise_removes_deposition_citation():
    text = "Plaintiff testified about the incident. (Pl. Dep. 74.)"

    result = remove_inline_citation_noise(text)

    assert result == "Plaintiff testified about the incident. "


def test_protect_abbreviations_handles_mr_dr_and_charge_no():
    text = "Mr. Gipson met Dr. Smith about Charge No. 24E-2019-00136."

    result = protect_abbreviations(text)

    assert (
        result
        == "Mr<DOT> Gipson met Dr<DOT> Smith about Charge No<DOT> 24E-2019-00136."
    )


def test_protect_abbreviations_handles_middle_initial():
    text = "District Court Judge James T. Moody entered an Order."

    result = protect_abbreviations(text)

    assert result == "District Court Judge James T<DOT> Moody entered an Order."


def test_restore_abbreviations_restores_placeholders():
    text = "Mr<DOT> Gipson met James T<DOT> Moody."

    result = restore_abbreviations(text)

    assert result == "Mr. Gipson met James T. Moody."


def test_clean_sentence_candidate_removes_leading_parenthesis_artifact():
    text = ") On January 22, 2020 plaintiff was suspended."

    result = clean_sentence_candidate(text)

    assert result == "On January 22, 2020 plaintiff was suspended."


def test_clean_sentence_candidate_removes_leading_page_number_artifact():
    text = "3 On March 22, 2022 plaintiff missed deposition."

    result = clean_sentence_candidate(text)

    assert result == "On March 22, 2022 plaintiff missed deposition."


def test_split_into_sentences_does_not_split_after_mr():
    text = "Mr. Gipson filed a charge. This has no date."

    result = split_into_sentences(text)

    assert result == [
        "Mr. Gipson filed a charge.",
        "This has no date.",
    ]


def test_split_into_sentences_does_not_split_after_middle_initial():
    text = "Judge James T. Moody entered an order. Done."

    result = split_into_sentences(text)

    assert result == [
        "Judge James T. Moody entered an order.",
        "Done.",
    ]


def test_extract_sentences_by_dates_returns_only_date_sentences():
    text = (
        "USS hired Mr. Gipson on October 29, 2012. "
        "This sentence has no date."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "USS hired Mr. Gipson on October 29, 2012.",
    ]


def test_extract_sentences_by_dates_handles_multiple_date_sentences():
    text = (
        "USS hired Mr. Gipson on October 29, 2012. "
        "Mr. Gipson became a member of USW on or about November 28, 2012. "
        "This is another sentence."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "USS hired Mr. Gipson on October 29, 2012.",
        "Mr. Gipson became a member of USW on or about November 28, 2012.",
    ]


def test_extract_sentences_by_dates_removes_leading_id_parenthesis_artifact():
    text = (
        "(Id.) USW Local 6103 filed a grievance regarding the suspension "
        "on plaintiff’s behalf, which resulted in a hearing on January 23, 2020."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "USW Local 6103 filed a grievance regarding the suspension "
        "on plaintiff’s behalf, which resulted in a hearing on January 23, 2020.",
    ]


def test_extract_sentences_by_dates_does_not_split_james_t_moody():
    text = (
        "On May 3, 2022, District Court Judge James T. Moody entered an Order. "
        "This sentence has no date."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "On May 3, 2022, District Court Judge James T. Moody entered an Order.",
    ]


def test_extract_sentences_by_dates_does_not_split_charge_no():
    text = (
        "On June 6, 2019, Mr. Gipson filed a charge of discrimination "
        "with the EEOC (Charge No. 24E-2019-00136)."
    )

    result = extract_sentences_by_dates(text)

    assert result == [
        "On June 6, 2019, Mr. Gipson filed a charge of discrimination "
        "with the EEOC (Charge No. 24E-2019-00136).",
    ]



def test_remove_inline_citation_noise_removes_id_at_citation():
    text = "USS converted the suspension to termination. (Id. at 10.)"

    result = remove_inline_citation_noise(text)

    assert result == "USS converted the suspension to termination. "

def test_extract_sentences_by_dates_returns_empty_list_for_empty_text():
    assert extract_sentences_by_dates("") == []
