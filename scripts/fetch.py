"""Download State Employee Pay from data.mo.gov and write the source survey."""
import csv
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PORTAL = "https://data.mo.gov"
MAP_DOWNLOAD = "https://mapyourtaxes.mo.gov/MAP/Download/Default.aspx"
MAP_EMPLOYEES = "https://mapyourtaxes.mo.gov/MAP/Employees/"
POLICY = "https://mo.gov/data-policy"
OA_REPORTS = [f"https://oa.mo.gov/sites/default/files/AnnualReport{y}.pdf" for y in (2017, 2018)]
WORKFORCE_ID = "gvbf-hkku"
PROTECTED = "PROTECTED"
STIPEND_TITLES = ["BOARD MEMBER", "COMMISSION MEMBER", "COMMISSION MEMBERS"]
FIELDS = ["calendar_year", "agency_name", "position_title", "employee_name", "ytd_gross_pay"]
TODAY = date.today().isoformat()


def get(url, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": "mo-workforce-dashboard"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url))


def row_count(uid):
    query = urllib.parse.urlencode({"$select": "count(*) as n"})
    return int(get_json(f"{PORTAL}/resource/{uid}.json?{query}")[0]["n"])


def pay_datasets():
    """Return (year, id) for every State Employee Pay dataset in the portal catalog."""
    query = urllib.parse.urlencode({"domains": "data.mo.gov", "search_context": "data.mo.gov", "limit": 1000})
    results = get_json(f"https://api.us.socrata.com/api/catalog/v1?{query}")["results"]
    names = [(r["resource"]["name"], r["resource"]["id"]) for r in results]
    return sorted((int(n[:4]), uid) for n, uid in names if re.fullmatch(r"\d{4} State Employee Pay", n))


def fetch_year(year, uid):
    """Download one year, check it against the API row count, and return its manifest row."""
    meta = get_json(f"{PORTAL}/api/views/{uid}.json")
    url = f"{PORTAL}/api/views/{uid}/rows.csv?accessType=DOWNLOAD"
    body = get(url)
    (RAW / f"{year}.csv").write_bytes(body)
    rows = sum(1 for _ in csv.reader(body.decode("utf-8").splitlines())) - 1
    assert rows == row_count(uid), year
    assert [c["fieldName"] for c in meta["columns"]] == FIELDS, year
    updated = datetime.fromtimestamp(meta["rowsUpdatedAt"], timezone.utc).date().isoformat()
    return {"calendar_year": year, "dataset_id": uid, "url": url, "rows": rows, "bytes": len(body),
            "sha256_sorted_lines": hashlib.sha256(b"\n".join(sorted(body.splitlines()))).hexdigest(),
            "data_updated": updated, "retrieved": TODAY,
            "license": meta.get("license") or "", "attribution": meta.get("attribution") or ""}


def load(year):
    df = pd.read_csv(RAW / f"{year}.csv", dtype=str, keep_default_na=False)
    df.columns = ["year", "agency", "title", "name", "pay"]
    df["pay"] = df["pay"].astype(float)
    return df


def year_stats(year, df):
    """Profile one raw year. A person is approximated by (agency, name); protected rows count singly."""
    protected = df["name"].str.startswith(PROTECTED)
    dup = df.duplicated()
    units = df[~protected].groupby(["agency", "name"])["pay"].agg(["size", "sum"])
    unit_pay = pd.concat([units["sum"], df.loc[protected, "pay"]])
    stipend = df["title"].isin(STIPEND_TITLES)
    negative = df["pay"] < 0
    return {"year": year, "rows": len(df), "total": df["pay"].sum(), "zero": int((df["pay"] == 0).sum()),
            "neg": int(negative.sum()), "neg_total": df.loc[negative, "pay"].sum(), "dup": int(dup.sum()),
            "dup_prot": int((dup & protected).sum()), "prot": int(protected.sum()),
            "blank_agency": int((df["agency"].str.strip() == "").sum()), "units": len(unit_pay),
            "multi": int((units["size"] > 1).sum()), "stipend": int(stipend.sum()),
            "stipend_total": df.loc[stipend, "pay"].sum(), "row_median": df["pay"].median(),
            "unit_median": unit_pay.median(), "max": df["pay"].max()}


def top_title_pairs(df, n=5):
    named = df[~df["name"].str.startswith(PROTECTED)]
    sets = named.groupby(["agency", "name"])["title"].agg(lambda s: tuple(sorted(set(s))))
    return Counter(sets[sets.map(len) == 2]).most_common(n)


def survey_map():
    """Read the Accountability Portal file list and the layout of its plain-text 2026 file."""
    page = get(MAP_DOWNLOAD).decode("utf-8", "replace")
    files = re.findall(r">Employee ([\d-]+\.\w+)</a><span id=\"lblEMP_[\d-]+\">\s*&nbsp\s*([\d.]+ MB)", page)
    form = {html.unescape(k): html.unescape(v) for k, v in
            re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', page)}
    form.update({"__EVENTTARGET": "EMP_2026", "__EVENTARGUMENT": ""})
    lines = get(MAP_DOWNLOAD, urllib.parse.urlencode(form).encode()).decode("latin-1").splitlines()
    employees = get(MAP_EMPLOYEES).decode("utf-8", "replace")
    as_of = re.search(r"current as of the\s+([A-Za-z]+ \d+, \d{4})", employees).group(1)
    return {"files": files, "rows_2026": len(lines) - 1, "header": [c.strip() for c in lines[0].split("|")], "as_of": as_of}


def disclaimer():
    """Return the disclaimer that the State Data Policy requires applications to display."""
    page = get(POLICY).decode("utf-8")
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<(script|style).*?</\1>|<[^>]+>", " ", page, flags=re.S)))
    return re.search(r"following disclaimers on their sites: \W*(.+?)\W* Right to Modify", text).group(1) + "."


def md_table(rows):
    head = list(rows[0])
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    return "\n".join(lines + ["| " + " | ".join(str(r[h]) for h in head) + " |" for r in rows])


def money(x):
    return f"{x:,.2f}"


def write_sources(manifest, stats, pairs, new_agencies, m, notice, oa_status, workforce):
    years = [s["year"] for s in stats]
    first, last = min(years), max(years)
    y2020 = next(s for s in stats if s["year"] == 2020)
    others = [s["multi"] for s in stats if s["year"] != 2020]
    no_license = sum(1 for r in manifest if not r["license"])
    attribution = sorted({r["attribution"] for r in manifest})
    pick = md_table([{"Calendar year": r["calendar_year"], "Dataset": f"[{r['dataset_id']}]({PORTAL}/d/{r['dataset_id']})",
                      "Rows": f"{r['rows']:,}", "MB": f"{r['bytes'] / 1e6:.1f}", "Data last updated": r["data_updated"]}
                     for r in manifest])
    profile = md_table([{"Year": s["year"], "Rows": f"{s['rows']:,}", "Total pay ($)": money(s["total"]), "Zero": s["zero"],
                         "Negative": s["neg"], "Negative ($)": money(s["neg_total"]),
                         "Exact duplicates (protected)": f"{s['dup']} ({s['dup_prot']})", "Protected": s["prot"],
                         "Blank agency": s["blank_agency"], "Stipend titles": s["stipend"],
                         "Stipend ($)": money(s["stipend_total"]), "Person units": f"{s['units']:,}",
                         "Units with 2+ rows": f"{s['multi']:,}", "Row median ($)": money(s["row_median"]),
                         "Unit median ($)": money(s["unit_median"]), "Maximum ($)": money(s["max"])} for s in stats])
    pair_rows = md_table([{"Title A": a, "Title B": b, "Person units": f"{n:,}"} for (a, b), n in pairs])
    map_years = [f for f, _ in m["files"] if re.fullmatch(r"\d{4}\.txt", f)]
    agencies = "; ".join(f"{a} (first in {y})" for a, y in new_agencies)
    candidates = md_table([
        {"Candidate": "State Employee Pay", "URL": f"{PORTAL}/d/{manifest[-1]['dataset_id']} (one dataset per year)",
         "Fields": ", ".join(FIELDS), "Rows": f"{sum(r['rows'] for r in manifest):,} over {len(manifest)} files",
         "Years": f"Calendar {first}-{last}", "Terms": "No license stated; State Data Policy applies",
         "Retrieved": TODAY, "Decision": "Selected"},
        {"Candidate": "Missouri Accountability Portal employee files", "URL": MAP_DOWNLOAD,
         "Fields": ", ".join(m["header"]), "Rows": f"{m['rows_2026']:,} in the 2026 file; earlier files not downloaded",
         "Years": f"Calendar {map_years[-1][:4]}-{map_years[0][:4]}; 2026 runs through the {m['as_of']} pay date",
         "Terms": "Portal disclaimer text could not be read; coverage by the Data Policy is unconfirmed",
         "Retrieved": TODAY, "Decision": "Not used; same schema and years, and 2026 is a partial year"},
        {"Candidate": "Office of Administration annual reports", "URL": " ".join(OA_REPORTS),
         "Fields": "PDF report tables", "Rows": "Not row-level", "Years": "2017 and 2018 reports located",
         "Terms": "Not reviewed", "Retrieved": TODAY,
         "Decision": f"Not used; HTTP {oa_status} confirmed, and no bulk pay file was located on this site"},
        {"Candidate": workforce["name"], "URL": f"{PORTAL}/d/{WORKFORCE_ID}", "Fields": "County workforce demographics",
         "Rows": f"{workforce['rows']:,}", "Years": "2016", "Terms": f"Attributed to {workforce['attribution']}",
         "Retrieved": TODAY, "Decision": "Not used; contains no state employee pay"}])
    (DATA / "SOURCES.md").write_text(f"""# Data sources

`scripts/fetch.py` writes this file and produces every number in it. Files were retrieved on {TODAY}. `data/manifest.csv` records the URL, row count, size and a SHA-256 hash of the sorted lines of each downloaded file. The hash is taken over sorted lines because repeat downloads returned the same rows in a different order for some years.

## Selected source

The State of Missouri publishes one State Employee Pay dataset per calendar year on data.mo.gov. Each dataset names {", ".join(attribution)} as its attribution. The {len(manifest)} datasets cover calendar years {first} to {last} and hold {sum(r["rows"] for r in manifest):,} rows in total. Every file has the same five fields: `{"`, `".join(FIELDS)}`. The CSV row count of each file equals the row count returned by the Socrata API.

{pick}

The files report calendar years. Fiscal-year pay cannot be derived because each row carries one year-to-date amount with no pay dates. The Accountability Portal states that gross pay includes all pay received and is not base salary. The files contain no division, pay type, FTE, hours or employee identifier field.

## Terms of use

The license field in the portal metadata is empty for {no_license} of {len(manifest)} datasets, and no license is therefore claimed here. The data.mo.gov footer links to the State Data Policy ({POLICY}). The policy contains no prohibition on reuse. It disclaims warranties, requires applications using the data to display the notice below, and reserves the right of the State to require that display or use of the data end. The notice is stored in `data/ref/mo_data_policy_disclaimer.txt` and must appear on the dashboard.

> {notice}

## Candidates reviewed

{candidates}

Pre-2026 Accountability Portal employee files are described on the download page as zipped executables, and they were not downloaded or run. The contents of the Office of Administration reports were taken from web search summaries, and the PDFs were not parsed.

## Observations in the raw files

The table precedes all exclusions. A person unit is one distinct (agency, employee name) pair within a year, plus one unit for each protected row. The dataset has no employee identifier, so two people with the same name in one agency merge into one unit. A person working in two agencies counts as two units. Unit median is the median of pay summed to the person unit.

{profile}

The 2020 file holds {y2020["rows"]:,} rows, and {y2020["multi"]:,} person units have two or more rows. Other years have between {min(others):,} and {max(others):,} such units. The row-level median in 2020 is ${money(y2020["row_median"])}, while the unit median is ${money(y2020["unit_median"])}. The title pairs below are the most frequent among 2020 units holding exactly two titles. The pattern is consistent with a mid-year change of job classifications that split pay across an old and a new title. The cause is inferred from these pairs, because no State document describing it was located.

{pair_rows}

Rows whose employee name begins with `{PROTECTED}` carry a masked name and cannot be resolved to a person. Exact duplicate rows among protected names may be distinct people with identical pay. The titles {", ".join(STIPEND_TITLES)} are counted as stipend titles. Agencies absent from the first year and present later are: {agencies or "none"}.
""", encoding="utf-8")


def main():
    for path in (RAW, DATA / "ref"):
        path.mkdir(parents=True, exist_ok=True)
    manifest = [fetch_year(y, uid) for y, uid in pay_datasets()]
    with open(DATA / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    frames = {r["calendar_year"]: load(r["calendar_year"]) for r in manifest}
    stats = [year_stats(y, df) for y, df in frames.items()]
    first_seen = {}
    for y, df in frames.items():
        for agency in set(df["agency"].str.strip()) - {""}:
            first_seen.setdefault(agency, y)
    new_agencies = sorted(((a, y) for a, y in first_seen.items() if y > min(frames)), key=lambda t: t[1])
    notice = disclaimer()
    (DATA / "ref" / "mo_data_policy_disclaimer.txt").write_text(notice + "\n", encoding="utf-8")
    meta = get_json(f"{PORTAL}/api/views/{WORKFORCE_ID}.json")
    workforce = {"name": meta["name"], "attribution": meta["attribution"], "rows": row_count(WORKFORCE_ID)}
    oa_status = "/".join(sorted({str(urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}), timeout=60).status) for u in OA_REPORTS}))
    write_sources(manifest, stats, top_title_pairs(frames[2020]), new_agencies, survey_map(), notice, oa_status, workforce)
    print(f"{len(manifest)} files, {sum(r['rows'] for r in manifest):,} rows, {sum(r['bytes'] for r in manifest) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
