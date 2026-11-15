"""Top-level orchestrator: runs both scenario assessments and attaches
research citations + historical climate context (never used to decide the
Result itself - see research/decision_engine_spec.md sec 6)."""
from datetime import date

import climate

from . import constants as C
from .baseline import assess_baseline
from .mungbean import assess_alternative


def parse_date(value):
    """Parse an ISO date string ('YYYY-MM-DD') to a date, or None.
    Raises ValueError on malformed input - the API layer turns that into a 400."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def relevant_months(start_date, end_date):
    """Calendar months (1-12) spanning start_date..end_date, for scoping the
    concise climate summary to the window actually relevant to a scenario."""
    if start_date is None or end_date is None:
        return None
    months = set()
    cursor = date(start_date.year, start_date.month, 1)
    end_marker = date(end_date.year, end_date.month, 1)
    guard = 0
    while cursor <= end_marker and guard < 36:
        months.add(cursor.month)
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)
        guard += 1
    return sorted(months) if months else None


def attach_supporting_data(assessment, scenario_key, months, soil_test):
    assessment["supporting_data"] = {
        "research_sources": climate.scenario_sources(scenario_key),
        "climate_context": climate.concise_climate_summary(months),
        "district_static_context": climate.district_static_context(),
        "farm_soil_test": soil_test or None,
    }
    return assessment


def run_assessment(payload):
    wheat_sow_date = parse_date(payload.get("wheat_sow_date"))
    wheat_harvest_date = parse_date(payload.get("wheat_harvest_date"))
    rice_transplant_date = parse_date(payload.get("rice_transplant_date"))
    mungbean_sow_date = parse_date(payload.get("mungbean_sow_date"))

    irrigation_source = payload.get("irrigation_source") or "unknown"
    irrigation_available = payload.get("irrigation_available") or "unknown"
    safety_buffer_days = payload.get("safety_buffer_days", C.SAFETY_BUFFER_DAYS_DEFAULT)
    assumed_sow_lag_days = payload.get("assumed_sow_lag_days", C.ASSUMED_SOW_LAG_DAYS_DEFAULT)
    soil_test = payload.get("soil_test")

    baseline = assess_baseline(wheat_sow_date, wheat_harvest_date)
    alternative = assess_alternative(
        wheat_harvest_date,
        rice_transplant_date,
        mungbean_sow_date,
        safety_buffer_days=safety_buffer_days,
        assumed_sow_lag_days=assumed_sow_lag_days,
        irrigation_source=irrigation_source,
        irrigation_available=irrigation_available,
    )

    baseline["scenario"] = "baseline"
    baseline["scenario_name"] = "Basmati rice -> wheat"
    attach_supporting_data(
        baseline, "baseline", relevant_months(wheat_sow_date, wheat_harvest_date), soil_test
    )

    alternative["scenario"] = "alternative"
    alternative["scenario_name"] = "Basmati rice -> wheat -> mungbean -> next rice"
    attach_supporting_data(
        alternative, "alternative", relevant_months(wheat_harvest_date, rice_transplant_date), soil_test
    )

    return {
        "inputs_received": {
            "wheat_sow_date": wheat_sow_date.isoformat() if wheat_sow_date else None,
            "wheat_harvest_date": wheat_harvest_date.isoformat() if wheat_harvest_date else None,
            "rice_transplant_date": rice_transplant_date.isoformat() if rice_transplant_date else None,
            "mungbean_sow_date": mungbean_sow_date.isoformat() if mungbean_sow_date else None,
            "irrigation_source": irrigation_source,
            "irrigation_available": irrigation_available,
            "safety_buffer_days": safety_buffer_days,
            "assumed_sow_lag_days": assumed_sow_lag_days,
        },
        "baseline": baseline,
        "alternative": alternative,
    }
