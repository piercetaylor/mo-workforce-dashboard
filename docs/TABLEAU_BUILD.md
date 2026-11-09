# Tableau build sheet

This sheet builds the dashboard in Tableau Desktop Public Edition. The sections are budgeted at 120 minutes in total. Run `make clean` and `make extract` first so that `data/extract/mo_workforce.csv` exists. Public Edition connects to the CSV because Tableau's technical specifications do not list Tableau extracts among its data sources.

All pay fields use `person_annual_pay`. The data source filter in step 3 leaves one row per person, and `annual_pay` is used only for reconciling totals outside Tableau.

## 1. Connect and set types (15 minutes)

1. Open Tableau Desktop Public Edition. Under Connect, choose Text file and open `data/extract/mo_workforce.csv`.
2. On the Data Source page, set these types with the icon above each column.

   | Field | Type |
   | --- | --- |
   | `calendar_year` | Number (whole) |
   | `department` | String |
   | `job_title` | String |
   | `annual_pay` | Number (decimal) |
   | `person_key` | String |
   | `person_annual_pay` | Number (decimal) |
   | `is_primary_row` | Number (whole) |
   | `source_row_id` | String |

3. At the top right of the Data Source page, click Add under Filters, then Add, and select `is_primary_row`. If asked how to filter the field, choose All values, then set the range from 1 to 1. This filter applies before FIXED calculations, so the statewide median also uses one row per person.
4. Go to a new sheet. In the Data pane, right-click `calendar_year` and choose Convert to Dimension. Right-click it again and choose Convert to Discrete.
5. In the Data pane, drag `job_title` onto `department` and name the hierarchy `Department Hierarchy`. The order is `department`, then `job_title`.

## 2. Parameter and calculated fields (20 minutes)

Create a parameter named `Calendar Year Parameter`. Set the data type to Integer, set Allowable values to List, and click Add values from > `calendar_year`. Set the current value to the latest year. Set the display format to Number (Custom) with 0 decimals and no thousands separator.

Create each calculated field below with the exact name shown.

`Headcount`

```
COUNTD([person_key])
```

`Median Pay`

```
MEDIAN([person_annual_pay])
```

`Mean Pay`

```
AVG([person_annual_pay])
```

`Headcount YoY`

```
(ZN([Headcount]) - LOOKUP(ZN([Headcount]), -1)) / ABS(LOOKUP(ZN([Headcount]), -1))
```

`Median Pay YoY`

```
(ZN([Median Pay]) - LOOKUP(ZN([Median Pay]), -1)) / ABS(LOOKUP(ZN([Median Pay]), -1))
```

Both YoY fields are table calculations and must compute along `calendar_year`. They return NULL for the first year.

`Statewide Median`

```
{ FIXED [calendar_year] : MEDIAN([person_annual_pay]) }
```

`Statewide Headcount`

```
{ FIXED [calendar_year] : COUNTD([person_key]) }
```

`Share of Statewide`

```
[Headcount] / MIN([Statewide Headcount])
```

`Suppressed Headcount`

```
IF [Headcount] >= 5 THEN [Headcount] END
```

`Suppressed Median`

```
IF [Headcount] >= 5 THEN [Median Pay] END
```

`Suppressed Mean`

```
IF [Headcount] >= 5 THEN [Mean Pay] END
```

`Show Cell`

```
[Headcount] >= 5
```

`Selected Year`

```
[calendar_year] = [Calendar Year Parameter]
```

Format `Share of Statewide`, `Headcount YoY` and `Median Pay YoY` as percentages with 1 decimal. Format the pay fields as currency with 0 decimals.

## 3. Sheets (45 minutes)

Sheet `Statewide Trend` shows every year, so it does not use `Selected Year`.

1. Put `calendar_year` on Columns. Put `Median Pay` and `Headcount` on Rows, and set the mark type to Line.
2. Add `Median Pay YoY` and `Headcount YoY` to Tooltip. Right-click each, choose Compute Using, and select `calendar_year`.
3. A filter on the year would remove the prior year that `LOOKUP` reads, so leave this sheet unfiltered.

Sheet `Department Median`

1. Put `Selected Year` on Filters and keep True.
2. Put `department` on Rows and `Suppressed Median` on Columns.
3. Sort `department` descending by `Suppressed Median`.
4. Put `Statewide Median` on Detail and set its aggregation to Minimum.
5. Open the Analytics pane and drag Reference Line to Table. Set Value to `MIN(Statewide Median)` and set Label to Custom with the text `Statewide median`.
6. Add `Suppressed Headcount` to Tooltip.

Sheet `Job Title Table`

1. Put `Selected Year` on Filters and keep True.
2. Put `Show Cell` on Filters and keep True. This removes rows with fewer than five people.
3. Put `Department Hierarchy` on Rows and expand it to show `job_title`.
4. Double-click `Suppressed Headcount`, `Suppressed Median` and `Suppressed Mean` so that all three appear as Measure Values.
5. Sort `job_title` descending by `Suppressed Headcount`.

Sheet `Department Share`

1. Put `Selected Year` on Filters and keep True.
2. Set the mark type to Square for a treemap.
3. Put `Headcount` on Size and `Share of Statewide` on Color.
4. Put `department` and `Share of Statewide` on Label.

## 4. Dashboard (25 minutes)

1. Create a dashboard named `Missouri State Workforce Pay`. Set Size to Fixed at 1200 by 900.
2. Place `Statewide Trend` across the top, `Department Median` at left, and `Job Title Table` at right. Place `Department Share` below `Department Median`.
3. Show the year control. Click a sheet, open its More Options menu, and choose Parameters > `Calendar Year Parameter`. Title the control `Calendar year`.
4. Choose Dashboard > Actions > Add Action > Filter. Name it `Department to Job Title`. Set Source Sheets to `Department Median`, Run action on to Select, Target Sheets to `Job Title Table`, Clearing the selection to Show all values, and Target Filters to Selected Fields with `department` to `department`.
5. Add a Text object at the bottom with the three paragraphs below. Replace the retrieval date with the value in `data/SOURCES.md`. Paste the notice from `data/ref/mo_data_policy_disclaimer.txt` unchanged, because the State Data Policy requires it.

   Source paragraph:

   > Source: State Employee Pay, Office of Administration, State of Missouri, data.mo.gov. Retrieved [date]. Years shown are calendar years.

   Definitions paragraph:

   > Headcount counts people paid at any point in the year, identified by name within a department, so it is not a count of filled positions. Pay is gross pay for the calendar year, summed for each person, and includes all pay received; it is not base salary. Part-year and part-time work lower the median and mean. Groups with fewer than five people are hidden.

   Notice paragraph: the full text of `data/ref/mo_data_policy_disclaimer.txt`.

## 5. Verify and publish (15 minutes)

Compare the dashboard with `docs/DEFINITIONS.md` before publishing.

- [ ] Statewide headcount, median and mean match the statewide table for the latest year.
- [ ] The statewide trend matches the statewide table for every year, including both YoY columns.
- [ ] Headcount, share, median and mean for the five largest departments match the department table for the latest year.
- [ ] The reference line equals the statewide median and does not move when a department is selected.
- [ ] Selecting a department filters only `Job Title Table`.
- [ ] Changing the year updates the three year-filtered sheets and leaves `Statewide Trend` unchanged.
- [ ] `Job Title Table` shows no row with fewer than five people.
- [ ] The text box holds the source, retrieval date, definitions paragraph and the full required notice.
- [ ] Every label reads calendar year, and no label says fiscal year.

Publish with Server > Tableau Public > Save to Tableau Public.

Use this title: `Missouri State Workforce Pay, Calendar Years 2019-2025`.

Use this description: `Headcount and gross pay by department and job title, built from the State Employee Pay files published by the Missouri Office of Administration on data.mo.gov. Headcount counts people paid during a calendar year. Pay is gross pay and is not base salary. Groups with fewer than five people are hidden.`

After publishing, open the viz on Tableau Public, select the Settings icon in the toolbar, and under Allow Access turn off `Let others download or make a copy of this viz`. Tableau Public allows downloads by default, and a downloaded workbook contains the rows that the dashboard hides. Tableau's FAQ notes that this setting also controls the View Data table used by assistive technologies, so the text box definitions carry the description for those users.
