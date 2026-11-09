# Data sources

`scripts/fetch.py` writes this file and produces every number in it. Files were retrieved on 2026-11-09. `data/manifest.csv` records the URL, row count, size and SHA-256 hash of each downloaded file.

## Selected source

The State of Missouri publishes one State Employee Pay dataset per calendar year on data.mo.gov. Each dataset names Office of Administration as its attribution. The 19 datasets cover calendar years 2007 to 2025 and hold 1,472,414 rows in total. Every file has the same five fields: `calendar_year`, `agency_name`, `position_title`, `employee_name`, `ytd_gross_pay`. The CSV row count of each file equals the row count returned by the Socrata API.

| Calendar year | Dataset | Rows | MB | Data last updated |
| --- | --- | --- | --- | --- |
| 2007 | [gapb-jve5](https://data.mo.gov/d/gapb-jve5) | 87,805 | 6.2 | 2024-09-26 |
| 2008 | [uccy-42en](https://data.mo.gov/d/uccy-42en) | 87,080 | 6.2 | 2024-09-26 |
| 2009 | [j82q-875v](https://data.mo.gov/d/j82q-875v) | 78,601 | 5.6 | 2024-05-06 |
| 2010 | [8ama-dpbv](https://data.mo.gov/d/8ama-dpbv) | 73,606 | 5.3 | 2024-09-26 |
| 2011 | [hj93-xter](https://data.mo.gov/d/hj93-xter) | 78,988 | 5.7 | 2024-09-26 |
| 2012 | [32yd-5xay](https://data.mo.gov/d/32yd-5xay) | 73,930 | 5.3 | 2024-09-26 |
| 2013 | [a6nm-4wbm](https://data.mo.gov/d/a6nm-4wbm) | 73,650 | 5.3 | 2024-09-26 |
| 2014 | [i6tz-nkqw](https://data.mo.gov/d/i6tz-nkqw) | 75,990 | 5.4 | 2024-05-06 |
| 2015 | [8yf2-bu4d](https://data.mo.gov/d/8yf2-bu4d) | 74,596 | 5.3 | 2024-09-26 |
| 2016 | [qy64-qzrf](https://data.mo.gov/d/qy64-qzrf) | 77,414 | 5.5 | 2024-09-26 |
| 2017 | [mesr-3mki](https://data.mo.gov/d/mesr-3mki) | 76,826 | 5.5 | 2024-09-26 |
| 2018 | [g8g2-6fyn](https://data.mo.gov/d/g8g2-6fyn) | 78,391 | 5.6 | 2024-09-26 |
| 2019 | [wnyf-5ce9](https://data.mo.gov/d/wnyf-5ce9) | 75,233 | 5.4 | 2024-09-26 |
| 2020 | [53ys-svak](https://data.mo.gov/d/53ys-svak) | 99,728 | 7.2 | 2024-09-26 |
| 2021 | [7j8x-y8ki](https://data.mo.gov/d/7j8x-y8ki) | 70,535 | 5.1 | 2024-09-26 |
| 2022 | [7m33-xh7t](https://data.mo.gov/d/7m33-xh7t) | 70,901 | 5.2 | 2024-09-26 |
| 2023 | [d5qn-3gs9](https://data.mo.gov/d/d5qn-3gs9) | 72,528 | 5.3 | 2024-09-26 |
| 2024 | [nkgr-ek2r](https://data.mo.gov/d/nkgr-ek2r) | 72,868 | 5.3 | 2025-01-02 |
| 2025 | [przm-8aj2](https://data.mo.gov/d/przm-8aj2) | 73,744 | 5.4 | 2026-01-05 |

The files report calendar years. Fiscal-year pay cannot be derived because each row carries one year-to-date amount with no pay dates. The Accountability Portal states that gross pay includes all pay received and is not base salary. The files contain no division, pay type, FTE, hours or employee identifier field.

## Terms of use

The license field in the portal metadata is empty for 19 of 19 datasets, and no license is therefore claimed here. The data.mo.gov footer links to the State Data Policy (https://mo.gov/data-policy). The policy contains no prohibition on reuse. It disclaims warranties, requires applications using the data to display the notice below, and reserves the right of the State to require that display or use of the data end. The notice is stored in `data/ref/mo_data_policy_disclaimer.txt` and must appear on the dashboard.

> The data made available here has been modified for use from its original source, which is the State of Missouri. THE STATE OF MISSOURI MAKES NO REPRESENTATIONS OR WARRANTY AS TO THE COMPLETENESS, ACCURACY, TIMELINESS, OR CONTENT OF ANY DATA MADE AVAILABLE THROUGH THIS SITE. THE STATE OF MISSOURI EXPRESSLY DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS OR IMPLIED, INCLUDING ANY IMPLIED WARRANTIES OF MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE. The data is subject to change as modifications and updates are complete. It is understood that the information contained in the Web feed is being used at one’s own risk.

## Candidates reviewed

| Candidate | URL | Fields | Rows | Years | Terms | Retrieved | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| State Employee Pay | https://data.mo.gov/d/przm-8aj2 (one dataset per year) | calendar_year, agency_name, position_title, employee_name, ytd_gross_pay | 1,472,414 over 19 files | Calendar 2007-2025 | No license stated; State Data Policy applies | 2026-11-09 | Selected |
| Missouri Accountability Portal employee files | https://mapyourtaxes.mo.gov/MAP/Download/Default.aspx | Calendar Year, Agency Name, Position Title, Employee Name, YTD Gross Pay | 68,926 in the 2026 file; earlier files not downloaded | Calendar 2007-2026; 2026 runs through the October 30, 2026 pay date | Portal disclaimer text could not be read; coverage by the Data Policy is unconfirmed | 2026-11-09 | Not used; same schema and years, and 2026 is a partial year |
| Office of Administration annual reports | https://oa.mo.gov/sites/default/files/AnnualReport2017.pdf https://oa.mo.gov/sites/default/files/AnnualReport2018.pdf | PDF report tables | Not row-level | 2017 and 2018 reports located | Not reviewed | 2026-11-09 | Not used; HTTP 200 confirmed, and no bulk pay file was located on this site |
| Workforce Characteristics 2016 | https://data.mo.gov/d/gvbf-hkku | County workforce demographics | 116 | 2016 | Attributed to U.S. Census Bureau | 2026-11-09 | Not used; contains no state employee pay |

Pre-2026 Accountability Portal employee files are described on the download page as zipped executables, and they were not downloaded or run. The contents of the Office of Administration reports were taken from web search summaries, and the PDFs were not parsed.

## Observations in the raw files

The table precedes all exclusions. A person unit is one distinct (agency, employee name) pair within a year, plus one unit for each protected row. The dataset has no employee identifier, so two people with the same name in one agency merge into one unit. A person working in two agencies counts as two units. Unit median is the median of pay summed to the person unit.

| Year | Rows | Total pay ($) | Zero | Negative | Negative ($) | Exact duplicates (protected) | Protected | Blank agency | Stipend titles | Stipend ($) | Person units | Units with 2+ rows | Row median ($) | Unit median ($) | Maximum ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2007 | 87,805 | 2,028,345,470.12 | 0 | 34 | -2,585.66 | 1 (1) | 57 | 0 | 428 | 1,743,655.47 | 74,773 | 11,907 | 23,172.56 | 27,541.16 | 1,217,030.74 |
| 2008 | 87,080 | 2,112,021,252.36 | 0 | 26 | -4,065.58 | 4 (2) | 58 | 0 | 264 | 1,817,147.61 | 74,882 | 11,196 | 24,186.00 | 28,550.46 | 1,186,644.74 |
| 2009 | 78,601 | 2,129,875,701.43 | 0 | 15 | -1,798.12 | 3 (2) | 65 | 0 | 267 | 1,678,922.36 | 70,408 | 7,748 | 27,878.65 | 29,726.29 | 1,126,064.27 |
| 2010 | 73,606 | 2,055,989,671.64 | 0 | 17 | -3,792.42 | 4 (3) | 63 | 0 | 238 | 1,623,887.25 | 66,914 | 6,227 | 28,486.59 | 29,923.14 | 1,122,495.27 |
| 2011 | 78,988 | 2,008,285,550.95 | 0 | 31 | -4,615.57 | 3 (3) | 74 | 0 | 238 | 1,668,439.61 | 68,872 | 9,203 | 26,196.00 | 29,341.86 | 963,954.17 |
| 2012 | 73,930 | 1,985,532,963.99 | 0 | 36 | -9,680.33 | 1 (1) | 60 | 0 | 243 | 1,592,819.37 | 66,473 | 6,954 | 27,134.07 | 29,718.71 | 989,888.30 |
| 2013 | 73,650 | 1,994,671,388.61 | 0 | 24 | -3,404.99 | 0 (0) | 68 | 0 | 228 | 1,879,086.98 | 66,740 | 6,551 | 27,432.00 | 29,799.85 | 970,558.82 |
| 2014 | 75,990 | 2,039,290,414.69 | 0 | 41 | -8,461.54 | 1 (0) | 61 | 0 | 224 | 1,674,747.10 | 68,792 | 6,830 | 27,054.85 | 30,120.02 | 982,104.56 |
| 2015 | 74,596 | 2,051,356,022.30 | 0 | 42 | -9,435.27 | 1 (1) | 66 | 0 | 235 | 1,805,489.58 | 66,635 | 7,466 | 27,648.50 | 30,807.00 | 1,074,875.53 |
| 2016 | 77,414 | 2,068,905,358.30 | 0 | 57 | -5,613.14 | 1 (1) | 63 | 0 | 238 | 1,914,539.32 | 66,753 | 9,905 | 26,402.00 | 31,103.25 | 1,075,660.80 |
| 2017 | 76,826 | 2,089,318,257.10 | 0 | 67 | -9,775.52 | 3 (1) | 59 | 0 | 218 | 1,781,079.92 | 68,135 | 8,127 | 27,180.00 | 31,187.16 | 1,029,830.20 |
| 2018 | 78,391 | 2,083,232,543.01 | 0 | 51 | -14,231.96 | 2 (2) | 69 | 0 | 232 | 1,787,600.36 | 65,219 | 12,241 | 25,527.92 | 32,063.44 | 1,054,144.88 |
| 2019 | 75,233 | 2,119,561,409.05 | 0 | 60 | -14,976.59 | 0 (0) | 64 | 0 | 222 | 1,756,871.26 | 65,700 | 8,916 | 27,566.34 | 32,321.85 | 1,130,393.05 |
| 2020 | 99,728 | 2,197,839,369.55 | 0 | 65 | -14,224.24 | 3 (3) | 63 | 0 | 205 | 1,808,328.80 | 62,041 | 33,673 | 18,913.35 | 35,779.45 | 902,160.27 |
| 2021 | 70,535 | 2,160,391,753.17 | 0 | 99 | -29,331.54 | 1 (1) | 61 | 0 | 205 | 1,908,134.79 | 61,592 | 8,241 | 29,757.48 | 35,152.35 | 982,768.70 |
| 2022 | 70,901 | 2,254,235,635.55 | 0 | 115 | -21,548.19 | 0 (0) | 62 | 0 | 208 | 2,098,311.93 | 61,588 | 8,491 | 31,216.10 | 36,502.00 | 1,196,699.90 |
| 2023 | 72,528 | 2,575,004,104.63 | 0 | 96 | -22,260.47 | 1 (1) | 57 | 1 | 207 | 1,967,697.27 | 63,528 | 8,353 | 35,111.43 | 40,296.22 | 1,408,418.29 |
| 2024 | 72,868 | 2,779,979,361.15 | 0 | 63 | -11,347.89 | 3 (3) | 60 | 0 | 198 | 2,237,622.62 | 64,065 | 8,054 | 38,018.09 | 43,078.26 | 1,537,077.17 |
| 2025 | 73,744 | 2,918,769,710.58 | 0 | 63 | -49,203.83 | 1 (1) | 65 | 0 | 183 | 2,206,827.96 | 65,077 | 8,058 | 39,066.23 | 44,443.11 | 1,778,605.91 |

The 2020 file holds 99,728 rows, and 33,673 person units have two or more rows. Other years have between 6,227 and 12,241 such units. The row-level median in 2020 is $18,913.35, while the unit median is $35,779.45. The title pairs below are the most frequent among 2020 units holding exactly two titles. The pattern is consistent with a mid-year change of job classifications that split pay across an old and a new title. The cause is inferred from these pairs, because no State document describing it was located.

| Title A | Title B | Person units |
| --- | --- | --- |
| CORRECTIONAL OFFICER | CORRECTIONS OFCR I | 3,423 |
| BENEFIT PROGRAM TECHNICIAN | FAMILY SUPPORT ELIGIBILITY SPC | 1,135 |
| DEVELOPMENTAL ASST I | SUPPORT CARE ASSISTANT | 1,038 |
| PROBATION & PAROLE OFCR II | PROBATION AND PAROLE OFFICER | 955 |
| ADMINISTRATIVE SUPPORT CLERK | OFFICE SUPPORT ASSISTANT | 762 |

Rows whose employee name begins with `PROTECTED` carry a masked name and cannot be resolved to a person. Exact duplicate rows among protected names may be distinct people with identical pay. The titles BOARD MEMBER, COMMISSION MEMBER, COMMISSION MEMBERS are counted as stipend titles. Agencies absent from the first year and present later are: NATIONAL GUARD (first in 2023).
