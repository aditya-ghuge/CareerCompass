"""
CareerCompass AI - Utility Functions
Reusable helpers for validation, sanitization, and common operations.
"""

import re
import logging
import json
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

VALID_YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "Postgraduate", "Alumni"]
VALID_CGPA_RANGE = (0.0, 10.0)


def validate_profile(data: dict) -> tuple[bool, list[str]]:
    """
    Validate the student profile payload.

    Returns (is_valid, list_of_error_messages).
    """
    errors: list[str] = []

    required_fields = {
        "name": "Name",
        "age": "Age",
        "college": "College",
        "branch": "Branch / Major",
        "year": "Current Year",
        "cgpa": "CGPA",
        "skills": "Skills",
        "interests": "Interests",
        "career_goal": "Career Goal",
    }

    for field, label in required_fields.items():
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{label} is required.")

    # Age validation
    try:
        age = int(data.get("age", 0))
        if not (15 <= age <= 60):
            errors.append("Age must be between 15 and 60.")
    except (ValueError, TypeError):
        errors.append("Age must be a valid number.")

    # CGPA validation
    try:
        cgpa = float(data.get("cgpa", -1))
        lo, hi = VALID_CGPA_RANGE
        if not (lo <= cgpa <= hi):
            errors.append(f"CGPA must be between {lo} and {hi}.")
    except (ValueError, TypeError):
        errors.append("CGPA must be a valid decimal number.")

    # Year validation
    year = data.get("year", "")
    if year not in VALID_YEARS:
        errors.append(f"Year must be one of: {', '.join(VALID_YEARS)}.")

    # Skills / interests length
    skills = data.get("skills", "")
    if isinstance(skills, str) and len(skills.strip()) < 3:
        errors.append("Please enter at least one skill.")

    career_goal = data.get("career_goal", "")
    if isinstance(career_goal, str) and len(career_goal.strip()) < 5:
        errors.append("Career Goal must be at least 5 characters.")

    return (len(errors) == 0, errors)


def sanitize_string(value: Any, max_length: int = 500) -> str:
    """Strip, truncate and basic-sanitize a string value."""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    # Remove potential prompt-injection characters
    value = re.sub(r"[{}\[\]\\]", "", value)
    return value[:max_length]


def sanitize_profile(data: dict) -> dict:
    """Return a sanitized copy of the student profile dict."""
    return {
        "name": sanitize_string(data.get("name", ""), 100),
        "age": int(data.get("age", 0)),
        "college": sanitize_string(data.get("college", ""), 200),
        "branch": sanitize_string(data.get("branch", ""), 150),
        "year": sanitize_string(data.get("year", ""), 50),
        "cgpa": float(data.get("cgpa", 0.0)),
        "skills": sanitize_string(data.get("skills", ""), 500),
        "interests": sanitize_string(data.get("interests", ""), 500),
        "career_goal": sanitize_string(data.get("career_goal", ""), 300),
        "additional_guidelines": sanitize_string(data.get("additional_guidelines", ""), 500),
    }


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def safe_json_parse(text: str) -> dict | None:
    """
    Parse JSON returned by the AI model.

    Handles:
    - Raw JSON
    - ```json ... ``` Markdown blocks
    - Extra text before/after JSON
    """

    if not text:
        return None

    text = text.strip()

    # Remove Markdown code fences
    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Try direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting the first complete JSON object using a stack
    start = text.find('{')
    if start != -1:
        stack = []
        for i in range(start, len(text)):
            if text[i] == '{':
                stack.append('{')
            elif text[i] == '}':
                if stack:
                    stack.pop()
                if not stack:  # We found the matching closing brace
                    json_str = text[start:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error during extraction: {e}")
                        break

    logger.warning("Could not parse JSON from model response.")
    return None


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def current_date_str() -> str:
    """Return current date as a readable string."""
    return datetime.now().strftime("%B %d, %Y")


def current_year() -> int:
    """Return current year."""
    return datetime.now().year


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def skill_list_from_string(skills_str: str) -> list[str]:
    """Split a comma/newline separated skills string into a clean list."""
    if not skills_str:
        return []
    # Split on comma or newline
    parts = re.split(r"[,\n]+", skills_str)
    return [p.strip() for p in parts if p.strip()]


def format_duration(hours: int) -> str:
    """Format hours into a human-readable duration."""
    if hours < 1:
        return "< 1 hour"
    if hours < 8:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    days = hours // 8
    remaining = hours % 8
    if remaining == 0:
        return f"{days} day{'s' if days != 1 else ''}"
    return f"{days} day{'s' if days != 1 else ''} {remaining} hr"


def truncate(text: str, max_chars: int = 200) -> str:
    """Truncate text to max_chars, appending ellipsis if needed."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"
