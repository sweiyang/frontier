"""Add default_view and view_locked columns to the projects table."""

import psycopg2

CONN = {
    "host": "localhost",
    "port": 5433,
    "dbname": "yugabyte",
    "user": "yugabyte",
    "password": "yugabyte",
}
SCHEMA = "conduit"

COLUMNS = [
    ('default_view', "VARCHAR(10) DEFAULT 'site' NOT NULL"),
    ('view_locked', "BOOLEAN DEFAULT FALSE NOT NULL"),
]

def main():
    conn = psycopg2.connect(**CONN)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = 'projects'",
        (SCHEMA,),
    )
    existing = {row[0] for row in cur.fetchall()}
    print(f"Existing columns: {sorted(existing)}")

    for col_name, col_def in COLUMNS:
        if col_name in existing:
            print(f"  {col_name} — already exists, skipping")
        else:
            sql = f'ALTER TABLE "{SCHEMA}"."projects" ADD COLUMN "{col_name}" {col_def}'
            print(f"  {sql}")
            cur.execute(sql)
            print(f"  {col_name} — added")

    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
