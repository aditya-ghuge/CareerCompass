"""
CareerCompass AI - Business Logic Service Layer
Orchestrates AI analysis, post-processes Granite output, and prepares
the final data structures consumed by the frontend.
"""

import logging
from datetime import datetime

from prompts import build_analysis_prompt
from watsonx import generate_json
from utils import (
    sanitize_profile,
    validate_profile,
    skill_list_from_string,
    current_year,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fallback / default builders — used if model omits a field
# ---------------------------------------------------------------------------

def _ensure_list(value, default=None):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        return [value]
    return default or []


def _ensure_dict(value, default=None):
    if isinstance(value, dict):
        return value
    return default or {}


def _ensure_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ensure_str(value, default=""):
    if isinstance(value, str):
        return value.strip()
    return default


def _normalize_career_recommendation(raw: dict) -> dict:
    """Normalize and sanitize the career_recommendation section."""
    cr = _ensure_dict(raw.get("career_recommendation"))
    return {
        "primary_career": _ensure_str(cr.get("primary_career"), "Software Engineer"),
        "career_category": _ensure_str(cr.get("career_category"), "Technology"),
        "match_score": max(0, min(100, _ensure_int(cr.get("match_score"), 75))),
        "confidence_score": max(0, min(100, _ensure_int(cr.get("confidence_score"), 72))),
        "confidence_explanation": _ensure_str(cr.get("confidence_explanation")),
        "why_this_career": _ensure_str(cr.get("why_this_career")),
        "market_demand": _ensure_str(cr.get("market_demand"), "High"),
        "avg_salary_entry": _ensure_int(cr.get("avg_salary_entry"), 65000),
        "avg_salary_mid": _ensure_int(cr.get("avg_salary_mid"), 95000),
        "avg_salary_senior": _ensure_int(cr.get("avg_salary_senior"), 130000),
        "avg_salary_lead": _ensure_int(cr.get("avg_salary_lead"), 170000),
        "job_growth_percent": _ensure_int(cr.get("job_growth_percent"), 22),
        "future_scope": _ensure_str(cr.get("future_scope")),
    }


def _normalize_skill_analysis(raw: dict, profile: dict) -> dict:
    """Normalize skill_analysis, falling back to profile skills."""
    sa = _ensure_dict(raw.get("skill_analysis"))
    profile_skills = skill_list_from_string(profile.get("skills", ""))

    existing = _ensure_list(sa.get("existing_skills"), profile_skills)
    required = _ensure_list(sa.get("required_skills"), [])
    gap = _ensure_list(sa.get("skill_gap"), [])
    radar = _ensure_dict(sa.get("radar_scores"), {})

    default_radar = {
        "technical_skills": 50,
        "problem_solving": 50,
        "communication": 50,
        "industry_knowledge": 40,
        "project_experience": 35,
        "soft_skills": 55,
    }
    for k, v in default_radar.items():
        if k not in radar:
            radar[k] = v
        else:
            radar[k] = max(0, min(100, _ensure_int(radar[k], v)))

    return {
        "existing_skills": existing,
        "required_skills": required,
        "skill_gap": gap,
        "skill_gap_reasons": _ensure_dict(sa.get("skill_gap_reasons")),
        "strengths": _ensure_list(sa.get("strengths"), existing[:3]),
        "strength_explanations": _ensure_dict(sa.get("strength_explanations")),
        "radar_scores": radar,
    }


def _normalize_certifications(raw: dict) -> list:
    certs = _ensure_list(raw.get("certifications"))
    normalized = []
    for c in certs[:10]:
        if not isinstance(c, dict):
            continue
        normalized.append({
            "name": _ensure_str(c.get("name"), "Certification"),
            "provider": _ensure_str(c.get("provider"), "Online Platform"),
            "level": _ensure_str(c.get("level"), "Intermediate"),
            "duration": _ensure_str(c.get("duration"), "3 months"),
            "cost": _ensure_str(c.get("cost"), "Varies"),
            "difficulty": _ensure_str(c.get("difficulty"), "Medium"),
            "skills_gained": _ensure_list(c.get("skills_gained")),
            "why_important": _ensure_str(c.get("why_important")),
            "url_hint": _ensure_str(c.get("url_hint")),
        })
    return normalized


def _normalize_learning_resources(raw: dict) -> dict:
    lr = _ensure_dict(raw.get("learning_resources"))

    books = []
    for b in _ensure_list(lr.get("books"))[:6]:
        if not isinstance(b, dict):
            continue
        books.append({
            "title": _ensure_str(b.get("title"), "Book"),
            "author": _ensure_str(b.get("author"), "Author"),
            "why_read": _ensure_str(b.get("why_read")),
            "difficulty": _ensure_str(b.get("difficulty"), "Intermediate"),
        })

    youtube = []
    for y in _ensure_list(lr.get("youtube_channels"))[:6]:
        if not isinstance(y, dict):
            continue
        youtube.append({
            "channel_name": _ensure_str(y.get("channel_name"), "Channel"),
            "focus_area": _ensure_str(y.get("focus_area")),
            "why_watch": _ensure_str(y.get("why_watch")),
        })

    # New: platform-specific learning resources
    platforms = []
    for pl in _ensure_list(lr.get("platforms"))[:12]:
        if not isinstance(pl, dict):
            continue
        platforms.append({
            "name": _ensure_str(pl.get("name"), "Platform"),
            "resource_title": _ensure_str(pl.get("resource_title"), "Learning Resource"),
            "url": _ensure_str(pl.get("url"), ""),
            "description": _ensure_str(pl.get("description")),
            "is_free": bool(pl.get("is_free", False)),
        })

    courses = []
    for co in _ensure_list(lr.get("online_courses"))[:6]:
        if not isinstance(co, dict):
            continue
        courses.append({
            "title": _ensure_str(co.get("title"), "Course"),
            "platform": _ensure_str(co.get("platform"), "Online"),
            "instructor": _ensure_str(co.get("instructor"), "Instructor"),
            "duration": _ensure_str(co.get("duration"), "Self-paced"),
            "why_take": _ensure_str(co.get("why_take")),
        })

    return {
        "books": books,
        "youtube_channels": youtube,
        "platforms": platforms,
        "online_courses": courses,
    }


def _normalize_projects(raw: dict) -> dict:
    projects_raw = _ensure_dict(raw.get("projects"))
    result = {}
    for level in ("beginner", "intermediate", "advanced"):
        level_projects = []
        for p in _ensure_list(projects_raw.get(level))[:6]:
            if not isinstance(p, dict):
                continue
            level_projects.append({
                "title": _ensure_str(p.get("title"), "Project"),
                "difficulty": _ensure_str(p.get("difficulty"), level.capitalize()),
                "description": _ensure_str(p.get("description")),
                "skills_learned": _ensure_list(p.get("skills_learned")),
                "technologies": _ensure_list(p.get("technologies")),
                "estimated_time": _ensure_str(p.get("estimated_time"), "2–4 weeks"),
                "expected_outcome": _ensure_str(p.get("expected_outcome")),
            })
        result[level] = level_projects
    return result


def _normalize_roadmap(raw: dict) -> dict:
    roadmap_raw = _ensure_dict(raw.get("roadmap"))
    phases = {}
    phase_keys = ["phase_1", "phase_2", "phase_3", "phase_4"]
    durations = ["Month 1–3", "Month 4–6", "Month 7–12", "Month 13–24"]
    titles = ["Foundation Building", "Skill Development", "Project Building", "Industry Readiness"]
    levels = ["Beginner", "Intermediate", "Advanced", "Expert"]

    for i, key in enumerate(phase_keys):
        p = _ensure_dict(roadmap_raw.get(key))
        phases[key] = {
            "title": _ensure_str(p.get("title"), titles[i]),
            "level": _ensure_str(p.get("level"), levels[i]),
            "duration": _ensure_str(p.get("duration"), durations[i]),
            "goals": _ensure_list(p.get("goals")),
            "topics": _ensure_list(p.get("topics")),
            "subtopics": _ensure_list(p.get("subtopics")),
            "practical_exercises": _ensure_list(p.get("practical_exercises")),
            "mini_projects": _ensure_list(p.get("mini_projects")),
            "weekly_focus": _ensure_str(p.get("weekly_focus")),
            "monthly_milestone": _ensure_str(p.get("monthly_milestone")),
            "expected_outcome": _ensure_str(p.get("expected_outcome")),
            "study_hours_per_week": _ensure_int(p.get("study_hours_per_week"), 10),
            "key_resources": _ensure_list(p.get("key_resources")),
        }
    return phases


def _normalize_action_plan(raw: dict) -> dict:
    ap = _ensure_dict(raw.get("action_plan"))
    result = {}
    for bucket in ("immediate_actions", "short_term", "long_term"):
        items = []
        for a in _ensure_list(ap.get(bucket))[:5]:
            if not isinstance(a, dict):
                continue
            items.append({
                "action": _ensure_str(a.get("action")),
                "reason": _ensure_str(a.get("reason")),
                "time_to_complete": _ensure_str(a.get("time_to_complete")),
            })
        result[bucket] = items
    return result


def _normalize_career_timeline(raw: dict) -> list:
    timeline = _ensure_list(raw.get("career_timeline"))
    result = []
    for t in timeline[:6]:
        if not isinstance(t, dict):
            continue
        result.append({
            "stage": _ensure_str(t.get("stage"), "Career Stage"),
            "years_from_now": _ensure_int(t.get("years_from_now"), 1),
            "description": _ensure_str(t.get("description")),
            "expected_salary": _ensure_int(t.get("expected_salary"), 60000),
            "key_skills_needed": _ensure_list(t.get("key_skills_needed")),
        })
    return result


def _normalize_related_careers(raw: dict) -> list:
    related = _ensure_list(raw.get("related_careers"))
    result = []
    for r in related[:8]:
        if not isinstance(r, dict):
            continue
        result.append({
            "title": _ensure_str(r.get("title"), "Related Career"),
            "similarity": max(50, min(95, _ensure_int(r.get("similarity"), 65))),
            "description": _ensure_str(r.get("description")),
            "avg_salary": _ensure_int(r.get("avg_salary"), 70000),
            "market_demand": _ensure_str(r.get("market_demand"), "Medium"),
            "required_skills": _ensure_list(r.get("required_skills")),
            "career_progression": _ensure_list(r.get("career_progression")),
            "future_scope": _ensure_str(r.get("future_scope")),
        })
    return result


def _normalize_profile_building(raw: dict) -> dict:
    pb = _ensure_dict(raw.get("profile_building"))
    return {
        "resume_tips": _ensure_list(pb.get("resume_tips")),
        "linkedin_tips": _ensure_list(pb.get("linkedin_tips")),
        "github_tips": _ensure_list(pb.get("github_tips")),
        "portfolio_tips": _ensure_list(pb.get("portfolio_tips")),
    }


def _normalize_internship_strategy(raw: dict) -> dict:
    ist = _ensure_dict(raw.get("internship_strategy"))
    return {
        "readiness_level": _ensure_str(ist.get("readiness_level"), "Getting Ready"),
        "readiness_reason": _ensure_str(ist.get("readiness_reason")),
        "target_companies": _ensure_list(ist.get("target_companies")),
        "preparation_steps": _ensure_list(ist.get("preparation_steps")),
        "best_platforms": _ensure_list(ist.get("best_platforms")),
        "application_tips": _ensure_str(ist.get("application_tips")),
    }


def _normalize_interview_prep(raw: dict) -> dict:
    ip = _ensure_dict(raw.get("interview_preparation"))
    return {
        "focus_areas": _ensure_list(ip.get("focus_areas")),
        "common_questions": _ensure_list(ip.get("common_questions")),
        "technical_topics": _ensure_list(ip.get("technical_topics")),
        "preparation_resources": _ensure_list(ip.get("preparation_resources")),
        "tips": _ensure_str(ip.get("tips")),
    }


# ---------------------------------------------------------------------------
# Main service function
# ---------------------------------------------------------------------------

def analyze_career(raw_profile: dict) -> dict:
    """
    Main entry point: validate → sanitize → call Granite → normalize → return.

    Returns a normalized analysis dict ready for JSON serialization.
    Raises ValueError for invalid profiles, RuntimeError for AI errors.
    """
    # 1. Validate
    is_valid, errors = validate_profile(raw_profile)
    if not is_valid:
        raise ValueError(f"Profile validation failed: {'; '.join(errors)}")

    # 2. Sanitize
    profile = sanitize_profile(raw_profile)
    logger.info("Starting career analysis for: %s", profile["name"])

    # 3. Build prompt
    prompt = build_analysis_prompt(profile)

    # 4. Call Granite
    try:
        raw_result = generate_json(prompt)
    except Exception as exc:
        logger.error("Granite analysis failed: %s", exc)
        raise RuntimeError(f"AI analysis failed: {str(exc)}") from exc

    # 5. Normalize all sections
    analysis = {
        "generated_at": datetime.now().isoformat(),
        "profile": profile,
        "career_recommendation": _normalize_career_recommendation(raw_result),
        "skill_analysis": _normalize_skill_analysis(raw_result, profile),
        "certifications": _normalize_certifications(raw_result),
        "learning_resources": _normalize_learning_resources(raw_result),
        "projects": _normalize_projects(raw_result),
        "roadmap": _normalize_roadmap(raw_result),
        "career_timeline": _normalize_career_timeline(raw_result),
        "action_plan": _normalize_action_plan(raw_result),
        "internship_strategy": _normalize_internship_strategy(raw_result),
        "interview_preparation": _normalize_interview_prep(raw_result),
        "profile_building": _normalize_profile_building(raw_result),
        "related_careers": _normalize_related_careers(raw_result),
        "motivational_message": _ensure_str(
            raw_result.get("motivational_message"),
            f"You're on a great path, {profile['name']}! Keep building on your strengths."
        ),
    }

    logger.info(
        "Analysis complete for %s — Career: %s (Score: %s)",
        profile["name"],
        analysis["career_recommendation"]["primary_career"],
        analysis["career_recommendation"]["match_score"],
    )

    return analysis
