"""Run each metric definition in pandas and write docs/DEFINITIONS.md."""
import inspect
import json
import platform
from importlib.metadata import version
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
DOCS = ROOT / "docs"
MIN_CELL = 5
LOW_PAY = 10_000
LATEST = 2025
DEPT_YEAR = ["calendar_year", "department"]
TITLE_YEAR = ["calendar_year", "department", "job_title"]


def headcount(people, by):
    return people.groupby(by)["person_key"].nunique()


def median_pay(people, by):
    return people.groupby(by)["person_annual_pay"].median()


def mean_pay(people, by):
    return people.groupby(by)["person_annual_pay"].mean()


def yoy_change(series):
    return series.groupby("department").pct_change()


def statewide_yoy_change(series):
    return series.pct_change()


def share_of_statewide(counts):
    return counts / counts.groupby("calendar_year").transform("sum")


def suppress(cells):
    return cells.where(cells["headcount"] >= MIN_CELL)


def usd(x):
    return f"{x:,.2f}"


def pct(x):
    return "n/a" if pd.isna(x) else f"{100 * x:.1f}%".replace("-0.0%", "0.0%")


def code(*functions):
    return "```python\n" + "\n".join(inspect.getsource(f) for f in functions).strip() + "\n```"


def md_table(frame):
    head = "| " + " | ".join(frame.columns) + " |\n|" + " --- |" * len(frame.columns)
    return head + "\n" + "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in frame.itertuples(index=False))


def main():
    DOCS.mkdir(exist_ok=True)
    pay = pd.concat([pd.read_csv(f) for f in sorted(CLEAN.glob("pay_CY*.csv"))], ignore_index=True)
    people = pay[pay["is_primary_row"] == 1]

    state = pd.DataFrame({"headcount": headcount(people, "calendar_year"), "median_pay": median_pay(people, "calendar_year"),
                          "mean_pay": mean_pay(people, "calendar_year")})
    state["headcount_yoy"] = statewide_yoy_change(state["headcount"])
    state["median_yoy"] = statewide_yoy_change(state["median_pay"])
    state.to_csv(CLEAN / "metrics_statewide.csv", lineterminator="\n")

    dept = pd.DataFrame({"headcount": headcount(people, DEPT_YEAR), "median_pay": median_pay(people, DEPT_YEAR), "mean_pay": mean_pay(people, DEPT_YEAR)})
    dept["share"] = share_of_statewide(dept["headcount"])
    dept["headcount_yoy"] = yoy_change(dept["headcount"])
    dept["median_yoy"] = yoy_change(dept["median_pay"])
    dept.to_csv(CLEAN / "metrics_department_year.csv", lineterminator="\n")

    titles = pd.DataFrame({"headcount": headcount(people, TITLE_YEAR), "median_pay": median_pay(people, TITLE_YEAR), "mean_pay": mean_pay(people, TITLE_YEAR)})
    shown = suppress(titles)
    latest_titles = titles.loc[LATEST]
    hidden = latest_titles[latest_titles["headcount"] < MIN_CELL]

    top5 = dept.loc[LATEST].sort_values("headcount", ascending=False).head(5).index.tolist()
    rows_vs_people = pd.DataFrame({"rows": pay.groupby("calendar_year").size(), "people": headcount(people, "calendar_year"),
                                   "row_median": pay.groupby("calendar_year")["annual_pay"].median(),
                                   "person_median": median_pay(people, "calendar_year")})

    latest_people = people[people["calendar_year"] == LATEST]
    multi = int((pay[pay["calendar_year"] == LATEST].groupby("person_key").size() > 1).sum())
    low = int((latest_people["person_annual_pay"] < LOW_PAY).sum())
    raw = pd.read_csv(ROOT / "data" / "raw" / f"{LATEST}.csv", dtype=str, keep_default_na=False)
    raw.columns = ["year", "agency", "title", "name", "pay"]
    named = raw[~raw["name"].str.startswith("PROTECTED") & (raw["agency"] != "")]
    two_agency = int((named.groupby("name")["agency"].nunique() > 1).sum())
    guard_2023 = int(dept.loc[(2023, "National Guard"), "headcount"])
    excl_guard = state.loc[2023, "headcount"] - guard_2023
    yoy_no_guard = excl_guard / state.loc[2022, "headcount"] - 1
    protected = int(pay["person_key"].str.startswith("X").sum())
    dept_hidden = int((dept["headcount"] < MIN_CELL).sum())
    low_median = dept.loc[LATEST].query("median_pay < @LOW_PAY").sort_values("median_pay")
    low_median_text = " and ".join(f"{d} (${usd(m)}, {int(h):,} people)" for d, m, h in zip(low_median.index, low_median["median_pay"], low_median["headcount"]))

    summary = {"latest": LATEST, "first": int(state.index.min()), "statewide_latest": {k: float(v) for k, v in state.loc[LATEST].items()},
               "headcount_first": int(state["headcount"].iloc[0]), "top_department": top5[0], "top_department_share": float(dept.loc[(LATEST, top5[0]), "share"]),
               "top_department_median": float(dept.loc[(LATEST, top5[0]), "median_pay"]), "rows_2020": int(rows_vs_people.loc[2020, "rows"]),
               "people_2020": int(rows_vs_people.loc[2020, "people"]), "row_median_2020": float(rows_vs_people.loc[2020, "row_median"]),
               "person_median_2020": float(rows_vs_people.loc[2020, "person_median"]), "low_share": low / len(latest_people), "multi": multi,
               "two_agency": two_agency, "guard_2023": guard_2023, "yoy_2023": float(state.loc[2023, "headcount_yoy"]), "yoy_2023_no_guard": float(yoy_no_guard),
               "title_cells": len(latest_titles), "title_hidden": len(hidden), "title_hidden_people": int(hidden["headcount"].sum()),
               "people_rows": len(people), "pay_rows": len(pay), "shown_cells": int(shown.loc[LATEST, "headcount"].notna().sum()),
               "versions": {"python": platform.python_version(), "pandas": version("pandas"), "tableauhyperapi": version("tableauhyperapi")}}
    (CLEAN / "metrics_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    state_table = md_table(pd.DataFrame({"Year": state.index, "Headcount": state["headcount"].map("{:,}".format).values, "Median pay ($)": state["median_pay"].map(usd).values,
                                         "Mean pay ($)": state["mean_pay"].map(usd).values, "Headcount YoY": state["headcount_yoy"].map(pct).values, "Median YoY": state["median_yoy"].map(pct).values}))
    top = dept.loc[(dept.index.get_level_values("department").isin(top5))].reset_index()
    top["order"] = top["department"].map({d: i for i, d in enumerate(top5)})
    top = top.sort_values(["order", "calendar_year"])
    top_table = md_table(pd.DataFrame({"Department": top["department"].values, "Year": top["calendar_year"].values, "Headcount": top["headcount"].map("{:,}".format).values,
                                       "Share": top["share"].map(pct).values, "Median pay ($)": top["median_pay"].map(usd).values, "Mean pay ($)": top["mean_pay"].map(usd).values,
                                       "Headcount YoY": top["headcount_yoy"].map(pct).values, "Median YoY": top["median_yoy"].map(pct).values}))
    compare = md_table(pd.DataFrame({"Year": rows_vs_people.index, "Rows": rows_vs_people["rows"].map("{:,}".format).values, "People": rows_vs_people["people"].map("{:,}".format).values,
                                     "Row-level median ($)": rows_vs_people["row_median"].map(usd).values, "Person-level median ($)": rows_vs_people["person_median"].map(usd).values}))
    v = summary["versions"]
    (DOCS / "DEFINITIONS.md").write_text(f"""# Metric definitions

`scripts/metrics.py` writes this file, runs every expression shown, and produces every number in it. The run used Python {v["python"]}, pandas {v["pandas"]} and tableauhyperapi {v["tableauhyperapi"]}. The inputs are the clean files `data/clean/pay_CY*.csv`. Results for all departments and years are in `data/clean/metrics_department_year.csv`.

## Terms

A *person* is one distinct pair of department and employee name within a calendar year. The State files carry no employee identifier, so a name is the only identifying field. `person_key` is a hash of that pair, which keeps names out of the dashboard files. The hash is a pseudonym and offers no anonymity, because the State publishes the names. Each row with a masked `PROTECTED` name receives its own key, and {protected:,} rows were treated this way. *Annual pay* is `ytd_gross_pay`, the gross amount paid in the calendar year.

`person_annual_pay` is the sum of annual pay across all of a person's rows in one department and year. `is_primary_row` equals 1 on the row with the most pay for that person, with ties broken by `source_row_id`. The primary row supplies the person's job title. The frame `people` below holds only primary rows, so it has one row per person and year, and {summary["people_rows"]:,} rows out of {summary["pay_rows"]:,} in the clean data.

## Definitions

**Headcount** is the number of distinct person keys in a group. Department headcounts sum to the statewide headcount because the person key includes the department.

{code(headcount)}

**Median and mean annual pay** are computed over `person_annual_pay` on the frame `people`. The `by` argument is `calendar_year` for statewide results, (`calendar_year`, `department`) for departments, and (`calendar_year`, `department`, `job_title`) for job titles.

{code(median_pay, mean_pay)}

**Year-over-year change** is the percent change from the previous calendar year, for headcount and for median pay. It is undefined for the first year of each series.

{code(yoy_change, statewide_yoy_change)}

**Share of statewide headcount** is department headcount divided by the sum of department headcounts for the same year.

{code(share_of_statewide)}

**Suppression** hides every value in a cell with fewer than {MIN_CELL} people. In the frame below, `cells` holds headcount, median pay and mean pay for one grouping.

{code(suppress)}

## Results for reconciliation

The statewide results for each year are below.

{state_table}

The five largest departments by {LATEST} headcount are below.

{top_table}

In {LATEST}, {len(latest_titles):,} department and job title cells exist. Suppression hides {len(hidden):,} cells, which hold {int(hidden["headcount"].sum()):,} people, and leaves {summary["shown_cells"]:,} cells visible. Department-year cells with fewer than {MIN_CELL} people number {dept_hidden}.

The next table places row-level figures beside person-level figures. Rows exceed people because a person changing title within a year receives one row per title.

{compare}

## Limitations of pay data as a headcount proxy

Headcount here counts people paid at any point in the year, so it is not a point-in-time count of filled positions and it cannot be compared directly with such counts. The files have no hire date, separation date, FTE or hours, so part-year and part-time work cannot be identified. Those people lower median and mean pay. In {LATEST}, {pct(summary["low_share"])} of people received less than ${LOW_PAY:,}. The {LATEST} department medians below ${LOW_PAY:,} are {low_median_text}. A median at that level means at least half of the people in the department received under ${LOW_PAY:,} during the year. The files do not state whether these people are seasonal, part-time or paid for short periods of duty.

A person with several titles has several rows, and {multi:,} people had two or more rows in {LATEST}. The person-level calculation removes this effect for pay and headcount, and the job title shown is the title with the most pay. Pay reported for a title therefore includes pay earned under the person's other titles that year.

Names identify people imperfectly. Two employees with the same name in one department merge into one person and lower headcount. A person paid by two departments counts once in each and raises statewide headcount, and {two_agency:,} names appeared in two or more departments in {LATEST}. Those names include different people who share a name, and the two cases cannot be separated.

Gross pay is not base salary. It includes all pay received, so these figures do not describe salary schedules and a change in median pay can reflect changes in the mix of staff, in overtime, in part-year work or in pay rates.

National Guard first appears in calendar year 2023 with {guard_2023:,} people. Statewide headcount rose {pct(summary["yoy_2023"])} in 2023, and the rise excluding National Guard is {pct(summary["yoy_2023_no_guard"])}. The files do not state why the department was added.
""", encoding="utf-8")
    print(f"statewide {LATEST}: headcount {int(state.loc[LATEST, 'headcount']):,}, median {usd(state.loc[LATEST, 'median_pay'])}, mean {usd(state.loc[LATEST, 'mean_pay'])}")
    print(f"top 5: {top5}; title cells {len(latest_titles):,}, hidden {len(hidden):,}")


if __name__ == "__main__":
    main()
