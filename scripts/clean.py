"""Build tidy yearly pay files, the department crosswalk, the exclusion log and title variants."""
import difflib
import hashlib
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
REF = ROOT / "data" / "ref"
YEARS = list(range(2019, 2026))
PROTECTED = "PROTECTED"
STIPEND_TITLES = ["BOARD MEMBER", "COMMISSION MEMBER", "COMMISSION MEMBERS"]
HIGH_PAY_CENTS = 50_000_000
RAW_COLS = ["calendar_year", "raw_department", "raw_title", "raw_name", "raw_pay"]
COLUMNS = ["calendar_year", "department", "job_title", "annual_pay", "person_key", "person_annual_pay",
           "is_primary_row", "source_row_id"]
REASONS = {"blank_department": "The agency field is empty.",
           "zero_pay": "Gross pay equals zero.",
           "negative_pay": "Gross pay is below zero.",
           "duplicate": "All five raw fields repeat an earlier row and the name is not masked.",
           "non_employee_payee": "No rule applies, because the files have no payee-type field."}
EXPANDED = {"HIGHER EDUCATION AND WORKFORCE DEV": "Higher Education and Workforce Development"}
SIMILARITY = 0.86
GRADE = re.compile(r"\b(?:I{1,3}|IV|VI?|[1-9]|SR|JR|LEAD)\b")


def money(cents):
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) // 100:,}.{abs(cents) % 100:02d}"


def plain(cents):
    return money(cents).replace(",", "")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def squeeze(series):
    return series.str.replace(r"\s+", " ", regex=True).str.strip()


def load(year):
    """Read one raw year. Sorting first makes row ids independent of portal row order."""
    df = pd.read_csv(RAW / f"{year}.csv", dtype=str, keep_default_na=False)
    df.columns = RAW_COLS
    df = df.sort_values(RAW_COLS, kind="mergesort").reset_index(drop=True)
    df["source_row_id"] = [f"CY{year}-{i:06d}" for i in range(1, len(df) + 1)]
    df["job_title"] = squeeze(df["raw_title"])
    df["name"] = squeeze(df["raw_name"])
    df["cents"] = (df["raw_pay"].astype(float) * 100).round().astype("int64")
    df["protected"] = df["name"].str.startswith(PROTECTED)
    return df


def canonical(raw):
    if raw in EXPANDED:
        return EXPANDED[raw], "Case normalized; abbreviation DEV expanded to Development."
    words = [w.lower() if w in ("AND", "OF") else w.capitalize() for w in raw.split()]
    return " ".join(words), "Case normalized."


def build_xwalk(frames):
    all_rows = pd.concat(frames.values())
    all_rows = all_rows[all_rows["raw_department"].str.strip() != ""]
    summary = all_rows.groupby("raw_department")["calendar_year"].agg(rows="size", first_year="min", last_year="max").reset_index()
    pairs = summary["raw_department"].map(canonical)
    summary["canonical_department"] = pairs.str[0]
    summary["decision"] = pairs.str[1]
    summary = summary.sort_values("canonical_department").reset_index(drop=True)
    summary["department_code"] = [f"D{i:02d}" for i in range(1, len(summary) + 1)]
    return summary[["raw_department", "canonical_department", "department_code", "decision", "rows", "first_year", "last_year"]]


def exclusion_reason(df):
    """Assign one reason per row. Masks are applied in reverse so earlier reasons win."""
    masks = {"blank_department": df["raw_department"].str.strip() == "",
             "zero_pay": df["cents"] == 0,
             "negative_pay": df["cents"] < 0,
             "duplicate": df.duplicated(RAW_COLS) & ~df["protected"]}
    reason = pd.Series("", index=df.index)
    for name in reversed(list(masks)):
        reason[masks[name]] = name
    return reason


def add_person_fields(df):
    """Add the person key, pay summed to the person, and one primary row per person."""
    df = df.copy()
    df["person_key"] = ["X" + sha(r) if p else "P" + sha(f"{d}|{n}")
                        for r, p, d, n in zip(df["source_row_id"], df["protected"], df["department"], df["name"])]
    df["person_cents"] = df.groupby("person_key")["cents"].transform("sum")
    ranked = df.sort_values(["person_key", "cents", "source_row_id"], ascending=[True, False, True])
    df["is_primary_row"] = (~ranked.duplicated("person_key")).reindex(df.index).astype(int)
    return df


def write_year(year, df):
    out = df.assign(annual_pay=df["cents"].map(plain), person_annual_pay=df["person_cents"].map(plain))
    out[COLUMNS].to_csv(CLEAN / f"pay_CY{year % 100:02d}.csv", index=False, lineterminator="\n")


def reconcile(year, df, reason):
    row = {"calendar_year": year, "raw_rows": len(df)}
    for name in REASONS:
        row[f"{name}_rows"] = int((reason == name).sum())
        row[f"{name}_cents"] = int(df.loc[reason == name, "cents"].sum())
    row["excluded_rows"] = int((reason != "").sum())
    row["clean_rows"] = int((reason == "").sum())
    row["raw_cents"] = int(df["cents"].sum())
    row["excluded_cents"] = int(df.loc[reason != "", "cents"].sum())
    row["clean_cents"] = int(df.loc[reason == "", "cents"].sum())
    return row


def add_total(rows):
    total = {k: sum(r[k] for r in rows) for k in rows[0] if k != "calendar_year"}
    return rows + [{"calendar_year": "TOTAL", **total}]


def title_variants(kept):
    """Pair each single-year title with its closest multi-year title at the same grade."""
    grades = lambda t: GRADE.findall(t.replace("SENIOR", "SR"))
    years = kept.groupby("job_title")["calendar_year"].agg(["nunique", "min", "max"])
    counts = kept["job_title"].value_counts()
    people = kept.groupby("job_title")["person_key"].agg(set)
    multi = years.index[years["nunique"] > 1].tolist()
    out = []
    for title in years.index[years["nunique"] == 1]:
        match = next((m for m in difflib.get_close_matches(title, multi, n=5, cutoff=SIMILARITY) if grades(m) == grades(title)), None)
        if match:
            out.append({"job_title": title, "only_year": years.loc[title, "min"], "rows": counts[title], "closest_title": match,
                        "closest_title_first_year": years.loc[match, "min"], "closest_title_last_year": years.loc[match, "max"],
                        "closest_title_rows": counts[match],
                        "similarity": round(difflib.SequenceMatcher(None, title, match).ratio(), 3),
                        "shared_people": len(people[title] & people[match])})
    return pd.DataFrame(out).sort_values(["shared_people", "similarity"], ascending=False)


def retained_stats(frames, reasons):
    rows = pd.concat(frames[y][reasons[y] == ""] for y in YEARS)
    stipend = rows[rows["job_title"].isin(STIPEND_TITLES)]
    medians = stipend.groupby("job_title")["cents"].median()
    duplicates = pd.concat(frames[y][frames[y].duplicated(RAW_COLS) & frames[y]["protected"]] for y in YEARS)
    whole = pd.concat(frames.values())
    return {"protected": int(rows["protected"].sum()), "protected_dups": len(duplicates), "stipend_rows": len(stipend),
            "stipend_cents": int(stipend["cents"].sum()), "stipend_max": int(stipend["cents"].max()),
            "stipend_medians": "; ".join(f"{t} ${money(int(c))}" for t, c in medians.items()),
            "high": int((rows["cents"] >= HIGH_PAY_CENTS).sum()), "max": int(rows["cents"].max()),
            "title_ws": int((whole["raw_title"] != whole["job_title"]).sum()),
            "name_ws": int((whole["raw_name"] != whole["name"]).sum())}


def write_exclusions(recon, stats):
    total = recon[-1]
    reasons = "\n".join(f"| `{k}` | {v} | {total[k + '_rows']:,} | {money(total[k + '_cents'])} |" for k, v in REASONS.items())
    by_year = "\n".join(f"| {r['calendar_year']} | {r['raw_rows']:,} | " + " | ".join(f"{r[k + '_rows']:,}" for k in REASONS)
                        + f" | {r['clean_rows']:,} | {money(r['raw_cents'])} | {money(r['excluded_cents'])} | {money(r['clean_cents'])} |" for r in recon)
    (CLEAN / "EXCLUSIONS.md").write_text(f"""# Exclusions

`scripts/clean.py` writes this file and produces every number in it. The analysis covers calendar years {YEARS[0]} to {YEARS[-1]}. Each raw row receives at most one exclusion reason, assigned in the order listed below. Pay is the raw `ytd_gross_pay`, summed in integer cents.

| Reason | Rule | Rows | Pay ($) |
| --- | --- | --- | --- |
{reasons}

## Reconciliation

Clean pay equals raw pay minus excluded pay in every year, and `scripts/clean.py` stops if it does not. Excluded pay is negative because the excluded rows with nonzero pay are almost all negative amounts, so clean pay exceeds raw pay.

| Year | Raw rows | Blank department | Zero pay | Negative pay | Duplicate | Non-employee | Clean rows | Raw pay ($) | Excluded pay ($) | Clean pay ($) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{by_year}

## Rows reviewed and retained

Rows whose employee name begins with `{PROTECTED}` carry a masked name. They were retained, {stats["protected"]:,} rows in all, and each counts as one person. {stats["protected_dups"]} of them repeat an earlier row in all five fields. Those repeats were retained because masked rows with the same title and pay may be different people.

The files have no field identifying a non-employee payee, so no row was excluded under that reason. The titles {", ".join(STIPEND_TITLES)} were reviewed as likely stipend payees. They account for {stats["stipend_rows"]:,} retained rows and ${money(stats["stipend_cents"])}. Their median row pay is {stats["stipend_medians"]}, and the largest row is ${money(stats["stipend_max"])}. Title alone does not separate stipend members from salaried members, so these rows stay in the data and the under-5 suppression rule governs small cells.

{stats["high"]} retained rows have pay of at least ${money(HIGH_PAY_CENTS)}, and the largest is ${money(stats["max"])}. These amounts were retained because the files offer no basis for treating them as errors.

Whitespace was collapsed in {stats["title_ws"]:,} position titles and {stats["name_ws"]:,} employee names. No other change was made to titles. Spelling variants are listed in `data/clean/title_variants.csv` and are left unmerged in the clean files.
""", encoding="utf-8")


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    REF.mkdir(parents=True, exist_ok=True)
    frames = {y: load(y) for y in YEARS}
    xwalk = build_xwalk(frames)
    xwalk.to_csv(REF / "department_xwalk.csv", index=False, lineterminator="\n")
    for row in xwalk.itertuples():
        print(f"map {row.raw_department!r} -> {row.canonical_department!r} [{row.department_code}] {row.decision} rows={row.rows}")
    lookup = dict(zip(xwalk["raw_department"], xwalk["canonical_department"]))
    recon, reasons, kept = [], {}, []
    for year, df in frames.items():
        df["department"] = df["raw_department"].map(lookup)
        reasons[year] = exclusion_reason(df)
        row = reconcile(year, df, reasons[year])
        assert row["clean_cents"] == row["raw_cents"] - row["excluded_cents"], year
        assert row["clean_rows"] == row["raw_rows"] - row["excluded_rows"], year
        recon.append(row)
        clean_year = add_person_fields(df[reasons[year] == ""])
        write_year(year, clean_year)
        kept.append(clean_year)
    recon = add_total(recon)
    pd.DataFrame(recon).to_csv(CLEAN / "reconciliation.csv", index=False, lineterminator="\n")
    title_variants(pd.concat(kept)).to_csv(CLEAN / "title_variants.csv", index=False, lineterminator="\n")
    write_exclusions(recon, retained_stats(frames, reasons))
    print(f"\n{'year':>6} {'raw':>8} {'excl':>6} {'clean':>8} {'raw $':>20} {'excluded $':>14} {'clean $':>20}")
    for r in recon:
        print(f"{r['calendar_year']:>6} {r['raw_rows']:>8,} {r['excluded_rows']:>6,} {r['clean_rows']:>8,} {money(r['raw_cents']):>20} {money(r['excluded_cents']):>14} {money(r['clean_cents']):>20}")
    total = recon[-1]
    print("\nexcluded by reason: " + ", ".join(f"{k}={total[k + '_rows']:,}" for k in REASONS))
    print(f"check: {money(total['raw_cents'])} - ({money(total['excluded_cents'])}) = {money(total['clean_cents'])}")


if __name__ == "__main__":
    main()
