"""Write README.md from the pipeline outputs."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DASHBOARD_URL = "https://public.tableau.com/app/profile/pierce.taylor2096/viz/mo_workforce/MissouriStateWorkforcePay"


def money(cents):
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) // 100:,}.{abs(cents) % 100:02d}"


def dollars(cents):
    return ("-" if cents < 0 else "") + "$" + money(abs(cents))


def usd(x):
    return f"{x:,.2f}"


def pct(x):
    return f"{100 * x:.1f}%"


def main():
    s = json.loads((CLEAN / "metrics_summary.json").read_text(encoding="utf-8"))
    total = pd.read_csv(CLEAN / "reconciliation.csv").set_index("calendar_year").loc["TOTAL"]
    state = pd.read_csv(CLEAN / "metrics_statewide.csv").set_index("calendar_year")
    manifest = pd.read_csv(ROOT / "data" / "manifest.csv")
    variants = pd.read_csv(CLEAN / "title_variants.csv")
    retrieved = manifest["retrieved"].iloc[0]
    first, last = s["first"], s["latest"]
    v = s["versions"]
    used = manifest[manifest["calendar_year"].between(first, last)]
    table = "\n".join(f"| {y} | {int(r.headcount):,} | {usd(r.median_pay)} | {usd(r.mean_pay)} |" for y, r in state.iterrows())
    (ROOT / "README.md").write_text(f"""# Missouri state workforce pay: data preparation for Tableau

This repository prepares the State Employee Pay files that the Office of Administration publishes on data.mo.gov (Office of Administration, {retrieved[:4]}). The output feeds a [Tableau Public dashboard]({DASHBOARD_URL}) of headcount and pay by department and job title for calendar years {first} to {last}, and a Tableau Prep demonstration flow. `scripts/write_readme.py` writes this file; the pipeline ran on Python {v["python"]}, pandas {v["pandas"]} and tableauhyperapi {v["tableauhyperapi"]}.

## Plain-language description

This dashboard shows how many people the State of Missouri paid each calendar year, how much the typical person received, and how that differs across departments and job titles. Choose a year to update the charts, then select a department to see only its job titles. Pay means all money a person received during the year, so people who worked part of a year lower the figures, and these amounts are not salary schedules. Groups with fewer than five people are hidden. The figures come from public pay files published by the State's Office of Administration, modified for this use.

## Data source and limits

The source has one file per calendar year from {manifest["calendar_year"].min()} to {manifest["calendar_year"].max()}, each with calendar year, agency, position title, employee name and year-to-date gross pay. The {len(used)} files used hold {int(used["rows"].sum()):,} rows and were retrieved on {retrieved}; `data/SOURCES.md` records each file and the other candidates reviewed. The portal declares no license, and the State Data Policy contains no prohibition on reuse but requires the notice in `data/ref/mo_data_policy_disclaimer.txt`, which the dashboard displays.

The files report calendar years and cannot be converted to fiscal years, because each row carries one annual amount with no pay dates. Pay is gross pay and not base salary. With no employee identifier, FTE or hire date, headcount counts people paid at any point in a year. Most people in the 2020 file hold two titles, consistent with a mid-year reclassification, so the 2020 row-level median of ${usd(s["row_median_2020"])} understates the person-level median of ${usd(s["person_median_2020"])}.

## Results

In {last}, {int(s["statewide_latest"]["headcount"]):,} people were paid at a person-level median of ${usd(s["statewide_latest"]["median_pay"])}, and {s["top_department"]} held {pct(s["top_department_share"])} of statewide headcount. `docs/DEFINITIONS.md` gives department results and limitations.

| Year | Headcount | Median pay ($) | Mean pay ($) |
| --- | --- | --- | --- |
{table}

## Cleaning decisions

Rows with a blank department ({int(total["blank_department_rows"])}) or negative pay ({int(total["negative_pay_rows"])}) were excluded, and no row had zero pay. Exact duplicates were kept because every one carries a masked name and may be a different person. Board and commission members were kept because title alone does not separate stipend from salaried members. `data/clean/EXCLUSIONS.md` gives the rules, counts and the reconciliation of raw to clean pay.

A person is one department and name pair per year, carried as the hash `person_key`. `person_annual_pay` sums a person's rows, and `is_primary_row` marks the row that supplies the job title. Department names needed only case changes and one expanded abbreviation, and {len(variants)} single-year title variants are listed in `data/clean/title_variants.csv`.

## Definitions

Headcount is the count of distinct `person_key` values. Median and mean pay use `person_annual_pay` with one row per person. Year-over-year change is percent change from the previous year, and share is department headcount over the statewide total. Cells with fewer than five people are hidden, which in {last} hides {s["title_hidden"]:,} of {s["title_cells"]:,} department and job title cells. Suppression is a display rule only, because the State publishes these rows with names.

## Reproduce

Python 3.11 or later and uv are required. `make fetch clean extract docs check` downloads {manifest["bytes"].sum() / 1e6:.1f} MB, rebuilds every output including the workbook `data/extract/mo_workforce.twb`, and runs `scripts/check.py`. `docs/TABLEAU_BUILD.md` gives the manual Tableau steps.

## Citation

Office of Administration, State of Missouri ({retrieved[:4]}). State Employee Pay, calendar years {first}-{last}. data.mo.gov. Retrieved {retrieved}.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
