"""Degrade two clean years into messy inputs for the Tableau Prep flow."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "data" / "prep_inputs"
SEED = 2026
DUPLICATE_SHARE = 0.02
A_FILE, B_FILE = "prep_input_a_cy2024.csv", "prep_input_b_cy2025.csv"
KEEP = ["calendar_year", "department", "job_title", "annual_pay", "person_key", "source_row_id"]


def read_year(year):
    return pd.read_csv(CLEAN / f"pay_CY{year % 100:02d}.csv", usecols=KEEP, dtype={"annual_pay": str})


def mix_case(titles, rng):
    """Leave a third of titles uppercase, and lowercase or titlecase the remaining two thirds."""
    choice = rng.integers(0, 3, len(titles))
    return [t if c == 0 else t.lower() if c == 1 else t.title() for t, c in zip(titles, choice)]


def add_duplicates(df, rng):
    extra = df.iloc[rng.choice(len(df), round(len(df) * DUPLICATE_SHARE), replace=False)]
    combined = pd.concat([df, extra], ignore_index=True)
    return combined.iloc[rng.permutation(len(combined))], len(extra)


def as_text_money(values):
    return [f"${float(v):,.2f}" for v in values]


def cents(values):
    return sum(int(v.replace(".", "")) for v in values)


def money(c):
    return f"{c // 100:,}.{c % 100:02d}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    xwalk = pd.read_csv(ROOT / "data" / "ref" / "department_xwalk.csv")
    codes = xwalk[["department_code", "canonical_department"]].rename(columns={"canonical_department": "department"})
    codes.to_csv(OUT / "department_codes.csv", index=False, lineterminator="\n")
    to_code = dict(zip(codes["department"], codes["department_code"]))

    clean_a, clean_b = read_year(2024), read_year(2025)
    a = clean_a.assign(job_title=mix_case(clean_a["job_title"], rng), annual_pay=as_text_money(clean_a["annual_pay"]))
    a = a.rename(columns={"calendar_year": "YR", "department": "AGENCY", "job_title": "TITLE", "annual_pay": "GROSS_PAY",
                          "person_key": "EMP_KEY", "source_row_id": "ROW_ID"})
    b = clean_b.assign(job_title=mix_case(clean_b["job_title"], rng), department=clean_b["department"].map(to_code))
    b = b.rename(columns={"calendar_year": "Calendar Year", "department": "Dept Code", "job_title": "Job Title",
                          "annual_pay": "Pay Amount", "person_key": "Employee", "source_row_id": "Row Identifier"})
    b = b[["Row Identifier", "Employee", "Pay Amount", "Job Title", "Dept Code", "Calendar Year"]]
    a, dup_a = add_duplicates(a, rng)
    b, dup_b = add_duplicates(b, rng)
    a.to_csv(OUT / A_FILE, index=False, lineterminator="\n")
    b.to_csv(OUT / B_FILE, index=False, lineterminator="\n")

    clean = pd.concat([clean_a, clean_b])
    expected = (clean.assign(c=[int(v.replace(".", "")) for v in clean["annual_pay"]])
                .groupby(["calendar_year", "department"])
                .agg(total_pay_cents=("c", "sum"), headcount=("person_key", "nunique"), rows=("c", "size")).reset_index())
    out = expected.assign(total_pay=[f"{c // 100}.{c % 100:02d}" for c in expected["total_pay_cents"]])
    out[["calendar_year", "department", "headcount", "rows", "total_pay"]].to_csv(OUT / "expected_output.csv", index=False, lineterminator="\n")
    write_readme(len(clean_a), dup_a, len(clean_b), dup_b, cents(clean_a["annual_pay"]), cents(clean_b["annual_pay"]), len(codes),
                 clean_a["person_key"].nunique(), clean_b["person_key"].nunique())
    print(f"A {len(clean_a):,} + {dup_a:,} duplicates; B {len(clean_b):,} + {dup_b:,} duplicates; {len(codes)} codes")


def write_readme(n_a, dup_a, n_b, dup_b, pay_a, pay_b, n_codes, people_a, people_b):
    variants = pd.read_csv(CLEAN / "title_variants.csv")
    shown = variants[variants["only_year"].isin([2024, 2025]) & (variants["closest_title_last_year"] >= 2024) & (variants["shared_people"] > 0)].head(5)
    examples = "\n".join(f"| {r.job_title} | {r.closest_title} | {r.similarity} | {r.shared_people} |" for r in shown.itertuples())
    (OUT / "README.md").write_text(f"""# Tableau Prep inputs

`scripts/make_prep_inputs.py` writes this file and every number in it, with random seed {SEED}. The two input files are copies of the clean calendar-year 2024 and 2025 data with defects added on purpose. They are for the Prep Builder demonstration and must not feed the dashboard.

`{A_FILE}` holds {n_a + dup_a:,} rows and `{B_FILE}` holds {n_b + dup_b:,} rows. `department_codes.csv` maps {n_codes} codes to department names. The codes were assigned by this repository in alphabetical order and are not State codes.

## Defects and the Prep step that fixes each

| Defect | File | Prep step |
| --- | --- | --- |
| Column names differ: `YR`, `AGENCY`, `TITLE`, `GROSS_PAY`, `EMP_KEY`, `ROW_ID` against `Calendar Year`, `Dept Code`, `Job Title`, `Pay Amount`, `Employee`, `Row Identifier` | Both | Clean step: rename each field to `calendar_year`, `department`, `job_title`, `annual_pay`, `person_key`, `source_row_id` |
| Column order differs | Both | Union: fields align by name after renaming |
| Department appears as a code | B | Join to `department_codes.csv` on `Dept Code` = `department_code`, then remove both code fields |
| Pay is text with `$` and commas | A | Clean step: calculated field, then number (decimal) data type |
| Job titles mix uppercase, lowercase and titlecase | Both | Clean step: More options > Clean > Make Uppercase on `job_title` |
| Exact duplicate rows, {dup_a:,} in A and {dup_b:,} in B | Both | Aggregate step grouped by all six fields, with nothing aggregated |
| Real spelling variants among titles | Both | Clean step: More options > Group Values > Spelling on `job_title`, reviewing each group |
| Row-level grain | Combined | Aggregate step to `calendar_year` and `department` |

## Flow, in order

1. Add both CSV files as inputs. Set `department_codes.csv` aside for step 3.
2. Add a Clean step to file A and rename its fields. Add a calculated field named `annual_pay_num` with `FLOAT(REPLACE(REPLACE([annual_pay], "$", ""), ",", ""))`. Remove the text field and rename the new field `annual_pay`. Tableau's Clean documentation does not state whether Remove Punctuation removes decimal points, and removing them would multiply pay by 100, so the calculation is used for this field.
3. Add a Clean step to file B and rename its fields. Set `annual_pay` to number (decimal) with the data type icon on the profile card. Add a Join step to `department_codes.csv` on the code, use an inner join, and remove both code fields after confirming that no rows are unmatched.
4. Add a Union step with both branches. Resolve any entry in the Mismatched Fields list with Merge Fields. The union holds {n_a + dup_a + n_b + dup_b:,} rows.
5. Add a Clean step. Apply Make Uppercase to `job_title`, then Group Values > Spelling to `job_title`. Accept only groups that differ in spelling. Reject any group that merges grade levels such as I and II.
6. Add an Aggregate step and group by all six fields with no aggregated field. The result holds {n_a + n_b:,} rows. Genuine repeats survive because `source_row_id` differs between them.
7. Add an Aggregate step grouped by `calendar_year` and `department`. Add `annual_pay` as SUM, `person_key` as COUNT DISTINCT, and `source_row_id` as COUNT.
8. Add an Output step. Set Save output to File and Output type to Tableau Data Extract (.hyper).

Tableau's documentation does not describe a dedicated action for removing duplicate rows. The Aggregate step in step 6 removes them because rows identical on every grouped field collapse to one.

## Expected results

| Check | CY2024 | CY2025 |
| --- | --- | --- |
| Rows after step 6 | {n_a:,} | {n_b:,} |
| Total `annual_pay` ($) | {money(pay_a)} | {money(pay_b)} |
| Distinct `person_key` | {people_a:,} | {people_b:,} |

`expected_output.csv` gives headcount, row count and total pay for each department and year, for comparison with the output of step 7. Grouping job titles in step 5 does not change those figures, because step 7 does not use `job_title`.

## Candidate variants for review

The pairs below come from `data/clean/title_variants.csv`. Shared people counts the person keys holding both titles. Pairs whose final words name different roles, such as a specialist and a supervisor, should be rejected.

| Title | Closest title | Similarity | Shared people |
| --- | --- | --- | --- |
{examples}

Similar spelling alone is weak evidence. The same file also contains pairs with different meanings, so each suggested group needs review.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
