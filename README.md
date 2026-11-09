# Missouri state workforce pay: data preparation for Tableau

This repository prepares State of Missouri employee pay records for a Tableau Public dashboard and a Tableau Prep Builder demonstration flow. It uses the State Employee Pay files that the Office of Administration publishes on data.mo.gov (Office of Administration, 2026). The dashboard reports headcount and pay by department and job title for calendar years 2019 to 2025. The dashboard is published on [Tableau Public](https://public.tableau.com/app/profile/pierce.taylor2096/viz/mo_workforce/MissouriStateWorkforcePay). `scripts/build_workbook.py` generates the workbook, and `docs/TABLEAU_BUILD.md` gives the equivalent manual steps.

`scripts/write_readme.py` writes this file from pipeline outputs. The pipeline ran on Python 3.12.4, pandas 3.1.1 and tableauhyperapi 0.0.26963.

## Plain-language description

This dashboard shows how many people the State of Missouri paid each calendar year, how much the typical person received, and how that differs across departments and job titles. Choose a year to update the charts, then select a department to see only its job titles. Pay means all money a person received during the year, so people who worked part of a year lower the figures, and these amounts are not salary schedules. Groups with fewer than five people are hidden. The figures come from public pay files published by the State's Office of Administration, modified for this use.

## Data source and its limits

The selected source holds one dataset per calendar year from 2007 to 2025, and `data/SOURCES.md` records each dataset, the other candidates reviewed and the retrieval date of 2026-11-09. The 7 files used here hold 535,537 rows. Each row has five fields: calendar year, agency, position title, employee name and year-to-date gross pay.

No license is declared on the portal. The State Data Policy, linked from the portal footer, contains no prohibition on reuse and requires a disclaimer on applications that use the data. The disclaimer is stored in `data/ref/mo_data_policy_disclaimer.txt`, and the build sheet places it on the dashboard.

The files report calendar years, and they cannot be converted to fiscal years because each row carries one annual amount with no pay dates. Gross pay includes all pay received and is not base salary. The files have no employee identifier, division, pay type, FTE, hours, hire date or separation date. Headcount therefore counts people paid at any point in a year and is not a count of filled positions.

The 2019-2025 window was chosen to include 2020, the year that most affects row-level measures. The 2020 file holds 99,663 clean rows for 62,030 people. Most people in that file hold two titles, in pairs such as CORRECTIONS OFCR I and CORRECTIONAL OFFICER. The pattern is consistent with a mid-year reclassification that split each person's pay between an old and a new title, although no State document describing it was located. The row-level median for 2020 is $18,917.20, and the person-level median is $35,783.71.

## Results

Statewide headcount in 2025 is 65,069, compared with 65,691 in 2019. Median person-level pay in 2025 is $44,452.24. Corrections is the largest department, with 18.6% of statewide headcount and a median of $46,483.47.

| Year | Headcount | Median pay ($) | Mean pay ($) |
| --- | --- | --- | --- |
| 2019 | 65,691 | 32,327.93 | 32,265.86 |
| 2020 | 62,030 | 35,783.71 | 35,432.11 |
| 2021 | 61,580 | 35,157.08 | 35,083.16 |
| 2022 | 61,562 | 36,510.07 | 36,617.67 |
| 2023 | 63,510 | 40,307.07 | 40,545.21 |
| 2024 | 64,050 | 43,084.74 | 43,403.45 |
| 2025 | 65,069 | 44,452.24 | 44,857.29 |

Statewide headcount rose 3.2% in 2023, and 2.3% excluding National Guard, which first appears in that year with 551 people. These files cannot separate pay-rate changes from changes in staffing mix, overtime or part-year work, so the mechanism behind any change in median pay is not established here.

## Cleaning decisions

Each row was assigned at most one exclusion reason. Rows with a blank department (1) and negative pay (561) were excluded. No row had zero pay. No row was excluded as a duplicate, because every exact duplicate in the window carries a masked name, and two masked people may share a title and pay amount. The files have no payee-type field, so no row was excluded as a non-employee. Board and commission member titles were reviewed and retained because title alone does not separate stipend members from salaried members. `data/clean/EXCLUSIONS.md` gives the counts and rules.

Department names were standardized across 25 raw values in `data/ref/department_xwalk.csv`, with the decision recorded on each row. The raw names were already consistent, so the crosswalk changes letter case and expands one abbreviation.

A person is one pair of department and employee name in a year. Clean files replace the name with `person_key`, a hash that is a pseudonym and offers no anonymity because the State publishes the names. Rows with masked names receive one key each. `person_annual_pay` sums a person's rows, and `is_primary_row` marks the row with the most pay, which supplies the job title. These three fields are additions to the planned schema, and they exist because row-level counts and medians are wrong for people with several rows.

Job titles keep their published spelling apart from collapsed whitespace. `data/clean/title_variants.csv` lists 61 titles found in one year only whose closest match in other years is at the same grade. The list includes false matches, and it records how many people held both titles as evidence.

`source_row_id` numbers rows after sorting each raw file on all five fields, because repeat downloads returned some files in a different order.

## Definitions

Headcount is the count of distinct `person_key` values. Median and mean pay are computed over `person_annual_pay` with one row per person. Year-over-year change is percent change from the previous calendar year. Share is department headcount divided by the statewide total for the same year. Any cell with fewer than five people is hidden. In 2025, that rule hides 2,061 of 3,311 department and job title cells, holding 3,564 people.

Suppression is a display rule. The State publishes these rows with names, so it provides no confidentiality against a reader of the source files. `docs/DEFINITIONS.md` gives the code for each definition, results for reconciling the dashboard, and limitations.

## Reproduce

Python 3.11 or later and uv are required. The full run downloads 105.8 MB and takes a few minutes.

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

Office of Administration, State of Missouri (2026). State Employee Pay, calendar years 2019-2025. data.mo.gov. Retrieved 2026-11-09.
