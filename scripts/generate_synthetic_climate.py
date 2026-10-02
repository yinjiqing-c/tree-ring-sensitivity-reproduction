import os
import pandas as pd
import numpy as np

# Generate synthetic monthly climate files for the three example sites.
# This avoids dependence on NOAA network access while preserving the analysis workflow.

root = os.path.dirname(os.path.dirname(__file__))
climate_dir = os.path.join(root, "data", "climate")
os.makedirs(climate_dir, exist_ok=True)

site_station_map = {
    "site_01": "USW00023174",
    "site_02": "USW00022534",
    "site_03": "USW00094995",
}

start_year = 1950
end_year = 2023

for site_id, station_id in site_station_map.items():
    months = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-01", freq="MS")
    rng = np.random.default_rng(42 + hash(site_id) % 1000)

    # Synthetic precipitation and temperature patterns to mimic realistic seasonal cycles
    if site_id == "site_01":
        base_precip = 90
        precip_trend = np.linspace(0, 30, len(months))
        season = 25 * np.sin(np.arange(len(months)) / 12 * 2 * np.pi)
    elif site_id == "site_02":
        base_precip = 110
        precip_trend = np.linspace(10, 40, len(months))
        season = 30 * np.sin(np.arange(len(months)) / 12 * 2 * np.pi)
    else:
        base_precip = 70
        precip_trend = np.linspace(0, 20, len(months))
        season = 20 * np.sin(np.arange(len(months)) / 12 * 2 * np.pi)

    precip = base_precip + precip_trend + season + rng.normal(0, 18, len(months))
    precip = np.clip(precip, 0, None)

    # Temperature seasonality and warming trend
    temp = 10 + 12 * np.sin(np.arange(len(months)) / 12 * 2 * np.pi - 1.2) + 0.02 * np.arange(len(months))
    temp = temp + rng.normal(0, 2.5, len(months))

    df = pd.DataFrame({
        "DATE": months.strftime("%Y-%m-%d"),
        "PRCP": np.round(precip, 2),
        "TAVG": np.round(temp, 2),
        "TMIN": np.round(temp - 5, 2),
        "TMAX": np.round(temp + 5, 2),
    })

    out_path = os.path.join(climate_dir, f"{station_id}_monthly.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved synthetic climate data to {out_path}")

print("Synthetic climate generation complete.")
