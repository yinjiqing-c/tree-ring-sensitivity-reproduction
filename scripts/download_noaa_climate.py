import os
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CLIMATE_DIR = DATA_DIR / "climate"
CLIMATE_DIR.mkdir(parents=True, exist_ok=True)


# Replace these with representative stations you actually plan to use.
STATIONS = [
    "USW00023174",
    "USW00022534",
    "USW00094995",
]
START_YEAR = 1950
END_YEAR = 2023


def download_station(station_id: str) -> None:
    url = (
        "https://www.ncei.noaa.gov/access/services/data/v1"
        f"?dataset=monthly-summaries"
        f"&stations={station_id}"
        f"&startdate={START_YEAR}-01-01"
        f"&enddate={END_YEAR}-12-31"
        "&units=metric"
        "&format=json"
        "&dataTypes=PRCP,TAVG,TMIN,TMAX"
    )
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if not payload:
            print(f"No climate data returned for {station_id}")
            return

        df = pd.DataFrame(payload)
        if "DATE" not in df.columns:
            print(f"No DATE field for {station_id}")
            return

        out_path = CLIMATE_DIR / f"{station_id}_monthly.csv"
        df.to_csv(out_path, index=False)
        print(f"Saved: {out_path}")
    except Exception as exc:
        print(f"Failed to fetch {station_id}: {exc}")


if __name__ == "__main__":
    for station in STATIONS:
        download_station(station)
        time.sleep(1)
    print("Climate download complete.")
