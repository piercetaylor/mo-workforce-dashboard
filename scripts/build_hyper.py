"""Write the Hyper extract and the CSV that Tableau Desktop Public Edition connects to."""
from pathlib import Path

import pandas as pd
from tableauhyperapi import Connection, CreateMode, HyperProcess, SqlType, TableDefinition, TableName, Telemetry, escape_string_literal

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "data" / "extract"
HYPER = OUT / "mo_workforce.hyper"
XWALK = ROOT / "data" / "ref" / "department_xwalk.csv"
PAY_TABLE = TableName("Extract", "pay")
XWALK_TABLE = TableName("Extract", "department_xwalk")
PAY_COLUMNS = [("calendar_year", SqlType.int()), ("department", SqlType.text()), ("job_title", SqlType.text()),
               ("annual_pay", SqlType.numeric(14, 2)), ("person_key", SqlType.text()),
               ("person_annual_pay", SqlType.numeric(14, 2)), ("is_primary_row", SqlType.int()), ("source_row_id", SqlType.text())]
XWALK_COLUMNS = [("raw_department", SqlType.text()), ("canonical_department", SqlType.text()), ("department_code", SqlType.text()),
                 ("decision", SqlType.text()), ("rows", SqlType.int()), ("first_year", SqlType.int()), ("last_year", SqlType.int())]


def create(conn, table, columns):
    definition = TableDefinition(table, [TableDefinition.Column(n, t) for n, t in columns])
    conn.catalog.create_table(definition)


def load(conn, table, path):
    return conn.execute_command(f"COPY {table} FROM {escape_string_literal(str(path))} WITH (format csv, delimiter ',', header)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(CLEAN.glob("pay_CY*.csv"))
    expected_pay = sum(len(pd.read_csv(f, usecols=[0])) for f in files)
    expected_xwalk = len(pd.read_csv(XWALK))
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, parameters={"log_config": ""}) as hyper:
        with Connection(hyper.endpoint, HYPER, CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            create(conn, PAY_TABLE, PAY_COLUMNS)
            create(conn, XWALK_TABLE, XWALK_COLUMNS)
            for f in files:
                load(conn, PAY_TABLE, f)
            load(conn, XWALK_TABLE, XWALK)
            pay_rows = conn.execute_scalar_query(f"SELECT COUNT(*) FROM {PAY_TABLE}")
            xwalk_rows = conn.execute_scalar_query(f"SELECT COUNT(*) FROM {XWALK_TABLE}")
    assert pay_rows == expected_pay and xwalk_rows == expected_xwalk
    combined = pd.concat(pd.read_csv(f, dtype=str, keep_default_na=False) for f in files)
    combined.to_csv(OUT / "mo_workforce.csv", index=False, lineterminator="\n")
    assert len(combined) == expected_pay
    people = combined.loc[combined["is_primary_row"] == "1", ["calendar_year", "department", "job_title", "person_key", "person_annual_pay"]]
    people.to_csv(OUT / "mo_workforce_people.csv", index=False, lineterminator="\n")
    assert not people.duplicated(["calendar_year", "person_key"]).any()
    print(f"mo_workforce_people.csv: {len(people):,} rows, one per person and year")
    print(f"pay: {pay_rows:,} rows in hyper = {expected_pay:,} in CSV files; department_xwalk: {xwalk_rows} rows; wrote mo_workforce.csv")
    print("Tableau Desktop Public Edition does not list Tableau extracts as a data source; connect it to mo_workforce.csv.")


if __name__ == "__main__":
    main()
