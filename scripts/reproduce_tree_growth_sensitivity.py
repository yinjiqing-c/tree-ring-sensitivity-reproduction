import os
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TREE_DIR = DATA_DIR / "tree_ring"
CLIMATE_DIR = DATA_DIR / "climate"
OUT_DIR = DATA_DIR / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Example site-to-station mapping. Replace with your local data.
SITE_MAP = {
    "site_01": "USW00023174",
    "site_02": "USW00022534",
    "site_03": "USW00094995",
}


def load_tree_ring(site_id: str) -> pd.DataFrame:
    """Load a site-level tree-ring CSV.

    Expected columns:
        site_id, year, ring_width
    """
    path = TREE_DIR / f"{site_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing tree-ring CSV: {path}")

    df = pd.read_csv(path)
    required = {"year", "ring_width"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{site_id} is missing columns: {missing}")

    df["site_id"] = site_id
    df["year"] = df["year"].astype(int)
    return df[["site_id", "year", "ring_width"]].sort_values("year").reset_index(drop=True)


def load_climate(station_id: str) -> pd.DataFrame:
    """Load NOAA monthly climate CSV.

    Expected columns:
        DATE, PRCP, TAVG, TMIN, TMAX
    """
    path = CLIMATE_DIR / f"{station_id}_monthly.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing climate file: {path}")

    df = pd.read_csv(path)
    if "DATE" not in df.columns:
        raise ValueError(f"Climate file {path} is missing DATE column")

    # Keep only necessary climate fields
    for col in ["PRCP", "TAVG"]:
        if col not in df.columns:
            raise ValueError(f"Climate file {path} is missing {col}")

    df["DATE"] = pd.to_datetime(df["DATE"])
    df["year"] = df["DATE"].dt.year
    df["month"] = df["DATE"].dt.month
    df["PRCP"] = pd.to_numeric(df["PRCP"], errors="coerce")
    df["TAVG"] = pd.to_numeric(df["TAVG"], errors="coerce")

    yearly = (
        df.groupby("year", as_index=False)
        .agg(
            annual_precip=("PRCP", "sum"),
            mean_temp=("TAVG", "mean"),
        )
    )
    return yearly


def detrend_ring_width(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Detrend ring width with a rolling mean baseline.

    This is a simple approximation of the chronology standardization step
    commonly used in tree-ring studies.
    """
    out = df.copy()
    out = out.sort_values("year").reset_index(drop=True)
    baseline = out["ring_width"].rolling(window=window, center=True, min_periods=5).mean()
    out["ring_baseline"] = baseline
    out["ring_index"] = out["ring_width"] / out["ring_baseline"].replace(0, np.nan)
    out["ring_index"] = out["ring_index"].replace([np.inf, -np.inf], np.nan)
    out["ring_index"] = (out["ring_index"] - out["ring_index"].mean()) / out["ring_index"].std(ddof=0)
    return out


def rolling_sensitivity(series: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Compute rolling-window slope of ring_index vs precipitation anomaly.

    Sensitivity is approximated as the slope coefficient from a simple regression:
        ring_index ~ precip_anom
    over a moving window.
    """
    result = []
    for idx in range(len(series) - window + 1):
        subset = series.iloc[idx:idx + window].copy()
        if len(subset) < window:
            continue

        X = subset[["precip_anom"]]
        y = subset["ring_index"]

        if X.isna().any().any() or y.isna().any():
            continue

        model = LinearRegression()
        model.fit(X, y)
        beta = float(model.coef_[0])
        result.append({
            "year": subset["year"].iloc[-1],
            "sensitivity": beta,
            "r2": float(model.score(X, y)),
            "n": len(subset),
        })

    return pd.DataFrame(result)


def compute_site_sensitivity(site_id: str, station_id: str) -> pd.DataFrame:
    tree = load_tree_ring(site_id)
    climate = load_climate(station_id)

    merged = tree.merge(climate, on="year", how="inner")
    if merged.empty:
        raise ValueError(f"No overlapping years for {site_id} and {station_id}")

    merged = detrend_ring_width(merged)
    merged["annual_precip_mean"] = merged["annual_precip"].mean()
    merged["precip_anom"] = merged["annual_precip"] - merged["annual_precip_mean"]

    # Optional: remove rows with missing values
    merged = merged.dropna(subset=["ring_index", "precip_anom"]).reset_index(drop=True)

    # Full-period sensitivity estimate
    model = LinearRegression()
    X = merged[["precip_anom"]]
    y = merged["ring_index"]
    model.fit(X, y)

    full = pd.DataFrame([{
        "site_id": site_id,
        "station_id": station_id,
        "full_period_beta": float(model.coef_[0]),
        "full_period_r2": float(model.score(X, y)),
        "start_year": int(merged["year"].min()),
        "end_year": int(merged["year"].max()),
        "n_years": len(merged),
    }])

    rolling = rolling_sensitivity(merged, window=20)
    rolling["site_id"] = site_id
    rolling["station_id"] = station_id

    return full, rolling


def run_all() -> None:
    all_full = []
    all_rolling = []

    for site_id, station_id in SITE_MAP.items():
        try:
            full, rolling = compute_site_sensitivity(site_id, station_id)
            all_full.append(full)
            all_rolling.append(rolling)
        except Exception as e:
            print(f"Skipping {site_id}: {e}")

    if not all_full:
        raise RuntimeError("No valid site-level analyses were produced")

    full_df = pd.concat(all_full, ignore_index=True)
    rolling_df = pd.concat(all_rolling, ignore_index=True)

    full_out = OUT_DIR / "site_level_sensitivity.csv"
    rolling_out = OUT_DIR / "rolling_sensitivity.csv"
    full_df.to_csv(full_out, index=False)
    rolling_df.to_csv(rolling_out, index=False)

    print(f"Saved full-period sensitivity: {full_out}")
    print(f"Saved rolling sensitivity: {rolling_out}")

    # Simple plot of rolling sensitivity over time
    fig, ax = plt.subplots(figsize=(9, 5))
    for site_id, df in rolling_df.groupby("site_id"):
        ax.plot(df["year"], df["sensitivity"], marker="o", linewidth=1.5, label=site_id)
    ax.axhline(0, color="black", linewidth=1, linestyle="--")
    ax.set_title("Rolling sensitivity of tree growth to precipitation")
    ax.set_xlabel("Year")
    ax.set_ylabel("Sensitivity (growth anomaly per precip anomaly)")
    ax.grid(alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "rolling_sensitivity_plot.png", dpi=200)
    print(f"Saved plot: {OUT_DIR / 'rolling_sensitivity_plot.png'}")


if __name__ == "__main__":
    run_all()
