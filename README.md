# Missouri state workforce pay: data preparation for Tableau

This repository prepares the State Employee Pay files that the Office of Administration publishes on data.mo.gov (Office of Administration, 2026). The output feeds a [Tableau Public dashboard](https://public.tableau.com/app/profile/pierce.taylor2096/viz/mo_workforce/MissouriStateWorkforcePay) of headcount and pay by department and job title for calendar years 2019 to 2025, and a Tableau Prep demonstration flow. `scripts/write_readme.py` writes this file; the pipeline ran on Python 3.12.4, pandas 3.1.1 and tableauhyperapi 0.0.26963.

## Plain-language description

This dashboard shows how many people the State of Missouri paid each calendar year, how much the typical person received, and how that differs across departments and job titles. Choose a year to update the charts, then select a department to see only its job titles. Pay means all money a person received during the year, so people who worked part of a year lower the figures, and these amounts are not salary schedules. Groups with fewer than five people are hidden. The figures come from public pay files published by the State's Office of Administration, modified for this use.

## Data source and limits

The source has one file per calendar year from 2007 to 2025, each with calendar year, agency, position title, employee name and year-to-date gross pay. The 7 files used hold 535,537 rows and were retrieved on 2026-11-09; `data/SOURCES.md` records each file and the other candidates reviewed. The portal declares no license, and the State Data Policy contains no prohibition on reuse but requires the notice in `data/ref/mo_data_policy_disclaimer.txt`, which the dashboard displays.

The files report calendar years and cannot be converted to fiscal years, because each row carries one annual amount with no pay dates. Pay is gross pay and not base salary. With no employee identifier, FTE or hire date, headcount counts people paid at any point in a year. Most people in the 2020 file hold two titles, consistent with a mid-year reclassification, so the 2020 row-level median of $18,917.20 understates the person-level median of $35,783.71.

## Results

In 2025, 65,069 people were paid at a person-level median of $44,452.24, and Corrections held 18.6% of statewide headcount. `docs/DEFINITIONS.md` gives department results and limitations.

| Year | Headcount | Median pay ($) | Mean pay ($) |
| --- | --- | --- | --- |
| 2019 | 65,691 | 32,327.93 | 32,265.86 |
| 2020 | 62,030 | 35,783.71 | 35,432.11 |
| 2021 | 61,580 | 35,157.08 | 35,083.16 |
| 2022 | 61,562 | 36,510.07 | 36,617.67 |
| 2023 | 63,510 | 40,307.07 | 40,545.21 |
| 2024 | 64,050 | 43,084.74 | 43,403.45 |
| 2025 | 65,069 | 44,452.24 | 44,857.29 |

## Cleaning decisions

Rows with a blank department (1) or negative pay (561) were excluded, and no row had zero pay. Exact duplicates were kept because every one carries a masked name and may be a different person. Board and commission members were kept because title alone does not separate stipend from salaried members. `data/clean/EXCLUSIONS.md` gives the rules, counts and the reconciliation of raw to clean pay.

A person is one department and name pair per year, carried as the hash `person_key`. `person_annual_pay` sums a person's rows, and `is_primary_row` marks the row that supplies the job title. Department names needed only case changes and one expanded abbreviation, and 61 single-year title variants are listed in `data/clean/title_variants.csv`.

## Definitions

Headcount is the count of distinct `person_key` values. Median and mean pay use `person_annual_pay` with one row per person. Year-over-year change is percent change from the previous year, and share is department headcount over the statewide total. Cells with fewer than five people are hidden, which in 2025 hides 2,061 of 3,311 department and job title cells. Suppression is a display rule only, because the State publishes these rows with names.

## Reproduce

Python 3.11 or later and uv are required. `make fetch clean extract docs check` downloads 105.8 MB, rebuilds every output including the workbook `data/extract/mo_workforce.twb`, and runs `scripts/check.py`. `docs/TABLEAU_BUILD.md` gives the manual Tableau steps.

## Citation

Office of Administration, State of Missouri (2026). State Employee Pay, calendar years 2019-2025. data.mo.gov. Retrieved 2026-11-09.
