"""
Fixed parameters for the Field Shift decision engine.

Every value here is either a direct research figure (cited in
research/decision_engine_spec.md) or an explicitly-labeled modeling
assumption. Nothing here is an invented agricultural threshold.
"""

# --- Modeling assumptions (not research findings) -------------------------
SAFETY_BUFFER_DAYS_DEFAULT = 7          # spec sec 4.1 - configurable, disclosed
ASSUMED_SOW_LAG_DAYS_DEFAULT = 7        # spec sec 4.1 - fallback only, farmer date preferred

# --- Research figures -------------------------------------------------------
# KSK trial (Ali et al. 2012): mungbean sowing-to-pod-picking span. A calendar
# screening estimate only - not a guarantee of full lifecycle completion.
MUNGBEAN_DURATION_MIN_DAYS = 65
MUNGBEAN_DURATION_MAX_DAYS = 70

# Punjab Agriculture (Extension) dept primary guidance: complete irrigated
# wheat sowing by ~20 Nov. Treated as a recommendation, not a biological cutoff.
WHEAT_SOWING_PRIMARY_CUTOFF_MONTH_DAY = (11, 20)

# Secondary/aggregator source: late sowing allowance up to ~15 Dec.
# Source-quality caveat applies (unverified provenance).
WHEAT_SOWING_LATE_CUTOFF_MONTH_DAY = (12, 15)

# Sanity bound around the ~5-month (derived) wheat field-duration reference
# (research/decision_engine_spec.md sec 3). This is a data-plausibility check,
# not a sourced agronomic limit - it only catches implausible date pairs.
WHEAT_FIELD_DURATION_PLAUSIBLE_DAYS = (100, 220)

IRRIGATION_SOURCES = ["canal", "tubewell", "both", "rainfed", "unknown"]
IRRIGATION_AVAILABILITY = ["available", "not_available", "unknown"]

# --- Output categories (spec sec 7) ----------------------------------------
RESULT_SUITABLE = "Suitable within calendar constraints"
RESULT_CONDITIONAL = "Conditionally feasible"
RESULT_INSUFFICIENT_WINDOW = "Insufficient time window"
RESULT_INSUFFICIENT_INFO = "Insufficient information"

# --- Validation status (spec sec 4.3) ---------------------------------------
VALIDATION_VALID = "valid"
VALIDATION_MISSING = "missing_inputs"
VALIDATION_INVALID = "invalid_dates"

# --- Evidence confidence (spec sec 8) ---------------------------------------
CONFIDENCE_HIGH = "High"
CONFIDENCE_MEDIUM = "Medium"
CONFIDENCE_LOW = "Low"
