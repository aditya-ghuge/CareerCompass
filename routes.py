"""
CareerCompass AI - REST API Routes
All endpoints the frontend consumes.
"""

import logging
import json
from flask import Blueprint, request, jsonify, send_file
import io

from services import analyze_career
from pdf import generate_pdf
from utils import validate_profile, sanitize_profile
from watsonx import health_check as watsonx_health

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Helper: standard JSON responses
# ---------------------------------------------------------------------------

def success(data: dict, status: int = 200):
    return jsonify({"success": True, **data}), status


def error(message: str, details=None, status: int = 400):
    payload = {"success": False, "error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint — confirms Flask and optionally watsonx connectivity."""
    watsonx_status = watsonx_health()
    return jsonify({
        "status": "ok",
        "service": "CareerCompass AI",
        "watsonx": watsonx_status,
    })


# ---------------------------------------------------------------------------
# Career Analysis
# ---------------------------------------------------------------------------

@api_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /api/analyze
    Body: student profile JSON
    Returns: full career analysis JSON
    """
    if not request.is_json:
        return error("Request must be JSON (Content-Type: application/json)", status=415)

    data = request.get_json(silent=True)
    if not data:
        return error("Request body is empty or malformed.", status=400)

    # Validate
    is_valid, validation_errors = validate_profile(data)
    if not is_valid:
        return error("Profile validation failed.", details=validation_errors, status=422)

    try:
        analysis = analyze_career(data)
        # NOTE: do not store the full analysis in the Flask session cookie —
        # the JSON can be 5–10KB which exceeds the 4KB cookie limit.
        # The frontend stores it in sessionStorage and sends it back for PDF export.
        return success({"analysis": analysis})

    except ValueError as exc:
        logger.warning("Validation error during analysis: %s", exc)
        return error(str(exc), status=422)

    except RuntimeError as exc:
        logger.error("Runtime error during analysis: %s", exc)
        return error(
            "The AI analysis service encountered an error. Please try again.",
            details=str(exc),
            status=503,
        )

    except Exception as exc:
        logger.exception("Unexpected error during analysis: %s", exc)
        return error("An unexpected error occurred.", status=500)


# ---------------------------------------------------------------------------
# PDF Export
# ---------------------------------------------------------------------------

@api_bp.route("/export/pdf", methods=["POST"])
def export_pdf():
    """
    POST /api/export/pdf
    Body: analysis JSON (same structure returned by /api/analyze)
    Returns: PDF binary with correct headers
    """
    if not request.is_json:
        return error("Request must be JSON.", status=415)

    data = request.get_json(silent=True)
    if not data:
        return error("No analysis data provided. Send the analysis JSON in the request body.", status=400)

    # Accept either a wrapped {"analysis": {...}} or bare analysis dict
    analysis = data.get("analysis", data)

    try:
        pdf_bytes = generate_pdf(analysis)
        profile_name = analysis.get("profile", {}).get("name", "student").replace(" ", "_")
        filename = f"CareerCompass_Report_{profile_name}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except RuntimeError as exc:
        logger.error("PDF generation failed: %s", exc)
        return error("PDF generation failed. Please try again.", details=str(exc), status=500)

    except Exception as exc:
        logger.exception("Unexpected PDF error: %s", exc)
        return error("An unexpected error occurred during PDF generation.", status=500)


# ---------------------------------------------------------------------------
# Validate profile (used for real-time form feedback)
# ---------------------------------------------------------------------------

@api_bp.route("/validate", methods=["POST"])
def validate():
    """
    POST /api/validate
    Body: partial or complete profile JSON
    Returns: validation result
    """
    if not request.is_json:
        return error("Request must be JSON.", status=415)

    data = request.get_json(silent=True) or {}
    is_valid, validation_errors = validate_profile(data)

    return jsonify({
        "valid": is_valid,
        "errors": validation_errors,
    })
