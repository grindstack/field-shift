# Field Shift

A transparent, rule-based crop rotation decision-support tool for a pilot
district in Punjab, Pakistan. Built for NASA Space Apps.

## Project overview

Field Shift compares two crop rotation plans for a rice-wheat field in
Sheikhupura district, Punjab, Pakistan, against ten years (2016-2025) of
historical satellite and weather data for the district:

- **Baseline** — basmati rice → wheat (the dominant local rotation)
- **Alternative** — basmati rice → wheat → mungbean → next rice (adds a
  short mungbean catch crop in the fallow window before the next rice
  transplant)

A farmer enters the dates they expect for their field (wheat sowing/harvest,
next rice transplanting, optionally a mungbean sowing date) plus a few
qualitative conditions (irrigation source/availability, optional soil-test
info). A rule-based decision engine checks whether there is enough calendar
time for the mungbean catch crop, compares the baseline's wheat-sowing date
against sourced agricultural guidance, and returns a result for each
scenario with its reasoning, confidence, constraints, and limitations spelled
out — never a bare "yes/no" or a numeric score.

## Problem being addressed

Rice-wheat is the standard rotation in this part of Punjab, but the fallow
window between wheat harvest and the next rice transplant is often long
enough to fit a short-duration legume catch crop (mungbean), which research
suggests can improve soil nitrogen and the following crop's yield. Deciding
whether that window is actually long enough for a *specific* field, on a
*specific* season's dates, is a manual calendar-math exercise that most
farmers and extension workers currently do informally, if at all — and the
supporting agronomic evidence for this district is thin (largely a single
2007-08 trial). Field Shift turns that calendar check into a transparent,
explainable tool rather than a black-box recommendation, and is explicit
about where the underlying evidence is strong, weak, or simply unavailable
(e.g. no crop water-requirement figures in millimeters exist anywhere in the
research used here, so the tool never calculates a water balance).

## Features

- Rule-based decision engine (no machine learning) for two rotation
  scenarios, driven entirely by farmer-supplied dates and documented research
  parameters
- Explicit date validation: missing inputs and contradictory dates (e.g. a
  mungbean sowing date before the wheat harvest date) are reported, never
  silently guessed or corrected
- Every result reports: **Result category, Reasons, Constraints and risks,
  Supporting data, Evidence confidence, Limitations** — not a single
  pass/fail verdict
- Historical climate context (2016-2025) for NASA POWER, IMERG, Landsat NDVI,
  and MODIS LST, clearly labeled as historical observations, never a forecast
- District-level SoilGrids/SRTM context, explicitly labeled as district-level
  (not farm-level) background
- A React dashboard with four pages: project overview, a farmer assessment
  form, side-by-side scenario results (with a visual mungbean-window
  calendar check), and historical climate charts

## NASA and other datasets

| Dataset | Source | Role in this project |
|---|---|---|
| NASA POWER (daily & monthly) | NASA POWER project | Air temperature, humidity, wind, solar radiation, precipitation — historical context |
| GPM IMERG (monthly rainfall) | NASA/JAXA GPM mission | Primary monthly rainfall figure, cross-checked against POWER precipitation |
| Landsat (monthly NDVI) | USGS/NASA Landsat program | Optional vegetation-greenness context — never used as crop identification |
| MODIS (monthly land-surface temperature) | NASA MODIS | Land-surface temperature context — explicitly never treated as air temperature |
| SoilGrids (soil properties) | ISRIC — World Soil Information | District-level soil texture/pH/nitrogen/organic-carbon context (single sample point) |
| SRTM (elevation & slope) | NASA/USGS Shuttle Radar Topography Mission | District-level elevation/slope context (single sample point) |

Agronomic research behind the crop calendars and the mungbean rotation
evidence comes from published trials and Punjab agriculture department/
research institute sources — see `research/crop_reference.md` for the full,
source-tagged bibliography, and the **Data attribution** section below.

## Technology stack

- **Backend:** Python, Flask, Flask-CORS, pandas
- **Frontend:** React 19, Vite, Tailwind CSS v4, React Router, Recharts
- **Data processing:** pandas, NumPy, Matplotlib (preprocessing pipeline)
- **Testing:** pytest (backend unit + API tests)

## Project structure

```
Field-Shift/
├── backend/                  Flask API + rule-based decision engine
│   ├── app.py                 API routes: /api/health, /api/climate, /api/assess
│   ├── climate.py              loads data/processed/*.csv + crop_profiles.json
│   ├── engine/                 decision-engine logic (baseline, mungbean, shared helpers)
│   └── tests/                  pytest suite (engine + API)
├── frontend/                  React + Vite + Tailwind dashboard
│   └── src/
│       ├── pages/               Dashboard, Assessment, Results, Climate
│       ├── components/          shared UI (badges, nav, mungbean-window bar)
│       └── api.js                fetch wrapper for the Flask API
├── data/
│   ├── raw/                     original downloaded datasets (never modified)
│   └── processed/                cleaned datasets the backend reads at runtime
├── scripts/                   preprocessing pipeline (raw → processed)
├── research/                  crop-calendar research + decision-engine spec
├── reports/                   data-quality documentation
└── requirements.txt            dependencies for the preprocessing scripts
```

## Installation

Requires Python 3.11+ and Node.js 18+.

```bash
git clone <this-repository>
cd Field-Shift

# Backend
cd backend
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

The processed datasets in `data/processed/` are already included in this
repository, so the app runs immediately after installing dependencies — you
do **not** need to run the preprocessing pipeline first. If you want to
regenerate `data/processed/` from `data/raw/` (e.g. after editing a raw
file), see **Reproducing the data pipeline** below.

## How to run

### Backend (Flask)

```bash
cd backend
python app.py
```
Serves the API at `http://127.0.0.1:5000`. Run the test suite with:
```bash
python -m pytest -v
```

### Frontend (React)

```bash
cd frontend
npm run dev
```
Serves the dashboard at `http://localhost:5173`. The frontend expects the
backend to be running at `http://127.0.0.1:5000` (override with a
`VITE_API_BASE` environment variable if needed).

### Reproducing the data pipeline (optional)

```bash
pip install -r requirements.txt
python scripts/run_all.py
```
Regenerates everything in `data/processed/` and `reports/` from
`data/raw/`. Nothing in `data/raw/` is ever modified by this pipeline.

## Decision-engine methodology and limitations

The full specification — including the normalized crop-calendar evidence
tables, the mungbean fallow-window calculation, farmer-input requirements,
output categories, and the evidence-confidence rubric — is documented in
[`research/decision_engine_spec.md`](research/decision_engine_spec.md). In
summary:

- **Mungbean fallow-window check:** compares the available days between the
  (farmer-supplied or assumed) mungbean sowing date and the next rice
  transplant date against a 65-70 day sowing-to-pod-picking estimate from a
  single Kala Shah Kaku (KSK) trial, plus a configurable 7-day safety buffer
  (a disclosed modeling assumption, not a research finding).
- **Baseline check:** compares the farmer's wheat sowing date against the
  Punjab Agriculture department's ~20 November guidance (treated as a
  recommendation, not a biological cutoff) and a secondary late-sowing
  allowance.
- **Four output categories:** *Suitable within calendar constraints*,
  *Conditionally feasible*, *Insufficient time window*, *Insufficient
  information*. The alternative (mungbean) scenario is permanently capped at
  *Conditionally feasible* under current evidence — reported irrigation
  availability is a stated condition, never a verified measurement of water
  sufficiency, and never upgrades a result.
- **No water balance, no yield prediction, no invented thresholds.** No
  crop water-requirement figures in millimeters were found in the underlying
  research, so none are calculated or implied anywhere in this tool.
- **Known limitations:** the mungbean rotation evidence rests on a single
  2007-08 trial at one site; the wheat late-sowing cutoff partly relies on a
  secondary/aggregator source of unverified provenance; NDVI, land-surface
  temperature, and soil/terrain figures are district-level historical
  background, not farm-level measurements or forecasts; rice/wheat acreage
  figures disagree across the sources reviewed. See
  `research/crop_reference.md` for the complete evidence log, including
  what is Punjab-wide versus Sheikhupura-specific, and what remains
  unverified.

## Data attribution

- NASA POWER — NASA Langley Research Center POWER Project
- GPM IMERG — NASA/JAXA Global Precipitation Measurement mission
- Landsat — USGS/NASA Landsat program
- MODIS — NASA MODIS Land Surface Temperature product
- SoilGrids — ISRIC — World Soil Information (soilgrids.org)
- SRTM — NASA/USGS Shuttle Radar Topography Mission
- Punjab Crop Reporting Service (CRS), Punjab Agriculture (Extension)
  Department, Rice Research Institute Kala Shah Kaku (AARI), and the
  published agronomic trials and news/leaflet sources cited in
  `research/crop_reference.md` and `research/decision_engine_spec.md`

This project does not claim to have independently verified every source
cited above beyond the cross-checks documented in `research/crop_reference.md`
and `reports/data_quality_report.md`.
