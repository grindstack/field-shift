"""
Automated tests for the Field Shift decision engine.

Covers the 10 required scenarios:
 1. Sufficient mungbean window
 2. Uncertain mungbean window
 3. Insufficient mungbean window
 4. Missing required dates
 5. Contradictory dates
 6. Dates crossing calendar years
 7. Farmer-supplied mungbean sowing date
 8. Assumed mungbean sowing date
 9. Wheat sowing after the recommended 20 November date
10. Alternative scenario never upgraded to "Suitable" under current evidence
"""
from datetime import date

from engine import constants as C
from engine.baseline import assess_baseline
from engine.mungbean import assess_alternative


# --------------------------------------------------------------------------
# 1. Sufficient mungbean window
# --------------------------------------------------------------------------
def test_sufficient_mungbean_window():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 7, 15),   # 79 days after the assumed sow date
    )
    assert result["calculation"]["signal"] == "sufficient"
    assert result["calculation"]["available_window_days"] >= result["calculation"]["required_with_buffer_days"]
    # capped at Conditionally feasible, never Suitable (see scenario 10)
    assert result["result"] == C.RESULT_CONDITIONAL
    assert result["validation_status"] == C.VALIDATION_VALID


# --------------------------------------------------------------------------
# 2. Uncertain mungbean window
# --------------------------------------------------------------------------
def test_uncertain_mungbean_window():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 7, 5),    # 69 days after the assumed sow date
    )
    calc = result["calculation"]
    assert calc["signal"] == "uncertain"
    assert calc["required_minimum_days"] <= calc["available_window_days"] < calc["required_with_buffer_days"]
    assert result["result"] == C.RESULT_CONDITIONAL
    assert result["validation_status"] == C.VALIDATION_VALID


# --------------------------------------------------------------------------
# 3. Insufficient mungbean window
# --------------------------------------------------------------------------
def test_insufficient_mungbean_window():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 5, 20),   # 23 days after the assumed sow date
    )
    assert result["calculation"]["signal"] == "insufficient"
    assert result["calculation"]["available_window_days"] < result["calculation"]["required_minimum_days"]
    assert result["result"] == C.RESULT_INSUFFICIENT_WINDOW
    assert result["validation_status"] == C.VALIDATION_VALID


# --------------------------------------------------------------------------
# 4. Missing required dates
# --------------------------------------------------------------------------
def test_missing_required_dates_alternative():
    result = assess_alternative(wheat_harvest_date=None, rice_transplant_date=None)
    assert result["validation_status"] == C.VALIDATION_MISSING
    assert result["result"] == C.RESULT_INSUFFICIENT_INFO
    assert result["calculation"] == {}
    assert "wheat harvest" in result["validation_message"]


def test_missing_required_dates_baseline():
    result = assess_baseline(wheat_sow_date=None, wheat_harvest_date=date(2026, 4, 20))
    assert result["validation_status"] == C.VALIDATION_MISSING
    assert result["result"] == C.RESULT_INSUFFICIENT_INFO
    assert "wheat sowing" in result["validation_message"]


# --------------------------------------------------------------------------
# 5. Contradictory dates (never silently corrected)
# --------------------------------------------------------------------------
def test_contradictory_dates_mungbean_before_harvest():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 7, 5),
        mungbean_sow_date=date(2026, 4, 10),      # before wheat harvest - invalid
    )
    assert result["validation_status"] == C.VALIDATION_INVALID
    assert result["result"] == C.RESULT_INSUFFICIENT_INFO
    assert "precedes" in result["validation_message"]
    # the invalid input must not have been auto-corrected or silently reinterpreted
    assert result["calculation"] == {}


def test_contradictory_dates_transplant_before_sow():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        mungbean_sow_date=date(2026, 4, 27),
        rice_transplant_date=date(2026, 4, 27),   # same day as sowing - invalid
    )
    assert result["validation_status"] == C.VALIDATION_INVALID
    assert result["result"] == C.RESULT_INSUFFICIENT_INFO


def test_contradictory_dates_baseline_harvest_before_sow():
    result = assess_baseline(
        wheat_sow_date=date(2025, 11, 15),
        wheat_harvest_date=date(2025, 11, 1),     # before sowing - invalid
    )
    assert result["validation_status"] == C.VALIDATION_INVALID
    assert result["result"] == C.RESULT_INSUFFICIENT_INFO


# --------------------------------------------------------------------------
# 6. Dates crossing calendar years
# --------------------------------------------------------------------------
def test_dates_crossing_calendar_year_boundary():
    # Wheat sown Nov 2025, harvested Apr 2026 - the normal, expected case.
    result = assess_baseline(
        wheat_sow_date=date(2025, 11, 15),
        wheat_harvest_date=date(2026, 4, 20),
    )
    assert result["validation_status"] == C.VALIDATION_VALID
    assert result["calculation"]["implied_field_duration_days"] == 156
    assert result["calculation"]["implied_field_duration_days"] > 0
    assert result["result"] == C.RESULT_SUITABLE


# --------------------------------------------------------------------------
# 7. Farmer-supplied mungbean sowing date
# --------------------------------------------------------------------------
def test_farmer_supplied_mungbean_sowing_date():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 7, 10),
        mungbean_sow_date=date(2026, 4, 22),      # explicit farmer date, different from the assumed default
    )
    assert result["calculation"]["mungbean_sow_date"] == "2026-04-22"
    assert result["calculation"]["mungbean_sow_date_source"] == "farmer_supplied"
    assert result["calculation"]["assumed_sow_lag_days"] is None
    assert result["evidence_confidence"] == C.CONFIDENCE_HIGH


# --------------------------------------------------------------------------
# 8. Assumed mungbean sowing date
# --------------------------------------------------------------------------
def test_assumed_mungbean_sowing_date():
    result = assess_alternative(
        wheat_harvest_date=date(2026, 4, 20),
        rice_transplant_date=date(2026, 7, 10),
        mungbean_sow_date=None,                   # not supplied -> engine must assume
    )
    assert result["calculation"]["mungbean_sow_date"] == "2026-04-27"  # +7 days default
    assert result["calculation"]["mungbean_sow_date_source"] == "assumed"
    assert result["calculation"]["assumed_sow_lag_days"] == 7
    assert result["evidence_confidence"] == C.CONFIDENCE_MEDIUM
    assert any("ASSUMED" in r for r in result["reasons"])


# --------------------------------------------------------------------------
# 9. Wheat sowing after the recommended 20 November date
# --------------------------------------------------------------------------
def test_wheat_sowing_after_20_nov_is_conditionally_feasible_not_impossible():
    result = assess_baseline(
        wheat_sow_date=date(2025, 11, 28),        # after the ~20 Nov primary guidance
        wheat_harvest_date=date(2026, 4, 25),
    )
    assert result["validation_status"] == C.VALIDATION_VALID
    assert result["result"] == C.RESULT_CONDITIONAL
    assert result["result"] != C.RESULT_INSUFFICIENT_WINDOW
    assert any("recommendation" in c or "not" in c for c in result["constraints_and_risks"])


def test_wheat_sowing_far_past_late_cutoff_is_insufficient():
    result = assess_baseline(
        wheat_sow_date=date(2025, 12, 28),        # past the ~15 Dec late-sowing cutoff
        wheat_harvest_date=date(2026, 5, 15),
    )
    assert result["result"] == C.RESULT_INSUFFICIENT_WINDOW


# --------------------------------------------------------------------------
# 10. Alternative scenario never upgraded to "Suitable" under current evidence
# --------------------------------------------------------------------------
def test_alternative_never_reaches_suitable_even_with_irrigation_available():
    for rice_transplant in (date(2026, 7, 15), date(2026, 7, 5), date(2026, 5, 20)):
        result = assess_alternative(
            wheat_harvest_date=date(2026, 4, 20),
            rice_transplant_date=rice_transplant,
            irrigation_source="canal",
            irrigation_available="available",
        )
        assert result["result"] != C.RESULT_SUITABLE
        assert result["result"] in (C.RESULT_CONDITIONAL, C.RESULT_INSUFFICIENT_WINDOW, C.RESULT_INSUFFICIENT_INFO)
