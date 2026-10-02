# Tree Ring Sensitivity Reproduction

This repository is a minimal but paper-like reproduction workflow for studying how tree radial growth sensitivity to precipitation changes over time, inspired by the 2024 GRL study:

- Li, T., et al. (2024). Increasing Sensitivity of Tree Radial Growth to Precipitation. Geophysical Research Letters.

The goal is to quickly validate the core logic:

1. Build a site-level tree ring chronology.
2. Match each site to precipitation and temperature records.
3. Estimate annual sensitivity of growth to precipitation.
4. Examine whether sensitivity increases over time.

## Data sources

- Tree ring: NOAA NCEI / ITRDB
  - https://www.ncei.noaa.gov/products/paleoclimatology/tree-ring
  - https://www.ncei.noaa.gov/pub/data/paleo/treering/
- Climate: NOAA monthly summaries, CRU, GPCC, or ERA5
- CO2: NOAA GML
  - https://gml.noaa.gov/ccgg/trends/

## Minimal dataset workflow

This repository starts with a minimal verification setup:

- 3-10 representative sites
- annual or seasonal precipitation records
- simple sensitivity regression
- rolling-window trend of sensitivity

This is useful before scaling to the full global dataset.

## Folder structure

```text
.
├── data/
│   ├── climate/
│   ├── tree_ring/
│   └── processed/
├── scripts/
│   ├── download_noaa_climate.py
│   └── reproduce_tree_growth_sensitivity.py
├── README.md
└── requirements.txt
```

## Quick start

1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

2. Download climate data for representative stations

```bash
python scripts/download_noaa_climate.py
```

3. Place ITRDB-style tree-ring CSV files under `data/tree_ring/`

Example:

```csv
site_id,year,ring_width
site_01,1950,1.210
site_01,1951,1.180
```

4. Run reproduction workflow

```bash
python scripts/reproduce_tree_growth_sensitivity.py
```

5. Check outputs in `data/processed/`

## Notes

- This script is intentionally simpler than the full paper pipeline.
- The paper likely uses site-level chronology standardization, precipitation anomalies, and multi-variable regression or sliding-window sensitivity estimation.
- To move closer to the published study, extend the workflow with:
  - site-specific detrending
  - seasonal climate anomalies
  - temperature and CO2 controls
  - biome stratification
  - global spatial interpolation

## License

Public research template; use for reproducible analysis and study replication.
