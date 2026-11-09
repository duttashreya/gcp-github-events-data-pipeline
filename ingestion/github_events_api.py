import json
import os
from datetime import datetime, timezone

import requests


API_URL = "https://api.github.com/events"
OUTPUT_DIR = "data/raw/github_events"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-events-data-pipeline",
}


def fetch_github_events(per_page=100, max_pages=3):
    events = []

    for page in range(1, max_pages + 1):
        params = {
            "per_page": per_page,
            "page": page,
        }

        response = requests.get(
            API_URL,
            headers=HEADERS,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        page_events = response.json()

        if not page_events:
            break

        events.extend(page_events)

        print(
            f"Fetched page {page}: "
            f"{len(page_events)} events"
        )

    return events


def save_raw_events(events):
    ingestion_timestamp = datetime.now(timezone.utc)
    ingestion_date = ingestion_timestamp.strftime("%Y-%m-%d")
    timestamp = ingestion_timestamp.strftime("%Y%m%d_%H%M%S")

    output_dir = os.path.join(
        OUTPUT_DIR,
        f"ingestion_date={ingestion_date}",
    )

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(
        output_dir,
        f"github_events_{timestamp}.json",
    )

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)

    return output_file


def main():
    print("Starting GitHub Events API ingestion...")

    events = fetch_github_events()

    print(f"Total events fetched: {len(events)}")

    output_file = save_raw_events(events)

    print(f"Raw events saved to: {output_file}")


if __name__ == "__main__":
    main()
