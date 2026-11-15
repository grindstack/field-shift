# Field Shift — Decision Engine Specification (v3, ready for implementation)

Status: design spec only. No code, no ML model, no new agricultural thresholds.
Revision: v3 applies final decisions on the baseline wheat-sowing cutoff, the
irrigation cap, the default climate summary content, and date-validation reporting
(see §9 — all prior open items are resolved; no approvals remain outstanding). All
scientific exclusions and PW/SKP/A/U evidence tags from v1/v2 are preserved.

Inputs reviewed: `research/crop_reference.md`, `data/processed/crop_profiles.json`,
`data/processed/master_monthly.csv`, `data/processed/master_monthly_with_static.csv`.
None of those files are modified by this spec.

## 1. Purpose and scope

Define a transparent, rule-based (not statistical/ML) assessment that compares two
rotation scenarios for a Sheikhupura rice-wheat field and reports a calendar-based
feasibility judgment plus supporting context:

- **Baseline**: basmati rice -> wheat
- **Alternative**: basmati rice -> wheat -> mungbean -> next rice

**Cycle interpretation (confirmed)**: one annual cycle — rice transplanted in Kharif
year N-1, wheat sown Rabi N-1/N and harvested in spring of year N, mungbean as a
catch crop in the resulting fallow window in N, then the next rice transplant later
in Kharif N.

The engine answers one question well: *given the dates a farmer expects, is there
enough calendar time to insert mungbean between wheat harvest and the next rice
transplant, and what else should the farmer know before deciding?* It does not
predict yield, does not compute water balance, and does not verify anything by
remote sensing.

## 2. Non-goals (explicit exclusions, per research limitations)

- No crop water balance, no irrigation-sufficiency claim, no mm-based water
  requirement figures — none exist in `crop_profiles.json` (`mm_values: null`
  throughout) or in any raw source reviewed.
- No use of `imerg_image_count`, `ndvi_image_count`, or `lst_image_count` as
  agricultural measurements — they are granule/scene counts (data-coverage
  metadata only; see §6).
- No treatment of `ndvi_mean_ndvi` as crop identification or crop health
  verification for a specific field.
- No treatment of `lst_mean_lst_c` as air temperature.
- No treatment of SoilGrids/SRTM district (single-point) values as a farm-level
  soil or terrain measurement.
- No invented sowing/harvest dates where the research only gives a broad window or
  a single-trial point estimate.
- No agricultural thresholds (heat stress, frost, drought) not present in the
  research files.
- No presentation of historical climate statistics as a forecast (§6).

## 3. Normalized crop calendar (structured windows)

Each entry is a *reference window*, not a prediction for any specific field. Every
value carries its original tag: **scope** (PW = Punjab-wide, SKP = Sheikhupura-
specific), **confidence** (stated / derived / unverified), and its source. Broad
seasonal windows stay broad — they are not narrowed into point dates.

### Basmati rice

| Stage | Window / point estimate | Scope | Confidence | Source |
|---|---|---|---|---|
| Nursery sowing | not before ~20 May | PW | stated | crop_reference.md |
| Transplanting | should finish by ~mid-July (grain quality) | PW | stated | crop_reference.md |
| Transplanting (point) | 1 July (Super Basmati) | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Harvest | early-maturing varieties: 1st week Nov; older varieties: 3rd week Nov | PW | stated | crop_reference.md |
| Harvest (point) | before 18 Nov | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Field duration | ~3.5–4.5 months | PW/SKP | **derived (A)**, not measured | crop_reference.md |

No primary department source for an exact basmati nursery/transplant calendar was
found — treat any date more precise than the windows above as **(U)**.

### Wheat

| Stage | Window / point estimate | Scope | Confidence | Source |
|---|---|---|---|---|
| Sowing (primary) | complete irrigated sowing by ~20 Nov | PW | stated, primary dept (Nov 2026) | Tribune/APP |
| Sowing (secondary) | optimum ~1–25 Nov by zone; late sowing to 15 Dec | PW | secondary/aggregator, unverified provenance | agrinfobank leaflet |
| Sowing (point) | 16 Nov | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Harvest | mid-Apr to end-May (plains) | PW | stated | crop_reference.md |
| Harvest (point) | 3rd week of April | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Field duration | ~5 months | SKP | **derived (A)** from the KSK point dates | crop_reference.md |

Note: wheat sowing (Nov/Dec) and wheat harvest (Apr/May) straddle a calendar-year
boundary. All wheat dates handled by the engine must be full dates (year + month +
day) — see §4.3 on year-crossing arithmetic.

Known real-world skew: late rice harvest commonly pushes wheat sowing later than the
department-urged date (PW, stated) — the engine must treat the farmer's *expected*
wheat sowing/harvest dates as the operative input whenever provided, not the generic
window.

### Mungbean

| Stage | Window / point estimate | Scope | Confidence | Source |
|---|---|---|---|---|
| Spring sowing | 15 Feb – 15 Mar | PW | stated | AARI Pulses leaflets |
| Kharif sowing | June – July | PW | stated | AARI Pulses leaflets |
| Catch-crop sowing (point) | 4th week April (~1 week after wheat harvest) | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Catch-crop pod-picking (point) | end of June | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Duration (used in calc) | **65–70 days, sowing to pod-picking** | SKP | stated, single trial (KSK) | Ali et al. 2012 |
| Duration (other genotypes, context only) | 56–91 days general; 80–95 days NIAB lines | PW/mixed | stated, not Sheikhupura-specific | crop_reference.md |

**On the 65–70 day figure (decision 6)**: this is the KSK trial's reported
sowing-to-pod-picking span, used here purely as a **calendar-screening estimate** —
it tells us whether there is plausibly enough time in the gap, not that a crop
sown there is guaranteed to reach full maturity, dry-seed harvest, or any particular
yield. The engine must never present it as a completion guarantee.

## 4. Mungbean feasibility calculation

### 4.1 Inputs

| Input | Source | Required? |
|---|---|---|
| `wheat_harvest_date` | farmer (actual or expected) | required |
| `mungbean_sow_date` | farmer-supplied actual/expected date **preferred**; if not supplied, derived as `wheat_harvest_date + assumed_sow_lag_days` | derived if not supplied — see disclosure rule below |
| `mungbean_duration_days` | fixed research value, 65–70 days, sowing-to-pod-picking (KSK) | fixed, not user-editable |
| `next_rice_transplant_date` | farmer (actual or expected) | required |
| `safety_buffer_days` | **modeling assumption, not a research finding**. Default **7 days**. Configurable. | has a default, overridable |
| `assumed_sow_lag_days` | **optional suggested modeling default, 7 days**, taken from the single KSK observation ("sown one week after wheat harvest"). Used only as a fallback. | has a default, overridable, farmer value always preferred |

**Disclosure rule**: every assessment must state explicitly whether
`mungbean_sow_date` was farmer-supplied or assumed (and if assumed, state the lag
value used). This feeds directly into the §8 evidence-confidence rating.

### 4.2 Arithmetic (plain language, no code)

1. Validate dates first — see §4.3. If validation fails, stop and report per §4.3;
   do not proceed to classification with invalid data.
2. If `mungbean_sow_date` is not supplied, derive it as
   `wheat_harvest_date + assumed_sow_lag_days` and record it as assumed.
3. `available_window_days` = days between `mungbean_sow_date` and
   `next_rice_transplant_date`.
4. `required_days_minimum` = 65 (lower bound of the KSK range).
5. `required_days_with_buffer` = 70 (upper bound of the KSK range) +
   `safety_buffer_days` (default 70 + 7 = 77).
6. Classification:
   - **Sufficient** — `available_window_days >= required_days_with_buffer`
   - **Insufficient** — `available_window_days < required_days_minimum`
   - **Uncertain** — `required_days_minimum <= available_window_days <
     required_days_with_buffer`

This three-way result feeds §7's category mapping; it is not the final reported
Result by itself.

### 4.3 Date validation rules

Applied before any classification, on both farmer-supplied and derived dates, and
on the baseline's wheat sowing/harvest pair (§7.2) using the same principle:

- `mungbean_sow_date` must not precede `wheat_harvest_date`. A supplied mungbean
  sowing date earlier than the wheat harvest date is **contradictory input**, not a
  calendar-feasibility finding.
- `next_rice_transplant_date` must be strictly after `mungbean_sow_date`. A
  transplant date on or before the mungbean sowing date is contradictory input.
- For the baseline, a supplied wheat harvest date on or before the supplied wheat
  sowing date is likewise contradictory input.
- All dates must be full calendar dates (year + month + day). Because wheat sowing
  and harvest straddle a year boundary (§3), interval arithmetic must use full dates,
  never month/day comparisons that assume a single calendar year.
- **Contradictory or invalid dates are reported, never silently corrected.** The
  engine must not guess which date the farmer "really meant."

**`validation_status` field**: every assessment carries a `validation_status` value,
separate from and alongside the main Result (§7–§8):

| `validation_status` | Meaning |
|---|---|
| `valid` | all required dates for this scenario were supplied (or validly derived, §4.1) and are internally consistent |
| `missing_inputs` | one or more required dates (§5) were not supplied; no contradiction found in what *was* supplied |
| `invalid_dates` | dates were supplied but are contradictory (e.g. mungbean sowing precedes wheat harvest, or wheat harvest precedes wheat sowing) |

`missing_inputs` and `invalid_dates` both drive the Result to **Insufficient
information** (§7), but `validation_status` lets the output distinguish *why* — "we
need more information" vs. "the information given conflicts with itself." Every
non-`valid` status must include a human-readable explanation naming the specific
dates and the conflict or gap (e.g., "supplied mungbean sowing date [X] precedes the
supplied wheat harvest date [Y] — please confirm both dates").

### 4.4 What this calculation deliberately does not do

- It does not check irrigation availability during the mungbean window. Irrigation
  is a separate, qualitative input that never upgrades a result on its own — see §7.
- It does not adjust the 65–70 day figure for temperature, soil, or variety — no
  such adjustment is sourced.
- It does not claim the 65–70 day figure guarantees full crop maturity or harvest
  (§3) — it is a screening estimate for calendar fit only.
- It does not estimate yield or return on the mungbean catch crop — the KSK trial's
  yield figures are reported as supporting context only (§8), never as a predicted
  outcome for a new field.

## 5. Farmer inputs required for a meaningful assessment

| Input | Why it's needed | If missing |
|---|---|---|
| Expected wheat sowing date | anchors the baseline's own calendar-fit check against the sourced wheat-sowing windows (§3, §7.2) | baseline cannot be fully assessed; see §7.2 for the effect on its Result/confidence |
| Expected wheat harvest date | anchors the mungbean fallow-window calculation (§4) and the baseline's harvest-fit check | alternative scenario calculation cannot run (→ Insufficient information); baseline confidence drops |
| Expected (next) rice transplanting date | the other end of the mungbean fallow window; also relevant to how the next cycle's rice start is framed | alternative scenario calculation cannot run (→ Insufficient information) |
| Expected mungbean sowing date (optional) | if supplied, replaces the assumed 7-day-after-harvest default and raises evidence confidence (§8) | engine falls back to the disclosed assumed default (§4.1) |
| Irrigation availability / source during Apr–Jun | the UCC canal is summer-only in this area (PW, stated); mungbean's April–June slot likely needs tubewell/groundwater, not canal water | treated as an unresolved constraint, reported but never scored pass/fail (§7) |
| Known farm soil-test results (optional) | lets the assessment note farm-specific pH/texture instead of only the single SoilGrids district point | soil context stays at the district (SKP) level and is labeled as such, never presented as farm-level |

If wheat harvest date or rice transplant date is missing, the alternative scenario's
§4 calculation cannot run and must report **Insufficient information**. The baseline
scenario can still be partially assessed on whatever dates are available, at reduced
confidence (§7.2, §8).

## 6. Role of the historical climate/static datasets

None of these datasets drive a pass/fail Result on their own. They supply
**contextual background** attached to the Supporting-data/Limitations fields of an
assessment (§8).

**Presentation rule**: by default, show a *concise* historical summary for the
calendar months spanning the farmer's dates, not the full monthly time series.
Detailed monthly figures are available as an optional, explicit expansion, not shown
by default. Every climate figure shown — concise or detailed — must be labeled with
its historical period, **2016–2025**, and must never be presented as a forecast,
prediction, or farm-level measurement.

**Default concise summary content** (fixed for v1):

1. **Historical monthly rainfall** — IMERG (`imerg_rainfall_mm`) as the primary
   figure, with NASA POWER precipitation (`power_prectotcorr`) shown alongside as an
   independent comparison figure where useful (two independently-derived rainfall
   estimates, shown side by side — not averaged or reconciled into one number).
2. **Historical mean air temperature** — NASA POWER (`power_t2m`), explicitly
   labeled as air temperature.
3. **Historical land-surface temperature** — MODIS (`lst_mean_lst_c`), explicitly
   labeled as *land-surface* temperature, kept visually/textually distinct from the
   POWER air-temperature figure above (§2: never implied to be air temperature).
4. **NDVI** — optional, supporting vegetation-greenness context only
   (`ndvi_mean_ndvi`). Not part of the required default three; may be shown
   alongside them but always labeled as general district vegetation-greenness
   context, never as confirmation of a specific crop or field condition (§2).

All four, when shown, are historical 2016–2025 figures only. `image_count` columns
are never part of this summary (§2).

| Dataset | File(s) | Role | Explicit restriction |
|---|---|---|---|
| NASA POWER daily/monthly | `power_daily_clean.csv`, `power_monthly_clean.csv` (`power_*` cols in master) | background on typical temperature/humidity/wind/solar/rainfall for the calendar months in play, 2016–2025 | not used to compute crop water balance or stress thresholds; not a forecast |
| IMERG monthly rainfall | `imerg_rainfall_mm` in master | background on historical monthly rainfall accumulation for the months in play, 2016–2025 | `imerg_image_count` excluded from all agricultural use (coverage metadata only) |
| Landsat NDVI monthly | `ndvi_mean_ndvi` in master | background on the district's historical vegetation-greenness cycle for the relevant months, 2016–2025 | never crop identification or confirmation that a specific crop is/was planted; `ndvi_image_count` excluded as a measurement |
| MODIS LST monthly | `lst_mean_lst_c` in master | background on the district's historical land-surface thermal cycle for the relevant months, 2016–2025 | never treated as air temperature; `lst_image_count` excluded as a measurement |
| SoilGrids static | `soil_clean.csv` + derived columns in `master_monthly_with_static.csv` | district-level soil texture/pH/N/SOC context (single sample point) | never presented as the farmer's own field's soil; farmer soil test (§5) takes precedence when supplied |
| SRTM static | `srtm_clean.csv` + same master file | district-level elevation/slope context | the known slope_max/slope_mean outlier (48.5° vs 2.1°, flagged in the data-quality pass) is carried forward as a caveat, not used as if representative of the field |

## 7. Output categories

Four fixed categories, applied per scenario:

- **Suitable within calendar constraints** — calendar dates fit the sourced
  windows (or clear the §4 buffer) without relying on unverified or single-trial
  figures alone, **and** without any open, unverified dependency (e.g. irrigation)
  being the deciding factor.
- **Conditionally feasible** — the calendar check is favorable but depends on a
  named condition the engine cannot verify itself (irrigation status, §4 result =
  Uncertain, or reliance on a single-trial SKP figure / broad PW window instead of a
  farmer-specific date).
- **Insufficient time window** — §4 classification = Insufficient, or the farmer's
  supplied dates fall clearly outside every sourced window with no plausible fit.
- **Insufficient information** — required farmer inputs (§5) are missing, or
  supplied dates are contradictory/invalid (§4.3), so no calendar check could be
  completed.

### 7.1 Alternative scenario mapping

| §4.2 signal | Category |
|---|---|
| Sufficient | **Conditionally feasible** — irrigation for the Apr–Jun mungbean window is never independently verified against a water-balance figure (§2), so a reported or unknown irrigation source cannot by itself award "Suitable." |
| Uncertain | Conditionally feasible |
| Insufficient | Insufficient time window |
| dates invalid/contradictory (§4.3) or required dates missing | Insufficient information |

**Final for v1**: the alternative scenario cannot reach "Suitable within calendar
constraints" — it is capped at "Conditionally feasible," because its calendar fit
always carries an unverified irrigation dependency for the Apr–Jun mungbean window.
There is **no irrigation-sufficiency escape hatch in v1**: a farmer reporting
irrigation as available does not change this cap, because that report is a stated
condition, not a verified water-sufficiency measurement (no mm-based water balance
exists, §2). This is a deliberate, disclosed, fixed design choice for v1, not an
oversight.

### 7.2 Baseline scenario assessment (decision 7)

The baseline is **not** automatically marked suitable. It is assessed by comparing
the farmer's expected wheat sowing date and expected wheat harvest date against the
sourced windows in §3, using the **primary Punjab Agriculture (Extension) department
guidance (~20 Nov completion) as the main reference cutoff** (decision, final for
v1). This cutoff is treated as an **agricultural recommendation for optimal timing,
not a universal biological cutoff** — sowing after it is not automatically
impossible or unsuitable; it moves the assessment into the "Conditionally feasible"
zone described below. The secondary ~1–25 Nov optimum / ~15 Dec late-sowing guidance
is retained as **supporting context only**, shown with its source-quality caveat
(secondary/aggregator source, unverified provenance, §3) rather than used as the
primary decision boundary.

- **Suitable within calendar constraints** — both wheat sowing and harvest dates
  are supplied, the sowing date is on or before the primary department's ~20 Nov
  guidance, and the harvest date is consistent with the mid-Apr–end-May window.
- **Conditionally feasible** — both dates are supplied, but sowing falls after the
  ~20 Nov primary guidance and up to the secondary source's ~15 Dec late-sowing
  cutoff. This is disclosed as a departure from the department's recommended
  optimal timing (not a biological impossibility), carrying the recurring
  late-sowing yield risk and the secondary source's quality caveat as disclosed
  constraints (§3, §8).
- **Insufficient time window** — sowing date is supplied but falls after even the
  ~15 Dec late-sowing cutoff, or the supplied sowing/harvest pair implies an
  implausible field duration against §3's ~5-month reference, with no sourced
  support that this still works.
- **Insufficient information** — wheat sowing date and/or harvest date is not
  supplied (`validation_status = missing_inputs`, §4.3), or the supplied dates are
  contradictory (`validation_status = invalid_dates`). Missing dates are expected to
  be common early in the season (before sowing has happened) and are reported as
  such, not treated as a negative finding.

Missing wheat sowing information specifically means the baseline cannot be checked
against the sourced sowing windows at all: its Result defaults to "Insufficient
information" and its evidence confidence (§8) cannot exceed Low until that date is
provided.

## 8. Required structure of every assessment

Each scenario assessment (baseline, alternative) must report all seven fields
below. None may be omitted even when the Result is "Insufficient information."

1. **Result** — one of the four §7 categories.
2. **`validation_status`** — `valid` / `missing_inputs` / `invalid_dates` (§4.3),
   with a human-readable explanation whenever it is not `valid`. Reported
   independently of Result so the output distinguishes "need more information" from
   "the information given conflicts with itself."
3. **Reasons** — the specific calculated facts behind the Result (e.g. "available
   window = 46 days; KSK duration 65–70 days; buffer 7 days -> required 77 days ->
   Insufficient"; or, for invalid input, "supplied mungbean sowing date precedes
   supplied wheat harvest date").
4. **Constraints and risks** — non-calendar factors pulled from the research, not
   computed: canal is summer-only / groundwater dependence for the Apr–Jun gap
   (reported irrigation access is **never** treated as proof of sufficient water —
   no water balance is calculated, §2; no escape hatch exists in v1, §7.1),
   declining water tables (rice districts generally), single-season single-site
   evidence for the KSK rotation trial, no farmer-adoption data for mungbean in
   Sheikhupura, wheat sowing-window source-quality caveat, late-sowing yield risk
   (for the baseline, disclosed as a recommendation departure, not a cutoff, §7.2).
5. **Supporting data** — which specific research entries and climate-dataset
   columns were used, each tagged with scope (PW/SKP) and confidence. By default,
   the fixed four-part concise climate summary from §6 (IMERG rainfall vs. POWER
   precipitation comparison, POWER mean air temperature, MODIS land-surface
   temperature, optional NDVI greenness context), all labeled 2016–2025, with
   detailed monthly figures available only as an explicit optional expansion; never
   presented as a forecast or farm-level measurement.
6. **Evidence confidence** — High / Medium / Low, per the fixed rubric below
   (decision 4). This rates the **strength of the evidence used**, not whether the
   scenario is favorable — a well-evidenced "Insufficient time window" is reported
   at High confidence, and a poorly-evidenced "Conditionally feasible" at Low.
   - **High** — key dates (including mungbean sowing) are farmer-supplied, and the
     feasibility result does not depend on generic calendar assumptions (the
     assumed sow-lag default, broad PW windows, or single-trial substitution).
   - **Medium** — one or more dates rely on a disclosed default (e.g. the assumed
     7-day sow lag) or on broad Punjab-wide guidance rather than a farmer-specific
     date.
   - **Low** — important dates are missing or estimated, or the assessment leans
     heavily on single-trial (SKP KSK) or otherwise flagged-uncertain evidence to
     reach its Result.
7. **Limitations** — standing disclaimers restated every time: no water-balance
   calculation performed and reported irrigation access is not verified as
   sufficient; the 65–70 day mungbean figure covers sowing-to-pod-picking in one
   trial, not a guaranteed full lifecycle (§3); NDVI/LST/soil/terrain are
   district-level background (2016–2025 historical, not a forecast), not
   farm-level measurements; mungbean rotation evidence is a single 2007–08 trial;
   wheat sowing-window has one secondary/unverified source; rice/wheat area
   figures in the underlying research disagree across sources.

## 9. Resolution status

All open items from v2 are resolved by the decisions applied in this revision:

1. **Baseline sowing-window cutoff** — resolved. The primary department's ~20 Nov
   guidance is the main Suitable/Conditionally-feasible boundary, treated as an
   agricultural recommendation rather than a biological cutoff; the secondary
   ~1–25 Nov / 15 Dec guidance is retained as supporting context with its
   source-quality caveat (§7.2).
2. **Irrigation escape hatch** — resolved. No escape hatch in v1. The alternative
   scenario is permanently capped at "Conditionally feasible" under current
   evidence; farmer-reported irrigation availability is a disclosed condition, not
   a verified water-sufficiency measurement (§7.1).
3. **Concise climate summary content** — resolved. The default summary is fixed:
   IMERG monthly rainfall with POWER precipitation as a comparison figure, POWER
   mean air temperature, MODIS land-surface temperature (explicitly labeled as
   such), and NDVI as optional supporting vegetation-greenness context — all
   labeled 2016–2025, never a forecast (§6, §8).
4. **Invalid-date reporting detail** — resolved. A separate `validation_status`
   field (`valid` / `missing_inputs` / `invalid_dates`) is now reported alongside
   Result, each with a human-readable explanation; the main Result category stays
   "Insufficient information" for both missing and invalid cases, with
   `validation_status` distinguishing which applies (§4.3, §8).

**No unresolved items remain.** This specification is ready for implementation.
