# Metric definitions

`scripts/metrics.py` writes this file, runs every expression shown, and produces every number in it. The run used Python 3.12.4, pandas 3.1.1 and tableauhyperapi 0.0.26963. The inputs are the clean files `data/clean/pay_CY*.csv`. Results for all departments and years are in `data/clean/metrics_department_year.csv`.

## Terms

A *person* is one distinct pair of department and employee name within a calendar year. The State files carry no employee identifier, so a name is the only identifying field. `person_key` is a hash of that pair, which keeps names out of the dashboard files. The hash is a pseudonym and offers no anonymity, because the State publishes the names. Each row with a masked `PROTECTED` name receives its own key, and 432 rows were treated this way. *Annual pay* is `ytd_gross_pay`, the gross amount paid in the calendar year.

`person_annual_pay` is the sum of annual pay across all of a person's rows in one department and year. `is_primary_row` equals 1 on the row with the most pay for that person, with ties broken by `source_row_id`. The primary row supplies the person's job title. The frame `people` below holds only primary rows, so it has one row per person and year, and 443,492 rows out of 534,975 in the clean data.

## Definitions

**Headcount** is the number of distinct person keys in a group. Department headcounts sum to the statewide headcount because the person key includes the department.

```python
def headcount(people, by):
    return people.groupby(by)["person_key"].nunique()
```

**Median and mean annual pay** are computed over `person_annual_pay` on the frame `people`. The `by` argument is `calendar_year` for statewide results, (`calendar_year`, `department`) for departments, and (`calendar_year`, `department`, `job_title`) for job titles.

```python
def median_pay(people, by):
    return people.groupby(by)["person_annual_pay"].median()

def mean_pay(people, by):
    return people.groupby(by)["person_annual_pay"].mean()
```

**Year-over-year change** is the percent change from the previous calendar year, for headcount and for median pay. It is undefined for the first year of each series.

```python
def yoy_change(series):
    return series.groupby("department").pct_change()

def statewide_yoy_change(series):
    return series.pct_change()
```

**Share of statewide headcount** is department headcount divided by the sum of department headcounts for the same year.

```python
def share_of_statewide(counts):
    return counts / counts.groupby("calendar_year").transform("sum")
```

**Suppression** hides every value in a cell with fewer than 5 people. In the frame below, `cells` holds headcount, median pay and mean pay for one grouping.

```python
def suppress(cells):
    return cells.where(cells["headcount"] >= MIN_CELL)
```

## Results for reconciliation

The statewide results for each year are below.

| Year | Headcount | Median pay ($) | Mean pay ($) | Headcount YoY | Median YoY |
| --- | --- | --- | --- | --- | --- |
| 2019 | 65,691 | 32,327.93 | 32,265.86 | n/a | n/a |
| 2020 | 62,030 | 35,783.71 | 35,432.11 | -5.6% | 10.7% |
| 2021 | 61,580 | 35,157.08 | 35,083.16 | -0.7% | -1.8% |
| 2022 | 61,562 | 36,510.07 | 36,617.67 | 0.0% | 3.8% |
| 2023 | 63,510 | 40,307.07 | 40,545.21 | 3.2% | 10.4% |
| 2024 | 64,050 | 43,084.74 | 43,403.45 | 0.9% | 6.9% |
| 2025 | 65,069 | 44,452.24 | 44,857.29 | 1.6% | 3.2% |

The five largest departments by 2025 headcount are below.

| Department | Year | Headcount | Share | Median pay ($) | Mean pay ($) | Headcount YoY | Median YoY |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Corrections | 2019 | 12,385 | 18.9% | 34,104.27 | 30,143.45 | n/a | n/a |
| Corrections | 2020 | 11,335 | 18.3% | 38,628.50 | 34,692.45 | -8.5% | 13.3% |
| Corrections | 2021 | 11,026 | 17.9% | 39,285.67 | 34,663.96 | -2.7% | 1.7% |
| Corrections | 2022 | 10,808 | 17.6% | 40,740.12 | 35,863.81 | -2.0% | 3.7% |
| Corrections | 2023 | 11,551 | 18.2% | 43,459.05 | 38,198.01 | 6.9% | 6.7% |
| Corrections | 2024 | 11,929 | 18.6% | 45,265.41 | 39,778.92 | 3.3% | 4.2% |
| Corrections | 2025 | 12,078 | 18.6% | 46,483.47 | 41,019.57 | 1.2% | 2.7% |
| Mental Health | 2019 | 8,973 | 13.7% | 27,234.54 | 29,088.00 | n/a | n/a |
| Mental Health | 2020 | 8,540 | 13.8% | 32,325.99 | 33,631.91 | -4.8% | 18.7% |
| Mental Health | 2021 | 8,287 | 13.5% | 31,988.43 | 33,434.26 | -3.0% | -1.0% |
| Mental Health | 2022 | 8,474 | 13.8% | 30,928.35 | 32,582.17 | 2.3% | -3.3% |
| Mental Health | 2023 | 9,079 | 14.3% | 35,703.60 | 37,484.04 | 7.1% | 15.4% |
| Mental Health | 2024 | 9,201 | 14.4% | 39,496.37 | 41,282.67 | 1.3% | 10.6% |
| Mental Health | 2025 | 8,986 | 13.8% | 42,080.49 | 44,057.71 | -2.3% | 6.5% |
| Social Services | 2019 | 7,823 | 11.9% | 32,243.01 | 30,295.79 | n/a | n/a |
| Social Services | 2020 | 7,462 | 12.0% | 33,710.84 | 32,768.78 | -4.6% | 4.6% |
| Social Services | 2021 | 7,468 | 12.1% | 32,544.62 | 31,359.15 | 0.1% | -3.5% |
| Social Services | 2022 | 7,622 | 12.4% | 34,262.73 | 32,251.81 | 2.1% | 5.3% |
| Social Services | 2023 | 7,881 | 12.4% | 37,225.73 | 36,603.74 | 3.4% | 8.6% |
| Social Services | 2024 | 7,928 | 12.4% | 39,658.35 | 39,967.97 | 0.6% | 6.5% |
| Social Services | 2025 | 7,895 | 12.1% | 40,983.28 | 41,120.46 | -0.4% | 3.3% |
| Transportation | 2019 | 6,478 | 9.9% | 37,687.38 | 36,046.51 | n/a | n/a |
| Transportation | 2020 | 6,138 | 9.9% | 37,310.79 | 37,016.20 | -5.2% | -1.0% |
| Transportation | 2021 | 6,108 | 9.9% | 39,301.90 | 38,090.67 | -0.5% | 5.3% |
| Transportation | 2022 | 5,864 | 9.5% | 42,938.18 | 41,773.36 | -4.0% | 9.3% |
| Transportation | 2023 | 5,892 | 9.3% | 46,879.13 | 45,541.37 | 0.5% | 9.2% |
| Transportation | 2024 | 6,092 | 9.5% | 48,426.25 | 47,516.45 | 3.4% | 3.3% |
| Transportation | 2025 | 6,306 | 9.7% | 49,950.83 | 48,641.21 | 3.5% | 3.1% |
| Public Safety | 2019 | 6,704 | 10.2% | 31,777.17 | 34,639.24 | n/a | n/a |
| Public Safety | 2020 | 7,641 | 12.3% | 31,301.90 | 31,718.43 | 14.0% | -1.5% |
| Public Safety | 2021 | 6,487 | 10.5% | 34,296.00 | 36,237.25 | -15.1% | 9.6% |
| Public Safety | 2022 | 6,467 | 10.5% | 36,135.84 | 37,588.27 | -0.3% | 5.4% |
| Public Safety | 2023 | 5,883 | 9.3% | 39,974.31 | 43,199.40 | -9.0% | 10.6% |
| Public Safety | 2024 | 5,585 | 8.7% | 44,312.28 | 48,774.66 | -5.1% | 10.9% |
| Public Safety | 2025 | 5,635 | 8.7% | 47,454.36 | 53,574.80 | 0.9% | 7.1% |

In 2025, 3,311 department and job title cells exist. Suppression hides 2,061 cells, which hold 3,564 people, and leaves 1,250 cells visible. Department-year cells with fewer than 5 people number 0.

The next table places row-level figures beside person-level figures. Rows exceed people because a person changing title within a year receives one row per title.

| Year | Rows | People | Row-level median ($) | Person-level median ($) |
| --- | --- | --- | --- | --- |
| 2019 | 75,173 | 65,691 | 27,598.91 | 32,327.93 |
| 2020 | 99,663 | 62,030 | 18,917.20 | 35,783.71 |
| 2021 | 70,436 | 61,580 | 29,800.43 | 35,157.08 |
| 2022 | 70,786 | 61,562 | 31,277.09 | 36,510.07 |
| 2023 | 72,431 | 63,510 | 35,158.26 | 40,307.07 |
| 2024 | 72,805 | 64,050 | 38,038.61 | 43,084.74 |
| 2025 | 73,681 | 65,069 | 39,066.23 | 44,452.24 |

## Limitations of pay data as a headcount proxy

Headcount here counts people paid at any point in the year, so it is not a point-in-time count of filled positions and it cannot be compared directly with such counts. The files have no hire date, separation date, FTE or hours, so part-year and part-time work cannot be identified. Those people lower median and mean pay. In 2025, 16.2% of people received less than $10,000.

A person with several titles has several rows, and 8,010 people had two or more rows in 2025. The person-level calculation removes this effect for pay and headcount, and the job title shown is the title with the most pay. Pay reported for a title therefore includes pay earned under the person's other titles that year.

Names identify people imperfectly. Two employees with the same name in one department merge into one person and lower headcount. A person paid by two departments counts once in each and raises statewide headcount, and 1,319 names appeared in two or more departments in 2025. Those names include different people who share a name, and the two cases cannot be separated.

Gross pay is not base salary. It includes all pay received, so these figures do not describe salary schedules and a change in median pay can reflect changes in the mix of staff, in overtime, in part-year work or in pay rates.

National Guard first appears in calendar year 2023 with 551 people. Statewide headcount rose 3.2% in 2023, and the rise excluding National Guard is 2.3%. The files do not state why the department was added.
