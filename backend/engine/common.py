"""Shared helpers and standing disclaimers for both scenario assessments."""

LIMITATIONS_ALTERNATIVE = [
    "No crop water balance is calculated anywhere in this assessment; no mm-based "
    "water requirement figures exist in the underlying research.",
    "The 65-70 day mungbean figure covers sowing-to-pod-picking in a single KSK "
    "trial, not a guaranteed full crop lifecycle or harvest.",
    "NDVI, land-surface temperature, and soil/terrain context are district-level "
    "historical background (2016-2025), not farm-level measurements, and are "
    "never a forecast.",
    "Mungbean rotation evidence rests on a single 2007-08 trial at one site and "
    "one season.",
    "There is no irrigation-sufficiency escape hatch: reported irrigation "
    "availability never upgrades this result.",
]

LIMITATIONS_BASELINE = [
    "NDVI, land-surface temperature, and soil/terrain context are district-level "
    "historical background (2016-2025), not farm-level measurements, and are "
    "never a forecast.",
    "Wheat sowing-window guidance partly relies on one secondary/aggregator "
    "source of unverified provenance for its exact late-sowing boundary.",
    "Rice/wheat acreage figures in the underlying research disagree across "
    "sources (484,000 vs 587,000 rice acres; 495,000 vs 561,000 wheat acres).",
]


def build_result(*, result, validation_status, validation_message, reasons,
                  constraints, confidence, limitations, calculation):
    return {
        "result": result,
        "validation_status": validation_status,
        "validation_message": validation_message,
        "reasons": reasons,
        "constraints_and_risks": constraints,
        "evidence_confidence": confidence,
        "limitations": limitations,
        "calculation": calculation,
    }


def describe_irrigation(source, available):
    """Qualitative-only description. Never used to upgrade a result (spec sec 5, 7.1)."""
    source = (source or "unknown").lower()
    available = (available or "unknown").lower()
    label = {
        "canal": "canal",
        "tubewell": "tubewell/groundwater",
        "both": "canal and tubewell/groundwater",
        "rainfed": "rainfed (no reported irrigation source)",
        "unknown": "an unspecified/unknown source",
    }.get(source, "an unspecified/unknown source")

    if available == "available":
        return (f"Farmer reports irrigation access via {label} as available for this "
                f"window. This is a reported condition, not a verified measurement of "
                f"water sufficiency, and does not upgrade this result.")
    if available in ("not_available", "unavailable"):
        return (f"Farmer reports irrigation via {label} as NOT reliably available for "
                f"this window - a disclosed risk, not quantified.")
    return (f"Irrigation availability for this window was not confirmed (reported "
            f"source: {label}; availability: unknown).")
