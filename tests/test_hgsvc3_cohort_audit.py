import pytest

from scripts.audit_hgsvc3_cohort import parse_index


HEADER = (
    "#ENA_FILE_PATH\tMD5SUM\tRUN_ID\tSAMPLE_NAME\tPOPULATION\t"
    "EXPERIMENT_ID\tINSTRUMENT_PLATFORM\tANALYSIS_GROUP"
)
ROW = (
    "ftp://example.org/HG00512.final.cram\tabcd\tERR1\tHG00512\tCHS\t"
    "ERX1\tILLUMINA\thigh_cov"
)


@pytest.mark.parametrize("extra_blank", [False, True])
def test_parse_index_handles_related_index_extra_empty_field(extra_blank):
    row = ROW.replace("CHS\tERX1", "CHS\t\tERX1") if extra_blank else ROW
    matches = parse_index(f"##metadata\n{HEADER}\n{row}\n", "698")
    assert matches["HG00512"] == [
        {
            "cohort": "698",
            "url": "https://example.org/HG00512.final.cram",
            "md5": "abcd",
            "run_id": "ERR1",
            "population": "CHS",
            "analysis_group": "high_cov",
        }
    ]


def test_parse_index_rejects_unexpected_row_width():
    with pytest.raises(ValueError, match="Unexpected 698 index row width"):
        parse_index(f"{HEADER}\n{ROW}\textra\tfield\n", "698")
