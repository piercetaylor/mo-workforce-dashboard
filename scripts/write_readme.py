"""Write README.md from the pipeline outputs."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"


def money(cents):
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) // 100:,}.{abs(cents) % 100:02d}"


def usd(x):
    return f"{x:,.2f}"


def pct(x):
    return f"{100 * x:.1f}%"


def main():
    s = json.loads((CLEAN / "metrics_summary.json").read_text(encoding="utf-8"))
    recon = pd.read_csv(CLEAN / "reconciliation.csv").set_index("calendar_year")
    total = recon.loc["TOTAL"]
    state = pd.read_csv(CLEAN / "metrics_statewide.csv").set_index("calendar_year")
    manifest = pd.read_csv(ROOT / "data" / "manifest.csv")
    xwalk = pd.read_csv(ROOT / "data" / "ref" / "department_xwalk.csv")
    variants = pd.read_csv(CLEAN / "title_variants.csv")
    retrieved = manifest["retrieved"].iloc[0]
    first, last = s["first"], s["latest"]
    v = s["versions"]
    used = manifest[manifest["calendar_year"].between(first, last)]
    table = "\n".join(f"| {y} | {int(r.headcount):,} | {usd(r.median_pay)} | {usd(r.mean_pay)} |" for y, r in state.iterrows())
    recon_rows = "\n".join(f"| {y} | {int(r.raw_rows):,} | {int(r.excluded_rows):,} | {int(r.clean_rows):,} | {money(int(r.raw_cents))} | {money(int(r.excluded_cents))} | {money(int(r.clean_cents))} |"
                           for y, r in recon.iterrows())
    (ROOT / "README.md").write_text(f"""# Missouri state workforce pay: data preparation for Tableau

This repository prepares State of Missouri employee pay records for a Tableau Public dashboard and a Tableau Prep Builder demonstration flow. It uses the State Employee Pay files that the Office of Administration publishes on data.mo.gov (Office of Administration, {retrieved[:4]}). The dashboard reports headcount and pay by department and job title for calendar years {first} to {last}. Tableau work is done by hand from `docs/TABLEAU_BUILD.md`.

`scripts/write_readme.py` writes this file from pipeline outputs. The pipeline ran on Python {v["python"]}, pandas {v["pandas"]} and tableauhyperapi {v["tableauhyperapi"]}.

## Plain-language description

This dashboard shows how many people the State of Missouri paid each calendar year, how much the typical person received, and how that differs across departments and job titles. Choose a year to update the charts, then select a department to see only its job titles. Pay means all money a person received during the year, so people who worked part of a year lower the figures, and these amounts are not salary schedules. Groups with fewer than five people are hidden. The figures come from public pay files published by the State's Office of Administration, modified for this use.

## Data source and its limits

The selected source holds one dataset per calendar year from {manifest["calendar_year"].min()} to {manifest["calendar_year"].max()}, and `data/SOURCES.md` records each dataset, the other candidates reviewed and the retrieval date of {retrieved}. The {len(used)} files used here hold {int(used["rows"].sum()):,} rows. Each row has five fields: calendar year, agency, position title, employee name and year-to-date gross pay.

No license is declared on the portal. The State Data Policy, linked from the portal footer, contains no prohibition on reuse and requires a disclaimer on applications that use the data. The disclaimer is stored in `data/ref/mo_data_policy_disclaimer.txt`, and the build sheet places it on the dashboard.

The files report calendar years, and they cannot be converted to fiscal years because each row carries one annual amount with no pay dates. Gross pay includes all pay received and is not base salary. The files have no employee identifier, division, pay type, FTE, hours, hire date or separation date. Headcount therefore counts people paid at any point in a year and is not a count of filled positions.

The {first}-{last} window was chosen to include 2020, the year that most affects row-level measures. The 2020 file holds {s["rows_2020"]:,} clean rows for {s["people_2020"]:,} people. Most people in that file hold two titles, in pairs such as CORRECTIONS OFCR I and CORRECTIONAL OFFICER. The pattern is consistent with a mid-year reclassification that split each person's pay between an old and a new title, although no State document describing it was located. The row-level median for 2020 is ${usd(s["row_median_2020"])}, and the person-level median is ${usd(s["person_median_2020"])}.

## Results

Statewide headcount in {last} is {int(s["statewide_latest"]["headcount"]):,}, compared with {s["headcount_first"]:,} in {first}. Median person-level pay in {last} is ${usd(s["statewide_latest"]["median_pay"])}. {s["top_department"]} is the largest department, with {pct(s["top_department_share"])} of statewide headcount and a median of ${usd(s["top_department_median"])}.

| Year | Headcount | Median pay ($) | Mean pay ($) |
| --- | --- | --- | --- |
{table}

Statewide headcount rose {pct(s["yoy_2023"])} in 2023, and {pct(s["yoy_2023_no_guard"])} excluding National Guard, which first appears in that year with {s["guard_2023"]:,} people. These files cannot separate pay-rate changes from changes in staffing mix, overtime or part-year work, so the mechanism behind any change in median pay is not established here.

## Cleaning decisions

Each row was assigned at most one exclusion reason. Rows with a blank department ({int(total["blank_department_rows"])}) and negative pay ({int(total["negative_pay_rows"])}) were excluded. No row had zero pay. No row was excluded as a duplicate, because every exact duplicate in the window carries a masked name, and two masked people may share a title and pay amount. The files have no payee-type field, so no row was excluded as a non-employee. Board and commission member titles were reviewed and retained because title alone does not separate stipend members from salaried members. `data/clean/EXCLUSIONS.md` gives the counts and rules.

Department names were standardized across {len(xwalk)} raw values in `data/ref/department_xwalk.csv`, with the decision recorded on each row. The raw names were already consistent, so the crosswalk changes letter case and expands one abbreviation.

A person is one pair of department and employee name in a year. Clean files replace the name with `person_key`, a hash that is a pseudonym and offers no anonymity because the State publishes the names. Rows with masked names receive one key each. `person_annual_pay` sums a person's rows, and `is_primary_row` marks the row with the most pay, which supplies the job title. These three fields are additions to the planned schema, and they exist because row-level counts and medians are wrong for people with several rows.

Job titles keep their published spelling apart from collapsed whitespace. `data/clean/title_variants.csv` lists {len(variants)} titles found in one year only whose closest match in other years is at the same grade. The list includes false matches, and it records how many people held both titles as evidence.

`source_row_id` numbers rows after sorting each raw file on all five fields, because repeat downloads returned some files in a different order.

## Reconciliation

`scripts/clean.py` sums pay in integer cents and stops unless clean pay equals raw pay minus excluded pay.

| Year | Raw rows | Excluded rows | Clean rows | Raw pay ($) | Excluded pay ($) | Clean pay ($) |
| --- | --- | --- | --- | --- | --- | --- |
{recon_rows}

Excluded pay is negative because almost all excluded rows have negative amounts, so clean pay exceeds raw pay by ${money(-int(total["excluded_cents"]))} over the window.

## Definitions

Headcount is the count of distinct `person_key` values. Median and mean pay are computed over `person_annual_pay` with one row per person. Year-over-year change is percent change from the previous calendar year. Share is department headcount divided by the statewide total for the same year. Any cell with fewer than five people is hidden. In {last}, that rule hides {s["title_hidden"]:,} of {s["title_cells"]:,} department and job title cells, holding {s["title_hidden_people"]:,} people.

Suppression is a display rule. The State publishes these rows with names, so it provides no confidentiality against a reader of the source files. `docs/DEFINITIONS.md` gives the code for each definition, results for reconciling the dashboard, and limitations.

## Tableau extract

`data/extract/mo_workforce.hyper` holds the tables `pay` and `department_xwalk`. Tableau's documentation states that Tableau Desktop and Tableau Prep open `.hyper` files directly. Its [technical specifications](https://www.tableau.com/products/techspecs) list Tableau extracts for the paid products and omit them from the data sources for Tableau Desktop Public Edition. `data/extract/mo_workforce.csv` is therefore also written, and the build sheet connects to it.

## Reproduce

Python 3.11 or later and uv are required. The full run downloads {manifest["bytes"].sum() / 1e6:.1f} MB and takes a few minutes.

```bash
make fetch
```

```bash
make clean
```

```bash
make extract
```

```bash
make docs
```

```bash
make check
```

A later run may differ if the State revises a file. `data/manifest.csv` records a hash of each file's sorted lines for detecting that.

## Checks

`scripts/check.py` confirms the following results. Raw and clean totals reconcile exactly using decimal arithmetic. Each person has one primary row per year. Hyper and CSV row counts agree. Statewide headcount, median and mean computed by SQL in Hyper match pandas. The Prep inputs reduce to the clean rows and totals after exact duplicates are removed.

## Citation

Office of Administration, State of Missouri ({retrieved[:4]}). State Employee Pay, calendar years {first}-{last}. data.mo.gov. Retrieved {retrieved}.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
