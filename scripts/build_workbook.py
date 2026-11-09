"""Write the Tableau workbook for the dashboard defined in docs/TABLEAU_BUILD.md."""
import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "data" / "extract"
OUT = EXTRACT / "mo_workforce.twb"
CSV_NAME = "mo_workforce_people.csv"
DS = "federated.0mo0workforce0people0000000"
CONN = "textscan.0mo0workforce0people0000000"
PARAM = "[Parameters].[Parameter 1]"
DASHBOARD = "Missouri State Workforce Pay"
SOURCE_BUILD = "0.0.0 (0000.25.1024.2150)"
USD = 'c"$"#,##0;-"$"#,##0'
PCT = "p0.0%"
MEASURE_NAMES = f"[{DS}].[:Measure Names]"


def calc_id(n):
    return f"Calculation_{1000000000000000000 + n}"


NAMES = {k: calc_id(i) for i, k in enumerate(
    ["headcount", "median", "mean", "hc_yoy", "median_yoy", "state_median", "state_headcount", "share",
     "s_headcount", "s_median", "s_mean", "show", "selected"], 1)}
R = {k: f"[{v}]" for k, v in NAMES.items()}
LOOKUP = "(ZN({0}) - LOOKUP(ZN({0}), -1)) / ABS(LOOKUP(ZN({0}), -1))"
CALCS = [("headcount", "Headcount", "COUNTD([person_key])", "integer", "measure", "quantitative", "n#,##0"),
         ("median", "Median Pay", "MEDIAN([person_annual_pay])", "real", "measure", "quantitative", USD),
         ("mean", "Mean Pay", "AVG([person_annual_pay])", "real", "measure", "quantitative", USD),
         ("hc_yoy", "Headcount YoY", LOOKUP.format(R["headcount"]), "real", "measure", "quantitative", PCT),
         ("median_yoy", "Median Pay YoY", LOOKUP.format(R["median"]), "real", "measure", "quantitative", PCT),
         ("state_median", "Statewide Median", "{ FIXED [calendar_year] : MEDIAN([person_annual_pay]) }", "real", "measure", "quantitative", USD),
         ("state_headcount", "Statewide Headcount", "{ FIXED [calendar_year] : COUNTD([person_key]) }", "integer", "measure", "quantitative", "n#,##0"),
         ("share", "Share of Statewide", f"{R['headcount']} / MIN({R['state_headcount']})", "real", "measure", "quantitative", PCT),
         ("s_headcount", "Headcount (5+)", f"IF {R['headcount']} >= 5 THEN {R['headcount']} END", "integer", "measure", "quantitative", "n#,##0"),
         ("s_median", "Median Pay (5+)", f"IF {R['headcount']} >= 5 THEN {R['median']} END", "real", "measure", "quantitative", USD),
         ("s_mean", "Mean Pay (5+)", f"IF {R['headcount']} >= 5 THEN {R['mean']} END", "real", "measure", "quantitative", USD),
         ("show", "Show Cell", f"{R['headcount']} >= 5", "boolean", "measure", "nominal", None),
         ("selected", "Selected Year", f"[calendar_year] = {PARAM}", "boolean", "dimension", "nominal", None)]
BASE = [("calendar_year", "integer", "dimension", "ordinal"), ("department", "string", "dimension", "nominal"),
        ("job_title", "string", "dimension", "nominal"), ("person_key", "string", "dimension", "nominal"),
        ("person_annual_pay", "real", "measure", "quantitative")]


def inst(kind, name):
    """Return the shelf reference for a field instance."""
    return f"[{DS}].[{kind}:{name}]"


YEAR = inst("none", "calendar_year:ok")
DEPT = inst("none", "department:nk")
TITLE = inst("none", "job_title:nk")
SEL = inst("none", f"{NAMES['selected']}:nk")
SHOW = inst("usr", f"{NAMES['show']}:nk")
STATE_MED = inst("min", f"{NAMES['state_median']}:qk")


def usr(key):
    return inst("usr", f"{NAMES[key]}:qk")


def param_column(first, last):
    members = "".join(f"<member value='{y}' />" for y in range(first, last + 1))
    return (f"<column caption='Calendar year' datatype='integer' default-format='*0' name='[Parameter 1]' param-domain-type='list' "
            f"role='measure' type='quantitative' value='{last}'><calculation class='tableau' formula='{last}' /><members>{members}</members></column>")


def column_xml():
    rows = [f"<column caption='{n.replace('_', ' ').title()}' datatype='{d}' name='[{n}]' role='{r}' type='{t}' />" for n, d, r, t in BASE]
    for key, caption, formula, dtype, role, typ, fmt in CALCS:
        fattr = f" default-format={quoteattr(fmt)}" if fmt else ""
        rows.append(f"<column caption={quoteattr(caption)} datatype='{dtype}'{fattr} name='{R[key]}' role='{role}' type='{typ}'>"
                    f"<calculation class='tableau' formula={quoteattr(formula)} /></column>")
    return "\n".join(rows)


def instances(refs):
    """Declare the column instances a worksheet uses."""
    out = []
    for ref in refs:
        short = ref.split(".[", 1)[1][:-1]
        kind, name, code = short.split(":")
        derivation = {"none": "None", "usr": "User", "min": "Min"}[kind]
        typ = {"ok": "ordinal", "nk": "nominal", "qk": "quantitative"}[code]
        out.append(f"<column-instance column='[{name}]' derivation='{derivation}' name='[{short}]' pivot='key' type='{typ}' />")
    return "\n".join(out)


def bool_filter(ref):
    short = ref.split(".[", 1)[1][:-1]
    return f"<filter class='categorical' column='{ref}'><groupfilter function='member' level='[{short}]' member='true' /></filter>"


def measure_names_filter(keys):
    members = "".join(f"<groupfilter function='member' level='[:Measure Names]' member={quoteattr(chr(34) + usr(k) + chr(34))} />" for k in keys)
    return f"<filter class='categorical' column='{MEASURE_NAMES}'><groupfilter function='union' user:op='manual'>{members}</groupfilter></filter>"


def worksheet(param, name, refs, filters, rows, cols, mark, encodings, extra_filter="", sort="", pane_extra="", style="<style />"):
    slice_refs = ([MEASURE_NAMES] if extra_filter else []) + list(filters)
    slices = "".join(f"<column>{r}</column>" for r in slice_refs)
    filter_xml = extra_filter + "".join(bool_filter(r) for r in filters)
    return f"""<worksheet name={quoteattr(name)}><table><view>
<datasources><datasource caption='mo_workforce_people' name='{DS}' /><datasource name='Parameters' /></datasources>
<datasource-dependencies datasource='Parameters'>{param}</datasource-dependencies>
<datasource-dependencies datasource='{DS}'>
{column_xml()}
{instances(refs)}
</datasource-dependencies>
{filter_xml}
{sort}
{f"<slices>{slices}</slices>" if slices else ""}
<aggregation value='true' />
</view>{style}
<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view><mark class='{mark}' />
<encodings>{encodings}</encodings>{pane_extra}</pane></panes>
<rows>{rows}</rows><cols>{cols}</cols>
</table></worksheet>"""


def header_style(headers, cell_width=None):
    widths = "".join(f"<format attr='width' field='{ref}' value='{w}' />" for ref, w in headers)
    cell = f"<style-rule element='cell'><format attr='width' field='{MEASURE_NAMES}' value='{cell_width}' /></style-rule>" if cell_width else ""
    return f"<style>{cell}<style-rule element='header'>{widths}</style-rule></style>"


def text_zone(zone_id, x, y, w, h, paragraphs):
    runs = "".join(f"<run fontsize='8'>{escape(p)}&#10;</run>" for p in paragraphs)
    return f"<zone h='{h}' id='{zone_id}' type-v2='text' w='{w}' x='{x}' y='{y}'><formatted-text>{runs}</formatted-text></zone>"


def filter_action():
    expression = f"tsl:{quote(DASHBOARD)}?%5B{DS}%5D.%5Bdepartment%5D~s0=&lt;[department]~na&gt;"
    return (f"<actions><action caption='Department to Job Title' name='[Action1_00000000000000000000000000000001]'>"
            f"<activation auto-clear='true' type='on-select' /><source dashboard={quoteattr(DASHBOARD)} type='sheet' worksheet='Department Median' />"
            f"<link caption='Department to Job Title' delimiter=',' escape='\\' expression='{expression}' include-null='true' multi-select='true' url-escape='true' />"
            f"<command command='tsc:tsl-filter'><param name='exclude' value='Department Median,Statewide Trend,Department Share' />"
            f"<param name='target' value={quoteattr(DASHBOARD)} /></command></action></actions>")


def main():
    summary = json.loads((ROOT / "data" / "clean" / "metrics_summary.json").read_text(encoding="utf-8"))
    first, last = summary["first"], summary["latest"]
    manifest = pd.read_csv(ROOT / "data" / "manifest.csv")
    notice = (ROOT / "data" / "ref" / "mo_data_policy_disclaimer.txt").read_text(encoding="utf-8").strip()
    param = param_column(first, last)
    base_cols = "\n".join(f"<column datatype='{d}' name='{n}' ordinal='{i}' />" for i, (n, d, _, _) in enumerate(BASE))

    trend = worksheet(param, "Statewide Trend", [YEAR, usr("median"), usr("headcount"), usr("median_yoy"), usr("hc_yoy")], [],
                      f"({usr('median')} / {usr('headcount')})", YEAR, "Line",
                      f"<tooltip column='{usr('median_yoy')}' /><tooltip column='{usr('hc_yoy')}' />")
    bar = worksheet(param, "Department Median", [DEPT, usr("s_median"), usr("s_headcount"), STATE_MED, SEL], [SEL], DEPT, usr("s_median"), "Bar",
                    f"<lod column='{STATE_MED}' /><tooltip column='{usr('s_headcount')}' />",
                    sort=f"<computed-sort column='{DEPT}' direction='DESC' using='{usr('s_median')}' />",
                    pane_extra=f"<reference-line axis-column='{usr('s_median')}' enable-instant-analytics='true' formula='min' id='refline0' label='Statewide median' "
                               f"label-type='custom' scope='per-table' value-column='{STATE_MED}' z-order='1' />",
                    style=header_style([(DEPT, 225)]))
    table = worksheet(param, "Job Title Table", [DEPT, TITLE, usr("s_headcount"), usr("s_median"), usr("s_mean"), SEL, SHOW], [SEL, SHOW],
                      f"({DEPT} / {TITLE})", MEASURE_NAMES, "Automatic", f"<text column='[{DS}].[Multiple Values]' />",
                      extra_filter=measure_names_filter(["s_headcount", "s_median", "s_mean"]),
                      sort=f"<computed-sort column='{TITLE}' direction='DESC' using='{usr('s_headcount')}' />",
                      style=header_style([(DEPT, 115), (TITLE, 235)], cell_width=116))
    share = worksheet(param, "Department Share", [DEPT, usr("headcount"), usr("share"), SEL], [SEL], "", "", "Square",
                      f"<size column='{usr('headcount')}' /><color column='{usr('share')}' /><text column='{DEPT}' /><text column='{usr('share')}' />",
                      pane_extra="<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' /></style-rule></style>")

    retrieved = manifest["retrieved"].iloc[0]
    source = f"Source: State Employee Pay, Office of Administration, State of Missouri, data.mo.gov. Retrieved {retrieved}. Years shown are calendar years."
    definitions = ("Headcount counts people paid at any point in the year, identified by name within a department, so it is not a count of filled positions. "
                   "Pay is gross pay for the calendar year, summed for each person, and includes all pay received; it is not base salary. "
                   "Part-year and part-time work lower the median and mean. Groups with fewer than five people are hidden.")
    zones = "\n".join([
        "<zone h='6000' id='3' type-v2='title' w='76000' x='0' y='0' />",
        f"<zone h='6000' id='4' mode='compact' param='{PARAM}' type-v2='paramctrl' w='24000' x='76000' y='0' />",
        "<zone h='24000' id='5' name='Statewide Trend' w='100000' x='0' y='6000' />",
        "<zone h='55000' id='6' name='Department Median' w='38000' x='0' y='30000' />",
        "<zone h='33000' id='8' name='Job Title Table' w='62000' x='38000' y='30000' />",
        "<zone h='22000' id='7' name='Department Share' w='62000' x='38000' y='63000' />",
        text_zone(9, 0, 85000, 100000, 15000, [source, definitions, notice])])
    sheets = ["Statewide Trend", "Department Median", "Job Title Table", "Department Share"]
    cards = ("<cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>"
             "<edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>"
             "<strip size='31'><card type='title' /></strip></edge></cards>")
    windows = "".join(f"<window class='worksheet' hidden='true' name={quoteattr(s)}>{cards}<viewpoint /></window>" for s in sheets)
    viewpoints = "".join(f"<viewpoint name={quoteattr(s)} />" if s == "Job Title Table" else f"<viewpoint name={quoteattr(s)}><zoom type='entire-view' /></viewpoint>" for s in sheets)
    xml = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build='{SOURCE_BUILD}' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
<document-format-change-manifest><SortTagCleanup /></document-format-change-manifest>
<preferences><preference name='ui.encoding.shelf.height' value='24' /></preferences>
<datasources>
<datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>
<aliases enabled='yes' />
{param}
</datasource>
<datasource caption='mo_workforce_people' inline='true' name='{DS}' version='18.1'>
<connection class='federated'>
<named-connections><named-connection caption='mo_workforce_people' name='{CONN}'>
<connection class='textscan' directory={quoteattr(EXTRACT.as_posix())} filename='{CSV_NAME}' password='' server='' />
</named-connection></named-connections>
<relation connection='{CONN}' name='{CSV_NAME}' table='[mo_workforce_people#csv]' type='table'>
<columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
{base_cols}
</columns></relation>
</connection>
<aliases enabled='yes' />
{column_xml()}
<drill-paths><drill-path name='Department Hierarchy'><field>[department]</field><field>[job_title]</field></drill-path></drill-paths>
<layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.4' show-structure='true' />
</datasource>
</datasources>
{filter_action()}
<worksheets>
{trend}
{bar}
{table}
{share}
</worksheets>
<dashboards><dashboard name={quoteattr(DASHBOARD)}><style />
<size maxheight='900' maxwidth='1200' minheight='900' minwidth='1200' />
<datasources><datasource name='Parameters' /></datasources>
<datasource-dependencies datasource='Parameters'>{param}</datasource-dependencies>
<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
{zones}
</zone></zones></dashboard></dashboards>
<windows source-height='30'><window class='dashboard' maximized='true' name={quoteattr(DASHBOARD)}><viewpoints>{viewpoints}</viewpoints><active id='-1' /></window>{windows}</windows>
</workbook>
"""
    ElementTree.fromstring(xml.encode("utf-8"))
    OUT.write_text(xml, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
