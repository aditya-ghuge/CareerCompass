"""
CareerCompass AI - Prompt Engineering Module
Constructs highly structured prompts for meta-llama/llama-3-3-70b-instruct
on IBM watsonx.ai, using the Llama-3 instruct chat format to produce
consistent, machine-parseable JSON responses.
"""

from utils import skill_list_from_string, current_year


# ---------------------------------------------------------------------------
# Master analysis prompt
# ---------------------------------------------------------------------------

def build_analysis_prompt(profile: dict) -> str:
    """
    Build the full career analysis prompt for meta-llama/llama-3-3-70b-instruct.

    Uses the Llama-3 instruct chat format:
      <|begin_of_text|>
      <|start_header_id|>system<|end_header_id|> ... <|eot_id|>
      <|start_header_id|>user<|end_header_id|> ... <|eot_id|>
      <|start_header_id|>assistant<|end_header_id|>

    The trailing assistant header primes the model to begin its response
    immediately with the JSON object.
    """
    skills_list = skill_list_from_string(profile.get("skills", ""))
    interests_list = skill_list_from_string(profile.get("interests", ""))
    year_now = current_year()

    skills_str = ", ".join(skills_list) if skills_list else profile.get("skills", "Not specified")
    interests_str = ", ".join(interests_list) if interests_list else profile.get("interests", "Not specified")

    system_msg = (
        "You are CareerCompass AI, an expert career counselor with 20+ years of experience "
        "helping students navigate their career paths. You specialize in providing deep, "
        "personalized, actionable career guidance. "
        "You ALWAYS respond with a single valid JSON object and nothing else. "
        "No markdown fences, no explanations, no text before or after the JSON. "
        "Your response MUST start with { and end with }."
    )

    user_msg = f"""Analyze this student's profile comprehensively and return the career analysis as a single JSON object.

STUDENT PROFILE:
- Name: {profile['name']}
- Age: {profile['age']}
- College: {profile['college']}
- Branch / Major: {profile['branch']}
- Current Year: {profile['year']}
- CGPA: {profile['cgpa']} / 10.0
- Current Skills: {skills_str}
- Interests: {interests_str}
- Career Goal: {profile['career_goal']}
- Additional Context: {profile.get('additional_guidelines', 'None')}
- Year of Analysis: {year_now}

Return a single JSON object that matches EXACTLY this schema. Every field is required. Be specific, detailed, and actionable. Base ALL recommendations on this student's actual profile — not generic advice.

{{
  "career_recommendation": {{
    "primary_career": "string — specific job title (e.g., 'Machine Learning Engineer', not 'Tech')",
    "career_category": "string — e.g., 'Artificial Intelligence & Data Science'",
    "match_score": integer between 60 and 98,
    "confidence_score": integer between 65 and 97,
    "confidence_explanation": "string — 2–3 sentences explaining why this confidence level was assigned based on the student's profile",
    "why_this_career": "string — 3–4 sentences explaining exactly why this career fits this specific student",
    "market_demand": "High|Medium|Low",
    "avg_salary_entry": integer in USD per year,
    "avg_salary_mid": integer in USD per year,
    "avg_salary_senior": integer in USD per year,
    "avg_salary_lead": integer in USD per year,
    "job_growth_percent": integer,
    "future_scope": "string — 3–4 sentences about where this career leads in 5–10 years"
  }},
  "skill_analysis": {{
    "existing_skills": ["string", ...],
    "required_skills": ["string", ...],
    "skill_gap": ["string", ...],
    "skill_gap_reasons": {{"skill_name": "why this skill is needed — 1 sentence", ...}},
    "strengths": ["string", ...],
    "strength_explanations": {{"skill_name": "why this is a strength — 1 sentence", ...}},
    "radar_scores": {{
      "technical_skills": integer 0–100,
      "problem_solving": integer 0–100,
      "communication": integer 0–100,
      "industry_knowledge": integer 0–100,
      "project_experience": integer 0–100,
      "soft_skills": integer 0–100
    }}
  }},
  "certifications": [
    {{
      "name": "string — full official certification name",
      "provider": "string — e.g. Google, IBM, AWS, Microsoft, Cisco",
      "level": "Beginner|Intermediate|Advanced|Expert",
      "duration": "string e.g. '3 months'",
      "cost": "string e.g. 'Free', '$49', '$300'",
      "difficulty": "Easy|Medium|Hard",
      "skills_gained": ["string", ...],
      "why_important": "string — 2–3 sentences explaining exactly why this cert matters for this specific career path",
      "url": "string — direct URL to official certification page (or realistic search URL if unknown)"
    }}
  ],
  "learning_resources": {{
    "books": [
      {{
        "title": "string",
        "author": "string",
        "url": "string — direct URL to Amazon, Goodreads, or official book page",
        "why_read": "string — 2 sentences explaining what this book teaches and why it is essential",
        "difficulty": "Beginner|Intermediate|Advanced"
      }}
    ],
    "youtube_channels": [
      {{
        "channel_name": "string",
        "url": "string — direct URL to YouTube channel",
        "focus_area": "string",
        "why_watch": "string — 1–2 sentences"
      }}
    ],
    "platforms": [
      {{
        "name": "string — platform name e.g. 'Coursera', 'IBM SkillsBuild', 'Microsoft Learn', 'freeCodeCamp', 'AWS Skill Builder', 'Google Cloud Skills Boost', 'Cisco Skills for All'",
        "resource_title": "string — specific course or learning path name on this platform",
        "url": "string — direct URL to the resource",
        "description": "string — 1–2 sentences on what this teaches and why it fits",
        "is_free": true or false
      }}
    ],
    "online_courses": [
      {{
        "title": "string",
        "platform": "string",
        "url": "string — direct URL to the course",
        "instructor": "string",
        "duration": "string",
        "why_take": "string — 2 sentences"
      }}
    ]
  }},
  "projects": {{
    "beginner": [
      {{
        "title": "string",
        "difficulty": "Beginner",
        "description": "string — 2–3 sentences",
        "skills_learned": ["string", ...],
        "technologies": ["string", ...],
        "estimated_time": "string e.g. '2–3 weeks'",
        "expected_outcome": "string — what the student will have built"
      }}
    ],
    "intermediate": [
      {{
        "title": "string",
        "difficulty": "Intermediate",
        "description": "string — 2–3 sentences",
        "skills_learned": ["string", ...],
        "technologies": ["string", ...],
        "estimated_time": "string",
        "expected_outcome": "string"
      }}
    ],
    "advanced": [
      {{
        "title": "string",
        "difficulty": "Advanced",
        "description": "string — 2–3 sentences",
        "skills_learned": ["string", ...],
        "technologies": ["string", ...],
        "estimated_time": "string",
        "expected_outcome": "string"
      }}
    ]
  }},
  "roadmap": {{
    "phase_1": {{
      "title": "Foundation Building",
      "level": "Beginner",
      "duration": "Month 1–3",
      "goals": ["string — specific measurable goal", ...],
      "topics": ["string — main topic to study", ...],
      "subtopics": ["string — specific subtopic or concept", ...],
      "practical_exercises": ["string — hands-on exercise description", ...],
      "mini_projects": ["string — small project idea to reinforce learning", ...],
      "weekly_focus": "string — what to focus on each week",
      "monthly_milestone": "string — what you should have achieved by end of this phase",
      "expected_outcome": "string — 2 sentences describing the student's capability level after completing this phase",
      "study_hours_per_week": integer,
      "key_resources": ["string — specific resource name", ...]
    }},
    "phase_2": {{
      "title": "Skill Development",
      "level": "Intermediate",
      "duration": "Month 4–6",
      "goals": ["string", ...],
      "topics": ["string", ...],
      "subtopics": ["string", ...],
      "practical_exercises": ["string", ...],
      "mini_projects": ["string", ...],
      "weekly_focus": "string",
      "monthly_milestone": "string",
      "expected_outcome": "string — 2 sentences",
      "study_hours_per_week": integer,
      "key_resources": ["string", ...]
    }},
    "phase_3": {{
      "title": "Project Building",
      "level": "Advanced",
      "duration": "Month 7–12",
      "goals": ["string", ...],
      "topics": ["string", ...],
      "subtopics": ["string", ...],
      "practical_exercises": ["string", ...],
      "mini_projects": ["string", ...],
      "weekly_focus": "string",
      "monthly_milestone": "string",
      "expected_outcome": "string — 2 sentences",
      "study_hours_per_week": integer,
      "key_resources": ["string", ...]
    }},
    "phase_4": {{
      "title": "Industry Readiness",
      "level": "Expert",
      "duration": "Month 13–24",
      "goals": ["string", ...],
      "topics": ["string", ...],
      "subtopics": ["string", ...],
      "practical_exercises": ["string", ...],
      "mini_projects": ["string", ...],
      "weekly_focus": "string",
      "monthly_milestone": "string",
      "expected_outcome": "string — 2 sentences",
      "study_hours_per_week": integer,
      "key_resources": ["string", ...]
    }}
  }},
  "career_timeline": [
    {{
      "stage": "string — e.g., 'Junior Developer'",
      "years_from_now": integer,
      "description": "string",
      "expected_salary": integer,
      "key_skills_needed": ["string", ...]
    }}
  ],
  "action_plan": {{
    "immediate_actions": [
      {{
        "action": "string — specific, actionable task",
        "reason": "string — why this matters",
        "time_to_complete": "string — e.g., 'This week'"
      }}
    ],
    "short_term": [
      {{
        "action": "string",
        "reason": "string",
        "time_to_complete": "string"
      }}
    ],
    "long_term": [
      {{
        "action": "string",
        "reason": "string",
        "time_to_complete": "string"
      }}
    ]
  }},
  "internship_strategy": {{
    "readiness_level": "Not Ready|Getting Ready|Ready|Highly Ready",
    "readiness_reason": "string — 2 sentences",
    "target_companies": ["string", ...],
    "preparation_steps": ["string", ...],
    "best_platforms": ["string", ...],
    "application_tips": "string — 2–3 sentences"
  }},
  "interview_preparation": {{
    "focus_areas": ["string", ...],
    "common_questions": ["string", ...],
    "technical_topics": ["string", ...],
    "preparation_resources": ["string", ...],
    "tips": "string — 2–3 sentences"
  }},
  "profile_building": {{
    "resume_tips": ["string", ...],
    "linkedin_tips": ["string", ...],
    "github_tips": ["string", ...],
    "portfolio_tips": ["string", ...]
  }},
  "related_careers": [
    {{
      "title": "string — specific job title",
      "similarity": integer 50–95,
      "description": "string — 2–3 sentences on what this role does and why it relates",
      "avg_salary": integer,
      "market_demand": "High|Medium|Low",
      "required_skills": ["string", ...],
      "career_progression": ["string — progression stage e.g. 'Junior → Mid → Senior → Principal'"],
      "future_scope": "string — 1–2 sentences on growth potential"
    }}
  ],
  "motivational_message": "string — 3–4 warm, encouraging, personalized sentences addressing the student by first name and affirming their potential based on their specific profile"
}}

Return ONLY the JSON object. Start your response with {{ and end with }}."""

    # Llama-3 instruct chat format — the trailing assistant header primes
    # the model to complete with the JSON body directly.
    prompt = (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n\n"
        f"{system_msg}"
        "<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}"
        "<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
    return prompt


# ---------------------------------------------------------------------------
# Quick summary prompt (for lightweight uses)
# ---------------------------------------------------------------------------

def build_quick_summary_prompt(profile: dict) -> str:
    """Lightweight prompt returning a minimal JSON summary (Llama-3 instruct format)."""
    system_msg = (
        "You are an expert career counselor. "
        "You respond ONLY with a valid JSON object. No markdown, no explanation."
    )
    user_msg = (
        f"Student: {profile['name']}, studying {profile['branch']} "
        f"({profile['year']}), CGPA {profile['cgpa']}, goal: {profile['career_goal']}.\n\n"
        "Return this JSON:\n"
        '{{\n'
        '  "one_liner": "one sentence career recommendation",\n'
        '  "top_career": "string",\n'
        '  "match_score": integer,\n'
        '  "top_3_skills_to_learn": ["string", "string", "string"],\n'
        '  "first_action": "string"\n'
        '}}'
    )
    return (
        "<|begin_of_text|>"
        "<|start_header_id|>system<|end_header_id|>\n\n"
        f"{system_msg}"
        "<|eot_id|>"
        "<|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_msg}"
        "<|eot_id|>"
        "<|start_header_id|>assistant<|end_header_id|>\n\n"
    )
