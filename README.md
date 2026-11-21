# StudySync — Personalised AI Academic Mentorship Platform

> **Smart India Hackathon (SIH) 2026 — Problem Statement SIH 26207 (Smart Education)**  
> **Team:** Learnova (`PE-B25-24`)

StudySync is a zero-dependency, container-free 3-tier academic mentorship web application designed for college students. It unifies semester syllabus tracking, AI-generated diagnostic practice quizzes, automated mastery promotion, and a **context-grounded AI academic mentor** powered by Google Gemini (`gemini-2.5-flash`)—with full offline deterministic fallback support for uninterrupted evaluation.

---

## Key Features

- **Zero-Dependency Single-Process Architecture:** Runs locally via FastAPI + Uvicorn serving both the REST API and the Tailwind CSS + Lucide Single Page Application (`app/static/index.html`) at `http://localhost:8000`.
- **Secure Authentication & Evaluator Quick Access:** Argon2id password hashing and JWT Bearer authentication, complete with a pre-seeded evaluator account (`siddharth@studysync.edu`) and one-click login fill.
- **Real-Time Syllabus Tracker:** Organize subjects by course code and semester, update module statuses (`not_started`, `in_progress`, `completed`), and launch topic quizzes in one click.
- **AI Practice Quiz Engine & Auto-Mastery Loop:** Generates 3 conceptual and practical MCQs per topic via Gemini 2.5 Flash (with regex JSON fence cleaning and offline fallback). Submissions are graded server-side; scoring **$\ge$ 80%** automatically marks the syllabus topic as `completed`, while scores **< 70%** flag the topic for targeted revision.
- **Context-Grounded AI Academic Mentor:** Dynamically queries SQLite for the student's enrolled subjects, syllabus completion ratio, weak quiz scores (< 70%), and recent chat turns before prompting Gemini—delivering concise (< 150 words), bulleted revision advice anchored to actual student telemetry.
- **Diagnostic Performance Analytics:** Visualizes overall syllabus readiness, mean quiz score, subject-wise completion meters, and a dual-column **Weak Topics (< 70%)** vs. **Strong Topics ($\ge$ 70%)** breakdown.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Vanilla HTML5, Tailwind CSS (CDN), Lucide Icons (CDN) |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| **Database & ORM** | SQLite (WAL mode + Foreign Keys), SQLAlchemy 2.0 |
| **AI & Grounding** | Google Gemini (`gemini-2.5-flash`) via `google-genai` SDK + Deterministic Offline Fallback |
| **Security** | Argon2id (`passlib[argon2]`), JWT (`python-jose`) |
| **Testing** | Pytest, FastAPI `TestClient`, In-Memory SQLite |

---

## Project Structure

```text
StudySync/
├── app/
│   ├── core/
│   │   ├── config.py          # Environment & app settings
│   │   ├── database.py        # SQLite WAL engine & session factory
│   │   └── security.py        # Argon2id hashing & JWT utilities
│   ├── routes/
│   │   ├── analytics.py       # GET /analytics
│   │   ├── auth.py            # POST /auth/signup, /auth/login, GET /auth/me
│   │   ├── mentor.py          # GET /mentor/history, POST /mentor/chat
│   │   ├── quiz.py            # POST /quiz/generate/{topic_id}, POST /quiz/submit
│   │   └── syllabus.py        # GET/POST /syllabus, PATCH /syllabus/topics/{id}/status
│   ├── services/
│   │   ├── llm_service.py     # Gemini 2.5 Flash client, regex sanitizer & offline fallback
│   │   └── mentor_context.py  # SQLite telemetry context builder for grounded chat
│   ├── static/
│   │   └── index.html         # Single Page Application (Dashboard, Syllabus, Quiz, Mentor, Analytics)
│   ├── deps.py                # JWT auth dependency
│   ├── main.py                # FastAPI entrypoint & static mount
│   ├── models.py              # SQLAlchemy 2.0 ORM models
│   └── schemas.py             # Pydantic request/response contracts
├── backend/
│   └── seed.py                # Idempotent evaluator demo data seeder
├── docs/
│   ├── iteration_log.md       # 4-version prompt engineering log (v1 -> v4)
│   ├── Milestone2_Report.md   # Complete project & evaluation report
│   └── test_table.md          # 12-case verification test matrix
├── tests/
│   └── test_api.py            # Automated pytest API test suite
├── run.bat                    # Windows one-click seeder, server launcher & browser opener
└── stop.bat                   # Windows graceful server shutdown script
