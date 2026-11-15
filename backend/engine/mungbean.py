"""
Alternative-scenario assessment: basmati rice -> wheat -> mungbean -> next rice.

Implements research/decision_engine_spec.md sections 4 and 7.1.
"""
from datetime import timedelta

from . import constants as C
from .common import build_result, describe_irrigation, LIMITATIONS_ALTERNATIVE


def assess_alternative(wheat_harvest_date, rice_transplant_date, mungbean_sow_date=None,
                        safety_buffer_days=C.SAFETY_BUFFER_DAYS_DEFAULT,
                        assumed_sow_lag_days=C.ASSUMED_SOW_LAG_DAYS_DEFAULT,
                        irrigation_source="unknown", irrigation_available="unknown"):
    limitations = list(LIMITATIONS_ALTERNATIVE)

    # --- missing required inputs (validation_status = missing_inputs) -----
    missing = []
    if wheat_harvest_date is None:
        missing.append("expected wheat harvest date")
    if rice_transplant_date is None:
        missing.append("expected next rice transplanting date")
    if missing:
        return build_result(
            result=C.RESULT_INSUFFICIENT_INFO,
            validation_status=C.VALIDATION_MISSING,
            validation_message=f"Missing required input(s): {', '.join(missing)}.",
            reasons=[f"Cannot evaluate the mungbean fallow window without {', '.join(missing)}."],
            constraints=[],
            confidence=C.CONFIDENCE_LOW,
            limitations=limitations,
            calculation={},
        )

    mungbean_sow_assumed = mungbean_sow_date is None
    if mungbean_sow_assumed:
        mungbean_sow_date = wheat_harvest_date + timedelta(days=assumed_sow_lag_days)

    # --- contradictory dates (validation_status = invalid_dates) ----------
    # Never silently corrected - reported as-is (spec sec 4.3).
    if mungbean_sow_date < wheat_harvest_date:
        return build_result(
            result=C.RESULT_INSUFFICIENT_INFO,
            validation_status=C.VALIDATION_INVALID,
            validation_message=(
                f"Supplied mungbean sowing date ({mungbean_sow_date.isoformat()}) precedes "
                f"the supplied wheat harvest date ({wheat_harvest_date.isoformat()}) - "
                f"please confirm both dates."
            ),
            reasons=["Dates are contradictory and were not auto-corrected."],
            constraints=[],
            confidence=C.CONFIDENCE_LOW,
            limitations=limitations,
            calculation={},
        )
    if rice_transplant_date <= mungbean_sow_date:
        return build_result(
            result=C.RESULT_INSUFFICIENT_INFO,
            validation_status=C.VALIDATION_INVALID,
            validation_message=(
                f"Supplied next rice transplanting date ({rice_transplant_date.isoformat()}) "
                f"is not after the mungbean sowing date ({mungbean_sow_date.isoformat()}) - "
                f"please confirm both dates."
            ),
            reasons=["Dates are contradictory and were not auto-corrected."],
            constraints=[],
            confidence=C.CONFIDENCE_LOW,
            limitations=limitations,
            calculation={},
        )

    # --- core calculation (spec sec 4.2) -----------------------------------
    available_window_days = (rice_transplant_date - mungbean_sow_date).days
    required_minimum = C.MUNGBEAN_DURATION_MIN_DAYS
    required_with_buffer = C.MUNGBEAN_DURATION_MAX_DAYS + safety_buffer_days

    if available_window_days >= required_with_buffer:
        signal = "sufficient"
    elif available_window_days < required_minimum:
        signal = "insufficient"
    else:
        signal = "uncertain"

    calculation = {
        "wheat_harvest_date": wheat_harvest_date.isoformat(),
        "mungbean_sow_date": mungbean_sow_date.isoformat(),
        "mungbean_sow_date_source": "assumed" if mungbean_sow_assumed else "farmer_supplied",
        "assumed_sow_lag_days": assumed_sow_lag_days if mungbean_sow_assumed else None,
        "next_rice_transplant_date": rice_transplant_date.isoformat(),
        "available_window_days": available_window_days,
        "required_minimum_days": required_minimum,
        "mungbean_duration_range_days": [C.MUNGBEAN_DURATION_MIN_DAYS, C.MUNGBEAN_DURATION_MAX_DAYS],
        "safety_buffer_days": safety_buffer_days,
        "required_with_buffer_days": required_with_buffer,
        "signal": signal,
    }

    reasons = [
        ("Mungbean sowing date was ASSUMED as wheat harvest + "
         f"{assumed_sow_lag_days} days (no farmer date supplied).") if mungbean_sow_assumed
        else "Mungbean sowing date was farmer-supplied.",
        f"Available window between mungbean sowing and next rice transplant: "
        f"{available_window_days} days.",
        "KSK trial estimate: 65-70 days, sowing to pod-picking (a calendar-screening "
        f"estimate, not a lifecycle guarantee). Minimum required: {required_minimum} days. "
        f"Buffered requirement (70 + {safety_buffer_days}-day safety-buffer modeling "
        f"assumption): {required_with_buffer} days.",
    ]
    if signal == "sufficient":
        reasons.append("Available window meets or exceeds the buffered requirement.")
    elif signal == "uncertain":
        reasons.append(
            "Available window exceeds the 65-day minimum but does not clear the "
            "buffered requirement - treated as uncertain, not sufficient."
        )
    else:
        reasons.append("Available window is below the 65-day minimum duration.")

    # --- qualitative constraints (never affect the classification) --------
    constraints = [
        "The Upper Chenab Canal in this area runs only in the summer season; the "
        "Apr-Jun mungbean window likely depends on tubewell/groundwater rather than "
        "canal water (Punjab-wide, stated).",
        describe_irrigation(irrigation_source, irrigation_available),
        "No water balance is calculated and no crop water requirement figures (mm) "
        "exist in the research. Reported irrigation availability is a stated "
        "condition, not a verified measurement of water sufficiency, and never "
        "upgrades this result.",
        "No farmer-adoption data was found for mungbean cultivation in Sheikhupura.",
        "Evidence for this rotation rests on a single 2007-08 KSK trial at one site "
        "and one season; its reported yields (paddy 3.57 vs 3.34 t/ha; mungbean "
        "0.78 t/ha) are context, not a prediction for this field.",
    ]

    # --- map signal -> Result (spec sec 7.1: capped at Conditionally feasible) --
    if signal == "insufficient":
        result = C.RESULT_INSUFFICIENT_WINDOW
    else:  # sufficient or uncertain both cap at Conditionally feasible
        result = C.RESULT_CONDITIONAL

    confidence = C.CONFIDENCE_HIGH if not mungbean_sow_assumed else C.CONFIDENCE_MEDIUM

    return build_result(
        result=result,
        validation_status=C.VALIDATION_VALID,
        validation_message=None,
        reasons=reasons,
        constraints=constraints,
        confidence=confidence,
        limitations=limitations,
        calculation=calculation,
    )
