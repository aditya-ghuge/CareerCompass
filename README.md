# CareerCompass AI

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen.svg)](https://careercompass-g74q.onrender.com)
[![Powered by IBM Granite](https://img.shields.io/badge/Powered_by-IBM_Granite-0f62fe.svg)](https://www.ibm.com/watsonx)

**Professional AI-powered career counseling platform **



---

## Overview

CareerCompass AI is a production-quality career counseling platform that analyzes student profiles and generates comprehensive, deeply personalized career guidance — not just answers, but complete career clarity with reasoning behind every recommendation.

---

## Key Features

- **Deep AI Profile Parsing**: Understands your unique background, skills, and aspirations using IBM Granite.
- **Actionable 24-Month Roadmap**: Generates a phase-by-phase timeline with specific focus areas and study plans.
- **Salary Projections & Career Timeline**: Maps out your financial and role progression from Entry to Lead.
- **Curated Projects & Certifications**: Recommends exact projects (sorted by difficulty) and certifications to build your resume.
- **Export to PDF**: Generate a clean, branded PDF report of your career analysis instantly.

---

## Screenshots

> **Note:** Add your screenshots here to show off the beautiful UI!
> 
> *Example format:*
> `![Landing Page](static/img/screenshot_landing.png)`
> `![Analysis Hub](static/img/screenshot_analyzing.png)`
> `![Dashboard Report](static/img/screenshot_dashboard.png)`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python Flask |
| AI Model | IBM Granite (`ibm/granite-3-3-8b-instruct`) |
| AI Platform | IBM watsonx.ai SDK |
| Frontend | HTML5 · CSS3 · Vanilla JavaScript |
| Charts | Chart.js 4 |
| PDF | ReportLab |
| Agent Framework | IBM BOB |

---

## Project Structure

```
careercompass/
├── app.py              # Flask application factory & page routes
├── config.py           # Centralized configuration (env vars)
├── routes.py           # REST API endpoints (/api/*)
├── services.py         # Business logic, normalizes Granite output
├── watsonx.py          # IBM watsonx.ai SDK integration
├── prompts.py          # Prompt engineering for Granite
├── pdf.py              # ReportLab PDF generation
├── utils.py            # Validation, sanitization, helpers
├── requirements.txt
├── .env.example
├── templates/
│   ├── base.html       # Shared layout, navbar, footer
│   ├── index.html      # Landing page (Hero, Benefits, How it Works, FAQ)
│   ├── profile.html    # Student profile input form
│   ├── analyzing.html  # AI analysis loading page
│   ├── report.html     # Full career report dashboard
│   └── error.html      # 404 / 500 error pages
└── static/
    ├── css/style.css   # Complete design system (IBM-inspired)
    └── js/report.js    # Report rendering, charts, PDF export
```

---

## Setup

### 1. Clone and install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure IBM watsonx.ai credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
WATSONX_API_KEY=your_ibm_watsonx_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-3-8b-instruct
FLASK_SECRET_KEY=your_secret_key_here
```

**Getting credentials:**
1. Go to [IBM watsonx.ai](https://us-south.ml.cloud.ibm.com)
2. Create a project and note the Project ID
3. Generate an API key from IBM Cloud IAM

### 3. Run the application

```bash
python app.py
```

Open `http://localhost:5000`

### Production deployment

```bash
gunicorn -w 2 -b 0.0.0.0:5000 app:app
```

---

## REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check + watsonx connectivity |
| POST | `/api/validate` | Real-time profile validation |
| POST | `/api/analyze` | Full career analysis (calls Granite) |
| POST | `/api/export/pdf` | Generate & download PDF report |

### POST /api/analyze

**Request body:**
```json
{
  "name": "Priya Sharma",
  "age": 21,
  "college": "IIT Delhi",
  "branch": "Computer Science Engineering",
  "year": "3rd Year",
  "cgpa": 8.5,
  "skills": "Python, Machine Learning, SQL, Data Analysis",
  "interests": "Artificial Intelligence, Robotics",
  "career_goal": "Machine Learning Engineer at a top tech company",
  "additional_guidelines": "I want to work in product-focused companies"
}
```

**Response:** Complete structured analysis JSON with career recommendation, skill analysis, roadmap, projects, certifications, salary projections, and more.

---

## Analysis Output

The platform generates:

- **Career Recommendation** — Primary career + match score + confidence score + reasoning
- **Skill Analysis** — Existing, required, gap skills with reasons; radar scores
- **24-Month Roadmap** — 4 phases with weekly focus, milestones, study hours
- **18 Projects** — 6 beginner, 6 intermediate, 6 advanced with full details
- **Certifications** — 8 recommendations with provider, cost, why important
- **Learning Resources** — Books, YouTube channels, online courses
- **Salary Projections** — Entry → Mid → Senior → Lead with charts
- **Career Timeline** — Stage-by-stage progression with salary at each stage
- **Action Plan** — Immediate, short-term, long-term actions
- **Internship Strategy** — Readiness level, target companies, platforms
- **Interview Preparation** — Topics, questions, resources
- **Profile Building** — Resume, LinkedIn, GitHub, Portfolio tips
- **Related Careers** — 5 alternative paths with similarity scores

---

## Design Principles

- IBM Design Language inspired
- Professional typography (system font stack)
- Consistent 8-point spacing grid
- IBM Blue (`#0f62fe`) as primary accent
- No gradients, no glassmorphism, no neon
- Lots of whitespace, professional card layout
- Minimal animations, smooth transitions
- Fully responsive (mobile, tablet, desktop)

---

## IBM Technology Used

| Technology | Usage |
|---|---|
| **IBM Granite** (`ibm/granite-3-3-8b-instruct`) | Core AI model for career analysis |
| **IBM watsonx.ai** | Model hosting and inference platform |
| **IBM watsonx.ai Python SDK** | `ibm-watsonx-ai` package for API calls |
| **IBM BOB** | AI assistant used during development |

---

## Architecture

```
Browser
  │
  ├── GET /           → templates/index.html
  ├── GET /profile    → templates/profile.html
  ├── GET /analyzing  → templates/analyzing.html (calls /api/analyze)
  └── GET /report     → templates/report.html (reads sessionStorage)

/api/analyze flow:
  POST /api/analyze
    → routes.py (validates, calls services)
    → services.py (sanitizes, builds prompt)
    → prompts.py (constructs Granite prompt)
    → watsonx.py (calls IBM Granite via watsonx.ai SDK)
    → services.py (normalizes JSON response)
    → routes.py (returns structured JSON)

/api/export/pdf flow:
  POST /api/export/pdf (receives analysis JSON)
    → pdf.py (ReportLab PDF generation)
    → Returns PDF binary
```

---

*CareerCompass AI *
*Powered by IBM Granite Foundation Model on watsonx.ai*
