"""
Field Shift decision-engine API.

Endpoints:
  GET  /api/health
  GET  /api/climate
  POST /api/assess

Run with:  python app.py   (from this backend/ directory)
"""
from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS

import climate
from engine import constants as C
from engine.assess import run_assessment

app = Flask(__name__)
CORS(app)

DATE_FIELDS = ["wheat_sow_date", "wheat_harvest_date", "rice_transplant_date", "mungbean_sow_date"]


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "field-shift-decision-engine"})


@app.get("/api/climate")
def get_climate():
    detail = request.args.get("detail", "false").lower() in ("1", "true", "yes")
    months_param = request.args.get("months")
    month_filter = None
    if months_param:
        try:
            month_filter = [int(m) for m in months_param.split(",") if m.strip()]
            if any(m < 1 or m > 12 for m in month_filter):
                raise ValueError
        except ValueError:
            return jsonify({"error": "invalid 'months' parameter; expected comma-separated integers 1-12"}), 400

    try:
        response = {
            "summary": climate.concise_climate_summary(month_filter),
            "district_static_context": climate.district_static_context(),
        }
        if detail:
            response["detailed_monthly"] = climate.detailed_monthly_series()
        return jsonify(response)
    except FileNotFoundError as exc:
        return jsonify({"error": f"processed dataset not found: {exc}"}), 500


@app.post("/api/assess")
def post_assess():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400

    for field in DATE_FIELDS:
        value = payload.get(field)
        if value is not None and value != "":
            try:
                date.fromisoformat(value)
            except (ValueError, TypeError):
                return jsonify({
                    "error": f"'{field}' must be an ISO date string (YYYY-MM-DD), got: {value!r}"
                }), 400

    irrigation_source = payload.get("irrigation_source")
    if irrigation_source and irrigation_source not in C.IRRIGATION_SOURCES:
        return jsonify({"error": f"'irrigation_source' must be one of {C.IRRIGATION_SOURCES}"}), 400

    irrigation_available = payload.get("irrigation_available")
    if irrigation_available and irrigation_available not in C.IRRIGATION_AVAILABILITY:
        return jsonify({"error": f"'irrigation_available' must be one of {C.IRRIGATION_AVAILABILITY}"}), 400

    for int_field in ("safety_buffer_days", "assumed_sow_lag_days"):
        value = payload.get(int_field)
        if value is not None:
            try:
                int(value)
            except (ValueError, TypeError):
                return jsonify({"error": f"'{int_field}' must be an integer number of days"}), 400

    try:
        result = run_assessment(payload)
        return jsonify(result)
    except FileNotFoundError as exc:
        return jsonify({"error": f"processed dataset not found: {exc}"}), 500
    except Exception as exc:  # defensive: never leak a stack trace to the client
        app.logger.exception("assessment failed")
        return jsonify({"error": "internal error while running the assessment", "detail": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
