import glob
import os

import duckdb


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "raw",
    "github_events",
)

DUCKDB_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "warehouse",
    "github_events.duckdb",
)


def get_latest_raw_file():
    files = glob.glob(
        os.path.join(
            RAW_DATA_PATH,
            "ingestion_date=*",
            "*.json",
        )
    )

    if not files:
        raise FileNotFoundError(
            "No GitHub Events JSON files found."
        )

    return max(files, key=os.path.getmtime)


def load_raw_events():
    raw_file = get_latest_raw_file()

    print(f"Checking raw file: {raw_file}")

    con = duckdb.connect(DUCKDB_PATH)

    # Raw event table
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_github_events (
            event_id VARCHAR,
            event_type VARCHAR,
            actor JSON,
            repo JSON,
            payload JSON,
            is_public BOOLEAN,
            created_at TIMESTAMP,
            raw_event JSON,
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Control table used to track successfully loaded raw files
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_ingestion_log (
            raw_file VARCHAR PRIMARY KEY,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER
        )
        """
    )

    # Check whether this exact file has already been loaded
    already_loaded = con.execute(
        """
        SELECT COUNT(*)
        FROM raw_ingestion_log
        WHERE raw_file = ?
        """,
        [raw_file],
    ).fetchone()[0]

    if already_loaded > 0:
        print("Raw file already loaded.")
        print("Skipping ingestion to prevent duplicate loading.")
        con.close()
        return

    # Load the new raw file
    con.execute(
        """
        INSERT INTO raw_github_events (
            event_id,
            event_type,
            actor,
            repo,
            payload,
            is_public,
            created_at,
            raw_event
        )
        SELECT
            json_extract_string(json, '$.id') AS event_id,
            json_extract_string(json, '$.type') AS event_type,
            json_extract(json, '$.actor') AS actor,
            json_extract(json, '$.repo') AS repo,
            json_extract(json, '$.payload') AS payload,
            CAST(json_extract(json, '$.public') AS BOOLEAN) AS is_public,
            CAST(
                json_extract_string(json, '$.created_at')
                AS TIMESTAMP
            ) AS created_at,
            json AS raw_event
        FROM read_json_objects(?)
        """,
        [raw_file],
    )

    # Get number of rows loaded from this file
    loaded_row_count = con.execute(
        """
        SELECT COUNT(*)
        FROM read_json_objects(?)
        """,
        [raw_file],
    ).fetchone()[0]

    # Record successful ingestion
    con.execute(
        """
        INSERT INTO raw_ingestion_log (
            raw_file,
            row_count
        )
        VALUES (?, ?)
        """,
        [raw_file, loaded_row_count],
    )

    total_count = con.execute(
        """
        SELECT COUNT(*)
        FROM raw_github_events
        """
    ).fetchone()[0]

    con.close()

    print("Raw events loaded successfully.")
    print(f"Rows loaded from current file: {loaded_row_count}")
    print(f"Total rows in raw_github_events: {total_count}")


if __name__ == "__main__":
    load_raw_events()