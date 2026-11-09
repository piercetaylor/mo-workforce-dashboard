# Tableau Prep inputs

`scripts/make_prep_inputs.py` writes this file and every number in it, with random seed 2026. The two input files are copies of the clean calendar-year 2024 and 2025 data with defects added on purpose. They are for the Prep Builder demonstration and must not feed the dashboard.

`prep_input_a_cy2024.csv` holds 74,261 rows and `prep_input_b_cy2025.csv` holds 75,155 rows. `department_codes.csv` maps 25 codes to department names. The codes were assigned by this repository in alphabetical order and are not State codes.

## Defects and the Prep step that fixes each

| Defect | File | Prep step |
| --- | --- | --- |
| Column names differ: `YR`, `AGENCY`, `TITLE`, `GROSS_PAY`, `EMP_KEY`, `ROW_ID` against `Calendar Year`, `Dept Code`, `Job Title`, `Pay Amount`, `Employee`, `Row Identifier` | Both | Clean step: rename each field to `calendar_year`, `department`, `job_title`, `annual_pay`, `person_key`, `source_row_id` |
| Column order differs | Both | Union: fields align by name after renaming |
| Department appears as a code | B | Join to `department_codes.csv` on `Dept Code` = `department_code`, then remove both code fields |
| Pay is text with `$` and commas | A | Clean step: calculated field, then number (decimal) data type |
| Job titles mix uppercase, lowercase and titlecase | Both | Clean step: More options > Clean > Make Uppercase on `job_title` |
| Exact duplicate rows, 1,456 in A and 1,474 in B | Both | Aggregate step grouped by all six fields, with nothing aggregated |
| Real spelling variants among titles | Both | Clean step: More options > Group Values > Spelling on `job_title`, reviewing each group |
| Row-level grain | Combined | Aggregate step to `calendar_year` and `department` |

## Flow, in order

1. Add both CSV files as inputs. Set `department_codes.csv` aside for step 3.
2. Add a Clean step to file A and rename its fields. Add a calculated field named `annual_pay_num` with `FLOAT(REPLACE(REPLACE([annual_pay], "$", ""), ",", ""))`. Remove the text field and rename the new field `annual_pay`. Tableau's Clean documentation does not state whether Remove Punctuation removes decimal points, and removing them would multiply pay by 100, so the calculation is used for this field.
3. Add a Clean step to file B and rename its fields. Set `annual_pay` to number (decimal) with the data type icon on the profile card. Add a Join step to `department_codes.csv` on the code, use an inner join, and remove both code fields after confirming that no rows are unmatched.
4. Add a Union step with both branches. Resolve any entry in the Mismatched Fields list with Merge Fields. The union holds 149,416 rows.
5. Add a Clean step. Apply Make Uppercase to `job_title`, then Group Values > Spelling to `job_title`. Accept only groups that differ in spelling. Reject any group that merges grade levels such as I and II.
6. Add an Aggregate step and group by all six fields with no aggregated field. The result holds 146,486 rows. Genuine repeats survive because `source_row_id` differs between them.
7. Add an Aggregate step grouped by `calendar_year` and `department`. Add `annual_pay` as SUM, `person_key` as COUNT DISTINCT, and `source_row_id` as COUNT.
8. Add an Output step. Set Save output to File and Output type to Tableau Data Extract (.hyper).

Tableau's documentation does not describe a dedicated action for removing duplicate rows. The Aggregate step in step 6 removes them because rows identical on every grouped field collapse to one.

## Expected results

| Check | CY2024 | CY2025 |
| --- | --- | --- |
| Rows after step 6 | 72,805 | 73,681 |
| Total `annual_pay` ($) | 2,779,990,709.04 | 2,918,818,914.41 |
| Distinct `person_key` | 64,050 | 65,069 |

`expected_output.csv` gives headcount, row count and total pay for each department and year, for comparison with the output of step 7. Grouping job titles in step 5 does not change those figures, because step 7 does not use `job_title`.

## Candidate variants for review

The pairs below come from `data/clean/title_variants.csv`. Shared people counts the person keys holding both titles. Pairs whose final words name different roles, such as a specialist and a supervisor, should be rejected.

| Title | Closest title | Similarity | Shared people |
| --- | --- | --- | --- |
| DRIVER EXAMINER SUP | DRIVER EXAMINER SPRV | 0.923 | 43 |
| DRIVER EXAMINER CHIEF | DRIVER EXAMINER - CHIEF | 0.955 | 11 |
| FRSTRY FIELD PROGRAMS SPEC | FORESTRY FIELD PROGRAMS SUPV | 0.889 | 3 |
| BRANCH ADMINISTRATIVE MANAGER | ADMINISTRATIVE MANAGER | 0.863 | 2 |
| CAPITAL PLANNING SOFTWARE SPEC | CAPITAL PLANNING SOFTWARE COOR | 0.9 | 1 |

Similar spelling alone is weak evidence. The same file also contains pairs with different meanings, so each suggested group needs review.
