# Exclusions

`scripts/clean.py` writes this file and produces every number in it. The analysis covers calendar years 2019 to 2025. Each raw row receives at most one exclusion reason, assigned in the order listed below. Pay is the raw `ytd_gross_pay`, summed in integer cents.

| Reason | Rule | Rows | Pay ($) |
| --- | --- | --- | --- |
| `blank_department` | The agency field is empty. | 1 | 334.38 |
| `zero_pay` | Gross pay equals zero. | 0 | 0.00 |
| `negative_pay` | Gross pay is below zero. | 561 | -162,892.75 |
| `duplicate` | All five raw fields repeat an earlier row and the name is not masked. | 0 | 0.00 |
| `non_employee_payee` | No rule applies, because the files have no payee-type field. | 0 | 0.00 |

## Reconciliation

Clean pay equals raw pay minus excluded pay in every year, and `scripts/clean.py` stops if it does not. Excluded pay is negative because the excluded rows with nonzero pay are almost all negative amounts, so clean pay exceeds raw pay.

| Year | Raw rows | Blank department | Zero pay | Negative pay | Duplicate | Non-employee | Clean rows | Raw pay ($) | Excluded pay ($) | Clean pay ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 75,233 | 0 | 0 | 60 | 0 | 0 | 75,173 | 2,119,561,409.05 | -14,976.59 | 2,119,576,385.64 |
| 2020 | 99,728 | 0 | 0 | 65 | 0 | 0 | 99,663 | 2,197,839,369.55 | -14,224.24 | 2,197,853,593.79 |
| 2021 | 70,535 | 0 | 0 | 99 | 0 | 0 | 70,436 | 2,160,391,753.17 | -29,331.54 | 2,160,421,084.71 |
| 2022 | 70,901 | 0 | 0 | 115 | 0 | 0 | 70,786 | 2,254,235,635.55 | -21,548.19 | 2,254,257,183.74 |
| 2023 | 72,528 | 1 | 0 | 96 | 0 | 0 | 72,431 | 2,575,004,104.63 | -21,926.09 | 2,575,026,030.72 |
| 2024 | 72,868 | 0 | 0 | 63 | 0 | 0 | 72,805 | 2,779,979,361.15 | -11,347.89 | 2,779,990,709.04 |
| 2025 | 73,744 | 0 | 0 | 63 | 0 | 0 | 73,681 | 2,918,769,710.58 | -49,203.83 | 2,918,818,914.41 |
| TOTAL | 535,537 | 1 | 0 | 561 | 0 | 0 | 534,975 | 17,005,781,343.68 | -162,558.37 | 17,005,943,902.05 |

## Rows reviewed and retained

Rows whose employee name begins with `PROTECTED` carry a masked name. They were retained, 432 rows in all, and each counts as one person. 9 of them repeat an earlier row in all five fields. Those repeats were retained because masked rows with the same title and pay may be different people.

The files have no field identifying a non-employee payee, so no row was excluded under that reason. The titles BOARD MEMBER, COMMISSION MEMBER, COMMISSION MEMBERS were reviewed as likely stipend payees. They account for 1,428 retained rows and $13,983,794.63. Their median row pay is BOARD MEMBER $425.00; COMMISSION MEMBER $2,500.00; COMMISSION MEMBERS $1,438.08, and the largest row is $142,840.39. Title alone does not separate stipend members from salaried members, so these rows stay in the data and the under-5 suppression rule governs small cells.

10 retained rows have pay of at least $500,000.00, and the largest is $1,778,605.91. These amounts were retained because the files offer no basis for treating them as errors.

Whitespace was collapsed in 128 position titles and 58 employee names. No other change was made to titles. Spelling variants are listed in `data/clean/title_variants.csv` and are left unmerged in the clean files.
