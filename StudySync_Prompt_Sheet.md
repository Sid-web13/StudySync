# StudySync -- Prompt Sheet

**Team Name:** Learnova\
**Team ID:** PE-B25-24\
**Problem Statement:** SIH 26207 -- Smart Education\
**Project:** StudySync -- Personalised Student Academic Mentorship
Platform

## Purpose

This prompt sheet indexes the 30 core prompts used to plan and develop
StudySync. The prompts are grouped according to the seven development
phases supplied by the team. The original prompt text should be retained
separately as primary evidence where required.

## Phase 1: Project Setup & Database Architecture

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P01                     Project Architecture &  Define the three-tier
                          Stack Definition        architecture,
                                                  technology stack and
                                                  project directory
                                                  structure.

  P02                     SQLAlchemy Data Models  Design database models
                                                  for students, subjects,
                                                  syllabus topics,
                                                  quizzes, quiz
                                                  questions, quiz
                                                  attempts and mentor
                                                  messages.

  P03                     Configuration & SQLite  Configure application
                          Database Engine         settings, SQLite
                                                  connection, SQLAlchemy
                                                  engine and database
                                                  session management.

  P04                     Password Security & JWT Implement password
                          Authentication Helpers  hashing, password
                                                  verification and JWT
                                                  token generation and
                                                  decoding.
  -----------------------------------------------------------------------

## Phase 2: Authentication & Syllabus State Machine

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P05                     Pydantic Validation     Define request and
                          Schemas                 response schemas for
                                                  authentication,
                                                  syllabus, quizzes,
                                                  mentor chat and
                                                  analytics.

  P06                     Authentication API      Implement signup,
                          Routes with Starter     login, protected
                          Seed                    profile access and
                                                  automatic seeding of
                                                  introductory subjects
                                                  and topics.

  P07                     Syllabus & Topic State  Develop APIs for
                          Machine Endpoints       subject management,
                                                  topic creation and
                                                  syllabus
                                                  progress-status
                                                  updates.

  P08                     Fast Verification Unit  Verify signup, JWT
                          Test for Syllabus       generation,
                                                  duplicate-email
                                                  rejection, syllabus
                                                  retrieval and
                                                  topic-status updates.
  -----------------------------------------------------------------------

## Phase 3: AI Quiz Generation & Scoring Engine

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P09                     Quiz Generation --      Establish a baseline
                          Zero-Shot Baseline      quiz-generation prompt
                                                  and examine the
                                                  limitations of
                                                  unstructured output.

  P10                     Quiz Generation -- Role Improve quiz generation
                          & Schema Request        using role prompting
                                                  and a JSON response
                                                  request.

  P11                     Quiz Generation --      Enforce a strict JSON
                          Strict Schema &         array, required keys,
                          Negative Constraints    four options per
                                                  question and
                                                  restrictions against
                                                  markdown fences,
                                                  comments and
                                                  conversational text.

  P12                     Resilient LLM Service   Integrate Gemini, clean
                          Layer with Fallback     and parse generated
                                                  JSON, and provide
                                                  deterministic fallback
                                                  responses for offline
                                                  testing or missing API
                                                  configuration.

  P13                     Quiz Generation API     Generate quizzes for
                          Route                   student-owned syllabus
                                                  topics and persist quiz
                                                  questions in SQLite.

  P14                     Server-Side Quiz        Evaluate submitted
                          Scoring & Topic Mastery answers on the server,
                          Promotion               record quiz attempts
                                                  and update topic status
                                                  using the 80% mastery
                                                  threshold.
  -----------------------------------------------------------------------

## Phase 4: AI Academic Mentor & Dynamic Context

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P15                     Mentor Chat -- Baseline Establish a baseline
                          Zero-Shot               academic
                                                  question-answering
                                                  prompt and identify its
                                                  personalization
                                                  limitations.

  P16                     Mentor Chat -- Persona  Introduce the StudySync
                          & Student Scoping       Mentor persona and
                                                  inject student-specific
                                                  academic information.

  P17                     Mentor Chat -- Dynamic  Add database-derived
                          Assessment Telemetry    context, including
                                                  enrolled subjects,
                                                  syllabus completion and
                                                  weak topics based on
                                                  recent quiz scores
                                                  below 70%.

  P18                     Mentor Chat -- Concise  Enforce syllabus
                          Actionable Standard     grounding, targeted
                                                  encouragement,
                                                  practical revision
                                                  guidance, bullet-point
                                                  structure and a
                                                  response limit of 150
                                                  words.

  P19                     Mentor Chat API &       Implement mentor chat
                          Conversation            and history endpoints
                          Persistence             with database-backed
                                                  conversation
                                                  persistence.
  -----------------------------------------------------------------------

## Phase 5: Performance Analytics & Diagnostic Engine

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P20                     Performance Analytics   Calculate syllabus
                          Calculation Logic       progress, quiz
                                                  statistics and
                                                  weak/strong topic
                                                  classifications.

  P21                     Demo Account Seeding    Create an evaluator
                          Script                  account with predefined
                                                  subjects, topic
                                                  statuses and quiz
                                                  history for
                                                  demonstration.

  P22                     FastAPI App Assembly &  Integrate application
                          Static Mounting         routers, configure
                                                  CORS, provide a health
                                                  check and serve the
                                                  frontend.
  -----------------------------------------------------------------------

## Phase 6: Frontend Interface & UI Components

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P23                     SPA Layout & Tailwind   Build the single-page
                          Styling Shell           interface with
                                                  navigation,
                                                  authentication and
                                                  client-side view
                                                  switching.

  P24                     One-Click Evaluator     Add quick evaluator
                          Login Banner            access by automatically
                                                  filling the demo
                                                  credentials.

  P25                     Dashboard Overview &    Develop the
                          Metric Cards            personalized dashboard
                                                  with progress metrics,
                                                  subject summaries and
                                                  weak-topic alerts.

  P26                     Interactive Syllabus    Display subjects and
                          Tracker UI              topics with interactive
                                                  progress controls and
                                                  quiz launchers.

  P27                     AI Quiz Engine &        Develop the quiz
                          Interactive Test Taker  interface with AI
                                                  generation, MCQ
                                                  selection, scoring and
                                                  explanations.

  P28                     AI Mentor Chat          Build the mentor chat
                          Messenger UI            interface with message
                                                  history, quick-prompt
                                                  chips and interactive
                                                  messaging.
  -----------------------------------------------------------------------

## Phase 7: Analytics, Testing & Deployment

  -----------------------------------------------------------------------
  Prompt ID               Prompt Title            Objective / Expected
                                                  Outcome
  ----------------------- ----------------------- -----------------------
  P29                     Performance Analytics   Create the analytics
                          View                    interface for weak
                                                  topics, strong topics
                                                  and subject-wise
                                                  syllabus progress.

  P30                     Comprehensive           Test application
                          End-to-End Test Suite   functionality across
                                                  authentication,
                                                  syllabus, quizzes,
                                                  mentor chat and
                                                  analytics using an
                                                  in-memory SQLite
                                                  database.
  -----------------------------------------------------------------------

## Prompt Sheet Summary

The 30 core prompts are organized into seven development phases,
covering the application lifecycle from architecture and database design
to AI integration, frontend development, analytics and end-to-end
testing.

The most explicit prompt-refinement experiments are the Quiz Generator
sequence (P09--P12) and the AI Academic Mentor sequence (P15--P18).
These sequences are documented separately in the Prompt Iteration Log.

## Supporting Prompts (P31--P34)

Prompts P31--P34 are supporting project prompts rather than part of the
30 core application-development prompts:

-   **P31 -- 12-Row Test Table for Milestone 2:** Requests a structured
    test table containing normal, edge and invalid cases.
-   **P32 -- 4-Version Prompt Iteration Log Documentation:** Requests
    documentation of the four prompt versions for the Quiz Generator and
    AI Academic Mentor.
-   **P33 -- One-Click Windows Launch Scripts:** Requests Windows
    `run.bat` and `stop.bat` scripts.
-   **P34 -- Milestone 2 Technical Project Report Compilation:**
    Requests compilation of the project report and its supporting
    sections.

These supporting prompts can be included as supplementary evidence if
the submission requires a complete record of all 34 prompts.
