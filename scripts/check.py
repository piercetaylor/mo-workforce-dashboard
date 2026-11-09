"""Verify reconciliation, extract contents, Prep inputs and the README description."""
import re
from decimal import Decimal
from pathlib import Path

import pandas as pd
from tableauhyperapi import Connection, CreateMode, HyperProcess, Telemetry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CLEAN = DATA / "clean"
PREP = DATA / "prep_inputs"
EXTRACT = DATA / "extract"
COLUMNS = ["calendar_year", "department", "job_title", "annual_pay", "person_key", "person_annual_pay", "is_primary_row", "source_row_id"]
YEARS = range(2019, 2026)


def ok(message):
    print(f"ok  {message}")


def dollars(strings):
    return sum(map(Decimal, strings))


def check_reconciliation():
    recon = pd.read_csv(CLEAN / "reconciliation.csv").set_index("calendar_year")
    for year in YEARS:
        raw = pd.read_csv(DATA / "raw" / f"{year}.csv", dtype=str, keep_default_na=False)
        clean = pd.read_csv(CLEAN / f"pay_CY{year % 100:02d}.csv", dtype=str, keep_default_na=False)
        row = recon.loc[str(year)]
        assert list(clean.columns) == COLUMNS
        assert len(raw) == row["raw_rows"] and len(clean) == row["clean_rows"]
        raw_total, clean_total = dollars(raw.iloc[:, 4]), dollars(clean["annual_pay"])
        assert raw_total == Decimal(int(row["raw_cents"])) / 100
        assert clean_total == raw_total - Decimal(int(row["excluded_cents"])) / 100
        assert clean["source_row_id"].is_unique
    ok("raw and clean row counts and exact totals reconcile for every year")


def check_people(pay):
    primary = pay[pay["is_primary_row"] == 1]
    assert not primary.duplicated(["calendar_year", "person_key"]).any()
    assert primary["person_key"].nunique() <= pay["person_key"].nunique()
    assert (pay.groupby(["calendar_year", "person_key"])["is_primary_row"].sum() == 1).all()
    ok("each person has exactly one primary row per year")


def check_hyper(pay):
    state = pd.read_csv(CLEAN / "metrics_statewide.csv").set_index("calendar_year")
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={"log_config": ""}) as hyper:
        with Connection(hyper.endpoint, EXTRACT / "mo_workforce.hyper", CreateMode.NONE) as conn:
            assert conn.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."pay"') == len(pay)
            xwalk = conn.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."department_xwalk"')
            assert xwalk == len(pd.read_csv(DATA / "ref" / "department_xwalk.csv"))
            rows = conn.execute_list_query('SELECT calendar_year, COUNT(DISTINCT person_key), MEDIAN(person_annual_pay), AVG(person_annual_pay) '
                                           'FROM "Extract"."pay" WHERE is_primary_row = 1 GROUP BY calendar_year')
    for year, count, median, mean in rows:
        assert count == state.loc[year, "headcount"], year
        assert abs(float(median) - state.loc[year, "median_pay"]) < 0.01, year
        assert abs(float(mean) - state.loc[year, "mean_pay"]) < 0.01, year
    ok("Hyper table counts match the CSVs; Hyper SQL statewide headcount, median and mean match pandas")


def check_extract_csv(pay):
    assert list(pay.columns) == COLUMNS
    ok(f"mo_workforce.csv has {len(pay):,} rows and no employee name column")


def check_prep():
    a = pd.read_csv(PREP / "prep_input_a_cy2024.csv", dtype=str)
    b = pd.read_csv(PREP / "prep_input_b_cy2025.csv", dtype=str)
    clean_a = pd.read_csv(CLEAN / "pay_CY24.csv", dtype=str)
    clean_b = pd.read_csv(CLEAN / "pay_CY25.csv", dtype=str)
    for messy, clean, pay_col in ((a, clean_a, "GROSS_PAY"), (b, clean_b, "Pay Amount")):
        unique = messy.drop_duplicates()
        assert len(unique) == len(clean)
        assert abs((len(messy) - len(unique)) / len(clean) - 0.02) < 0.001
        assert dollars(unique[pay_col].str.replace(r"[$,]", "", regex=True)) == dollars(clean["annual_pay"])
    assert not any("name" in c.lower() for c in list(a.columns) + list(b.columns))
    ok("Prep inputs reduce to the clean rows and totals after removing exact duplicates")


def check_description():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    text = re.search(r"## Plain-language description\n\n(.+?)\n\n", readme, re.S).group(1)
    assert len(text.split()) == 100, len(text.split())
    ok("README plain-language description is 100 words")


def main():
    check_reconciliation()
    pay = pd.read_csv(EXTRACT / "mo_workforce.csv")
    check_people(pay)
    check_extract_csv(pay)
    check_hyper(pay)
    check_prep()
    check_description()
    print("all checks passed")


if __name__ == "__main__":
    main()
