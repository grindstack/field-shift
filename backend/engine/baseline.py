"""
Baseline-scenario assessment: basmati rice -> wheat.

Implements research/decision_engine_spec.md section 7.2. The baseline is never
automatically marked suitable - it is checked against the farmer's own wheat
sowing/harvest dates and the sourced calendar guidance.
"""
from datetime import date

from . import constants as C
from .common import build_result, LIMITATIONS_BASELINE


def assess_baseline(wheat_sow_date, wheat_harvest_date):
    limitations = list(LIMITATIONS_BASELINE)

    # --- missing required inputs (validation_status = missing_inputs) -----
    missing = []
    if wheat_sow_date is None:
        missing.append("expected wheat sowing date")
    if wheat_harvest_date is None:
        missing.append("expected wheat harvest date")
    if missing:
        return build_result(
            result=C.RESULT_INSUFFICIENT_INFO,
            validation_status=C.VALIDATION_MISSING,
            validation_message=f"Missing required input(s): {', '.join(missing)}.",
            reasons=[
                f"Cannot check the wheat sowing date against sourced guidance "
                f"without {', '.join(missing)}. This is common early in the season "
                f"before sowing has happened."
            ],
            constraints=[],
            confidence=C.CONFIDENCE_LOW,
            limitations=limitations,
            calculation={},
        )

    # --- contradictory dates (validation_status = invalid_dates) ----------
    if wheat_harvest_date <= wheat_sow_date:
        return build_result(
            result=C.RESULT_INSUFFICIENT_INFO,
            validation_status=C.VALIDATION_INVALID,
            validation_message=(
                f"Supplied wheat harvest date ({wheat_harvest_date.isoformat()}) is not "
                f"after the supplied wheat sowing date ({wheat_sow_date.isoformat()}) - "
                f"please confirm both dates."
            ),
            reasons=["Dates are contradictory and were not auto-corrected."],
            constraints=[],
            confidence=C.CONFIDENCE_LOW,
            limitations=limitations,
            calculation={},
        )

    implied_duration_days = (wheat_harvest_date - wheat_sow_date).days
    primary_cutoff = date(wheat_sow_date.year, *C.WHEAT_SOWING_PRIMARY_CUTOFF_MONTH_DAY)
    late_cutoff = date(wheat_sow_date.year, *C.WHEAT_SOWING_LATE_CUTOFF_MONTH_DAY)

    calculation = {
        "wheat_sow_date": wheat_sow_date.isoformat(),
        "wheat_harvest_date": wheat_harvest_date.isoformat(),
        "implied_field_duration_days": implied_duration_days,
        "primary_dept_cutoff": primary_cutoff.isoformat(),
        "secondary_late_sowing_cutoff": late_cutoff.isoformat(),
    }

    duration_min, duration_max = C.WHEAT_FIELD_DURATION_PLAUSIBLE_DAYS
    duration_plausible = duration_min <= implied_duration_days <= duration_max

    reasons = [
        f"Implied field duration from supplied dates: {implied_duration_days} days "
        f"(reference: ~5 months / ~150 days, derived from the single KSK trial - a "
        f"plausibility check, not a strict rule)."
    ]
    constraints = []

    if not duration_plausible:
        result = C.RESULT_INSUFFICIENT_WINDOW
        reasons.append(
            "This duration is far outside the plausible range for a wheat crop in "
            "this zone; treated as an implausible date pair rather than a verified "
            "agronomic limit."
        )
    elif wheat_sow_date <= primary_cutoff:
        result = C.RESULT_SUITABLE
        reasons.append(
            f"Wheat sowing date is on/before the Punjab Agriculture (Extension) "
            f"department's ~20 Nov completion guidance ({primary_cutoff.isoformat()})."
        )
    elif wheat_sow_date <= late_cutoff:
        result = C.RESULT_CONDITIONAL
        reasons.append(
            f"Wheat sowing date is after the department's ~20 Nov guidance but "
            f"within the secondary source's late-sowing allowance (up to "
            f"{late_cutoff.isoformat()})."
        )
        constraints.append(
            "The ~20 Nov guidance is an agricultural recommendation for optimal "
            "timing, not a biological cutoff; sowing after it is not automatically "
            "unsuitable."
        )
        constraints.append(
            "The late-sowing allowance (to ~15 Dec) relies partly on a "
            "secondary/aggregator source of unverified provenance (research "
            "source-quality caveat)."
        )
        constraints.append(
            "Late sowing is a recognized recurring problem in this rice-wheat zone "
            "(yield risk), because rice is often harvested late (Punjab-wide, stated)."
        )
    else:
        result = C.RESULT_INSUFFICIENT_WINDOW
        reasons.append(
            f"Wheat sowing date is after even the secondary source's late-sowing "
            f"cutoff ({late_cutoff.isoformat()}), with no sourced guidance that this "
            f"still works."
        )

    constraints.append(
        "Rice/wheat acreage figures in the underlying research disagree across "
        "sources (e.g. 484,000 vs 587,000 rice acres) - a data-quality caveat, not "
        "specific to this field."
    )

    # Both required dates were farmer-supplied and internally consistent.
    confidence = C.CONFIDENCE_HIGH

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
