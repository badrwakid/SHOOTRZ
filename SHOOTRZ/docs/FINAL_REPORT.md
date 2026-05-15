# SHOOTRZ: AI-Powered Basketball Shot Mechanics Analysis Platform
## Final Project Report

**Project:** SHOOTRZ  
**Track:** Artificial Intelligence & Data Science  
**Date:** May 2026  
**Version:** 1.0 (Final Submission)

---

## Table of Contents

1. [Project Proposal](#1-project-proposal)
2. [System Requirements Specification](#2-system-requirements-specification)
3. [System Design Document](#3-system-design-document)
4. [System Implementation & Methodology](#4-system-implementation--methodology)
5. [Testing & Evaluation](#5-testing--evaluation)
6. [Results & Conclusions](#6-results--conclusions)
7. [Lessons Learned & Problems Faced](#7-lessons-learned--problems-faced)
8. [References](#8-references)
9. [Appendices](#9-appendices)

---

## 1. Project Proposal

### 1.1 Problem Statement

Basketball shooting mechanics are among the most studied aspects of the game, yet access to rigorous biomechanical feedback remains a privilege reserved for professional athletes with dedicated coaching staffs, motion-capture laboratories, and sports science departments. The overwhelming majority of amateur, scholastic, and semi-professional players receive either no feedback at all or subjective verbal cues from coaches who may lack the biomechanical vocabulary to articulate what they observe.

This gap is not trivial. Research consistently shows that poor shooting mechanics—inadequate elbow alignment, insufficient knee loading, inconsistent wrist follow-through—are the primary determinants of low shooting accuracy, yet these same defects are notoriously difficult to self-correct without quantified, frame-level evidence. Players spend thousands of hours in practice reinforcing flawed patterns because neither they nor their coaches have access to the analytical tools necessary to identify and correct them.

The frustrating part is that the information gap is not inherent to the sport. The biomechanics are well-understood—Cabarkapa et al. (2021) and Okazaki et al. (2012) have published precise angular targets for the elbow, knee, and wrist at each phase of the shooting motion. The problem is delivery: that knowledge lives in academic papers and motion-capture labs, not in the gym where it is needed.

### 1.2 Motivation

Three developments made this project practical to build at this moment.

The first was MediaPipe Pose reaching a level of reliability where we could extract 33 body landmarks per frame from a standard smartphone video without GPU hardware, without a controlled environment, and without a calibration procedure. Earlier pose estimators required lab conditions or expensive depth cameras. MediaPipe 0.10.14 works on footage shot by a phone propped against a water bottle.

The second was large language models maturing past the stage of generating plausible-sounding text toward generating structured, actionable output. We do not ask Gemini 2.5 Flash to write a coaching essay—we ask it to fill a defined Pydantic schema: specific verdicts, specific improvement cues, a 0–100 score with a one-line rationale. That constraint turns an LLM from a novelty into a reliable pipeline component.

The third was that modern mobile platforms (Expo, Supabase, FastAPI) now allow a small team to ship a functional full-stack product with authentication, cloud storage, and real-time streaming without maintaining dedicated infrastructure. The operational overhead that would have taken months five years ago now takes days.

Together, these three conditions made it possible to build something in a university project timeline that previously required a sports science lab budget.

### 1.3 Project Vision

SHOOTRZ is a basketball shot analysis platform built around a single idea: take a short phone video of a shot and get back the same quality of mechanical feedback a professional coach would give—but quantified, repeatable, and available without scheduling an appointment.

The core product is a six-stage computer vision pipeline that takes raw video frames and produces three things: joint angles at the key moments in the shot (crouch, release, follow-through), scores for each angle against research-validated biomechanical targets, and natural-language coaching cues from Gemini 2.5 Flash. Every result is persisted to the user's cloud account so they can track whether their mechanics are actually improving over time, not just how a single session felt.

Around the analysis engine, we built three supporting features: a conversational coaching chat that knows the user's most recent metrics, a drill recommendation engine that adapts suggestions to identified weaknesses using a contextual bandit model, and a progress dashboard that aggregates scores over weeks. Together these form a practice loop—analyze, understand, train, re-analyze—that previously required a dedicated coaching staff to sustain.

### 1.4 Objectives

1. Build a reliable, end-to-end computer vision pipeline capable of detecting shot events and computing biomechanical metrics from monocular smartphone video under typical amateur recording conditions.
2. Ground all metric thresholds in published biomechanics research, distinguishing between the optimal performance envelopes of beginner, intermediate, and advanced players.
3. Integrate a large language model to generate natural-language coaching feedback that is contextually personalized to the individual user's profile and recent performance history.
4. Implement a drill recommendation engine that adapts suggestions based on identified mechanical weaknesses, using similarity search and a contextual bandit model to balance exploration with exploitation.
5. Provide a persistent user account system with secure authentication, analysis history, streak tracking, and profile management.
6. Deliver the entire system through a polished mobile application capable of running on both iOS and Android.

### 1.5 Scope

**In scope:**
- Mobile video capture and upload for basketball shooting analysis
- 6-stage biomechanical analysis pipeline (pose extraction through metric derivation)
- AI-generated coaching feedback via Gemini 2.5 Flash
- Conversational coaching chat interface
- Personalized drill recommendations (FAISS + LinUCB contextual bandit)
- User authentication (email/password and Google OAuth)
- Cloud-persisted analysis history and streak tracking
- Optional ball trajectory analysis via YOLOv8n

**Out of scope:**
- Real-time (sub-second) on-device inference
- Multi-camera 3D reconstruction
- Team-level analytics
- Automated drill video playback
- Hardware integration (smart basketballs, wearables)

### 1.6 Target Users

The primary target users are basketball players at the amateur to semi-professional development level who practice regularly but lack access to professional coaching or sports science resources. Secondary targets include youth coaches seeking to provide data-backed feedback to large groups of players simultaneously, and independent skill trainers looking to augment their offering with AI-driven analytics.

### 1.7 Expected Impact

Biomechanical shot analysis currently costs somewhere between "a professional coaching contract" and "access to a university sports science lab." SHOOTRZ brings that cost to a phone video and a few seconds of server time. Players who receive precise mechanical feedback—specifically, which joint angle is off and by how much—can direct their practice time toward the actual deficiency rather than repeating the same flawed reps indefinitely. Coaching literature consistently links targeted mechanical correction to measurable accuracy improvement; the question has always been delivery, not whether the knowledge exists. The practical impact is most significant for developmental players (scholastic, amateur, semi-professional) who have neither the budget nor the access that elite programs take for granted.

### 1.8 Technical Innovation

The technical novelty of SHOOTRZ lies not in any single component but in the integration of several independently mature technologies into a cohesive, mobile-accessible analysis pipeline:

- **Adaptive shot event detection** using multi-signal temporal fusion (knee flexion, hip descent, wrist trajectory, elbow extension) rather than fixed-frame heuristics.
- **Confidence-weighted geometric mean scoring** that suppresses unreliable low-confidence metric estimates rather than allowing them to silently corrupt the overall score.
- **Skill-tiered normative ranges** that adapt assessment thresholds to the user's declared experience level, sourced from peer-reviewed sports science literature.
- **LLM score override with graceful fallback**: Gemini 2.5 Flash provides a holistic 0–100 assessment that corrects the conservatism of pure rule-based geometric means, with deterministic fallback if the model times out.
- **Contextual bandit recommendation**: LinUCB (via MABWiser) dynamically balances exploration and exploitation in drill selection, updating as user engagement data accumulates.

---

## 2. System Requirements Specification

### 2.1 Functional Requirements

#### FR-1: User Authentication & Account Management
- The system shall allow users to register and log in using email and password.
- The system shall support Google OAuth 2.0 via PKCE flow for mobile single-sign-on.
- The system shall support secure password reset via email.
- The system shall enforce email confirmation before granting full account access.
- The system shall collect a unique username during first-time onboarding.
- The system shall allow users to permanently delete their accounts, with cascading deletion of all associated data.

#### FR-2: Video Upload & Processing
- The system shall accept video uploads from the device camera roll or live recording.
- The system shall enforce a maximum upload size of 200 MB.
- The system shall detect and reject videos that are too short (fewer than 30 frames) to support reliable analysis.
- The system shall allow users to specify or override the detected shooting side (left/right).
- The system shall queue submitted videos and process them asynchronously, returning a job ID immediately.
- The system shall cap concurrent analysis jobs at eight globally, returning HTTP 429 to excess requests.

#### FR-3: Biomechanical Analysis
- The system shall extract per-frame 33-landmark body pose keypoints using MediaPipe Pose.
- The system shall smooth noisy pose signals using Savitzky–Golay filtering.
- The system shall detect the shot window (crouch, release, landing events) using a multi-signal state machine.
- The system shall compute elbow extension at release, knee flexion at crouch, and wrist follow-through angles.
- The system shall optionally compute ball release angle via YOLOv8n trajectory fitting.
- The system shall assess each metric against research-validated normative ranges, issuing verdicts of Good, Needs Work, or Low Confidence.
- The system shall produce an overall shot quality score on a 0–100 scale.
- The system shall generate annotated overlay video and raw data artifacts (pose CSV, angles CSV, JSON report).

#### FR-4: AI Coaching Feedback
- The system shall generate natural-language shot feedback using Gemini 2.5 Flash.
- Feedback shall include: overall explanation, metric-specific verdicts, listed strengths and improvement cues, and concise bullet-point coaching notes.
- The system shall provide a holistic AI score (0–100) alongside the rule-based metric score.
- The system shall fall back to the rule-based score if Gemini fails or exceeds a 10-second timeout.
- The system shall expose a conversational coaching chat interface using streaming server-sent events.
- The chat interface shall inject the user's recent analysis history, profile metadata, and weak areas as context for the LLM.

#### FR-5: Drill Recommendations
- The system shall recommend drills personalized to the user's identified mechanical weaknesses.
- Recommendations shall use FAISS nearest-neighbor similarity search over a curated drill pool.
- The system shall employ a LinUCB contextual bandit to rank drill clusters based on the user's mechanical profile.
- Each recommendation shall include a drill name, rationale, instructions, and estimated duration.

#### FR-6: History & Progress Tracking
- The system shall persist completed analyses to the user's cloud account.
- The system shall maintain a daily analysis streak counter.
- The system shall expose an analysis history endpoint with pagination and filtering.
- The system shall display aggregated progress metrics (weekly average score, total analyses, longest streak).

#### FR-7: Profile Management
- The system shall maintain user profile data including skill level, position, dominant hand, age, height, and coaching style preference.
- Profile data shall be used to personalize normative thresholds, AI feedback tone, and drill difficulty.

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- Video analysis pipeline shall complete within 40 seconds for a 5-second clip at 30 FPS under normal server load.
- API responses for non-analysis endpoints shall complete within 500 ms under normal load.
- The frontend shall display analysis results within 3 seconds of job completion.

#### NFR-2: Scalability
- The backend shall support a minimum of eight concurrent analysis jobs without degradation.
- The job concurrency limit shall be configurable via environment variable without code changes.
- The architecture shall support horizontal scaling by decoupling the job queue from the HTTP process.

#### NFR-3: Usability
- The application shall be operable by a non-technical user without a user manual.
- Visual feedback shall be provided for all asynchronous operations lasting more than one second.
- Error states shall display user-friendly messages rather than raw exception text.

#### NFR-4: Reliability
- Failed Gemini enrichment shall not prevent analysis results from being returned to the client.
- Failed result persistence shall not crash the application; retry logic shall be applied.
- The system shall degrade gracefully when Supabase is unavailable, continuing to serve cached results where possible.

#### NFR-5: Security
- All user-scoped data access shall be protected by Supabase Row-Level Security policies.
- API keys shall be stored exclusively in environment variables, never in source code.
- Authentication tokens shall be transmitted in request headers, not URL query parameters.
- Per-IP rate limiting shall be applied to all upload endpoints.

#### NFR-6: Portability
- The mobile application shall run on iOS 16+ and Android 12+ without platform-specific code paths.
- The backend shall run on Linux, macOS, and Windows (Python 3.11+) without modification.

#### NFR-7: Maintainability
- All API contracts shall be expressed in Pydantic models (backend) and TypeScript interfaces (frontend).
- All configuration parameters shall be centralized in `mvp_config.yaml` and environment variable files.
- All production log messages shall use structured JSON logging with `logging.getLogger(__name__)`.

### 2.3 User Requirements

- As a player, I want to record or upload a video of my shot and receive a score so I can gauge my current form.
- As a player, I want to see which specific joints are out of alignment and understand why so I can correct them.
- As a player, I want to ask the AI coach follow-up questions about my analysis in natural language.
- As a player, I want to be recommended drills that specifically target my weakest areas.
- As a player, I want to track my score over time and see whether my mechanics are improving.
- As a coach, I want to review individual player analyses and see metric breakdowns so I can provide targeted guidance.

### 2.4 System Constraints

- Video analysis is CPU-bound and requires a server with multiple cores to meet performance targets; GPU inference is not currently required.
- MediaPipe Pose requires that the full body be visible in the frame; heavily occluded or partially-visible clips will produce low-confidence results.
- Ball trajectory analysis (YOLOv8n) is disabled by default and requires the `SHOOTRZ_ENABLE_BALL=1` environment variable to activate, due to the additional CPU cost.
- The Gemini 2.5 Flash API has a rate limit of approximately 200 requests per minute at the free/standard tier.
- Supabase Storage is used for persisted video artifacts; the free tier imposes a 1 GB storage limit.

### 2.5 Assumptions

- Users record videos from a fixed camera position approximately 3–5 meters from the player, with the full body visible from the side or front.
- Videos are in MP4 or compatible format; HEVC (iOS default) may require transcoding.
- Users have a stable internet connection during video upload and polling.
- The server has at least two available CPU cores for pipeline processing.

### 2.6 Use Cases

**UC-1: Analyze Shot**
- Actor: Authenticated user
- Trigger: User selects a video from their camera roll
- Precondition: User is logged in; video is ≥30 frames; fewer than 8 jobs are in flight
- Flow: Upload → Queue → Pipeline → Enrich (Gemini) → Poll → Display → Persist
- Postcondition: Analysis is saved to user's account; streak is updated

**UC-2: Chat with Coach**
- Actor: Authenticated user
- Trigger: User types a question in the Chat screen
- Precondition: User has at least one completed analysis in their history
- Flow: Submit message → Backend injects analysis context → Gemini streams response → UI renders incrementally
- Postcondition: Message is persisted to chat_history table

**UC-3: Get Drill Recommendations**
- Actor: Authenticated user
- Trigger: User taps the Drills screen or "Get Drills" from an analysis result
- Flow: Send user metrics vector → FAISS search → LinUCB arm selection → Filter and rank → Return drill
- Postcondition: Drill displayed with rationale and instructions

**UC-4: View Progress**
- Actor: Authenticated user
- Trigger: User opens the Progress screen
- Flow: Fetch history from Supabase → Compute weekly averages, streak, trend → Render charts
- Postcondition: Historical performance trends displayed

### 2.7 User Flow

```
[Launch App]
     │
     ├─ (New User) → [Onboarding Slides] → [Email/Google Auth] → [Username Setup]
     │                                                                  │
     └─ (Returning User) → [Auth] ───────────────────────────────────→ [Home Dashboard]
                                                                             │
                    ┌────────────────────────────────────────────────────────┤
                    │                    │                │                  │
             [Analyze]           [Chat with Coach]  [Drills]         [Progress]
                    │
       [Select Video / Record]
                    │
       [POST /mvp/analyze → job_id]
                    │
       [Poll GET /mvp/result/{job_id}]
                    │
       [Result Display: Score Ring + Metrics + Feedback]
                    │
       [POST /api/analysis/complete → Persist to Supabase]
```

---

## 3. System Design Document

### 3.1 High-Level Architecture

SHOOTRZ follows a client-server architecture with a clear separation between the mobile frontend and the backend API service, connected through a managed cloud database and storage layer.

```
┌──────────────────────────────────────┐
│     React Native / Expo Mobile App    │
│  (iOS · Android · Web)                │
│                                       │
│  AuthContext · HistoryContext         │
│  ProfileContext                       │
│                                       │
│  Screens: Home · Analyze · Chat ·     │
│  Drills · Progress · Profile          │
└───────────────┬──────────────────────┘
                │ HTTPS · Axios · SSE
                ▼
┌──────────────────────────────────────┐
│     FastAPI Backend (Python 3.11+)    │
│                                       │
│  Routers · Services · Pipeline        │
│  LLM Integration · Recommender        │
│                                       │
│  ProcessPoolExecutor (≤ n_cpu - 1)    │
│  asyncio Semaphore (max 8 jobs)       │
│  SQLite Job Store (72h TTL)           │
└────────────┬─────────────┬───────────┘
             │             │
             ▼             ▼
┌─────────────────┐  ┌────────────────┐
│ Supabase        │  │ Google GenAI   │
│ PostgreSQL + RLS│  │ Gemini 2.5     │
│ Auth (JWT/PKCE) │  │ Flash (LLM)    │
│ Storage Bucket  │  └────────────────┘
└─────────────────┘
```

The backend is stateless with respect to HTTP requests; all durable state lives in Supabase (PostgreSQL). The exception is the ephemeral SQLite job store, which holds in-flight analysis jobs for up to 72 hours. This design means the backend can be restarted without losing committed analysis results, though in-progress jobs at crash time will be lost (a known limitation documented in Section 7).

### 3.2 Frontend Architecture

**Framework:** React Native 0.81.5 + TypeScript 5.9 managed by Expo 54. React 19.1 is used as the base rendering library.

**State Management:**  
The application uses React Context API with three top-level providers:

- `AuthContext`: Manages the Supabase session lifecycle, PKCE OAuth flow, deep link parsing for OAuth redirects, and the new-user detection gate that directs first-time users through onboarding.
- `HistoryContext`: Fetches and caches the user's analysis history from the API, triggering refreshes when the app returns to foreground or after a new analysis is committed.
- `ProfileContext`: Holds the user's extended profile, skill level, and preferences, exposing update methods that write through to Supabase.

**Navigation:**  
React Navigation 7 with a bottom-tab navigator (seven tabs: Home, Analyze, Chat, Drills, Workouts, Progress, Profile). Deep linking handles OAuth redirects and email confirmation URLs.

**API Communication:**  
Axios 1.12 with a shared instance configured to append the Supabase JWT in the `Authorization` header. Server-sent events (SSE) for chat streaming are handled by a custom `chat.service.ts` that incrementally accumulates chunk data.

**UI Components:**  
A purpose-built design system with tokens for color, typography, motion, and spacing. Key analysis-specific components include `ScoreRing` (animated 0–100 dial with tier color-coding), `MetricCard` (per-joint result with verdict and confidence), `AngleGraph` (frame-indexed angle timeline via react-native-chart-kit), and `AnalysisOverlayVideo` (expo-video player for the annotated skeleton overlay).

**Local Persistence:**  
AsyncStorage for offline access to recent analyses (capped at 200 entries) and chat history (capped at 200 messages), preventing storage quota exhaustion.

### 3.3 Backend Architecture

**Framework:** FastAPI 0.110+ on Uvicorn with a lifespan context manager that enforces multiprocessing spawn mode (required for MediaPipe fork-safety).

**Router Structure:**  
Eleven routers are registered at startup:

| Prefix | Purpose | Auth Required |
|--------|---------|--------------|
| `/mvp` | Video analysis (upload, poll, artifact download) | No (job-ID access) |
| `/api/analysis` | Commit analysis to Supabase | **Yes** |
| `/api/chat` | Streaming LLM coaching chat | **Yes** |
| `/api/history` | Analysis history retrieval | No (architectural gap—see §7) |
| `/api/user` | Profile, stats, account deletion | No (architectural gap—see §7) |
| `/api/feedback` | Per-analysis feedback retrieval | No |
| `/api/sessions` | Session metadata | No |
| `/api/recommend` | Drill recommendations | No |
| `/health` | Liveness + version info | No |

**Concurrency Model:**  
Video analysis is CPU-intensive and runs inside a `ProcessPoolExecutor` with `max_workers = cpu_count - 1`. Jobs are submitted to the pool from within an asyncio `BackgroundTask`. An asyncio `Semaphore(8)` gates submissions, returning HTTP 429 immediately when all slots are occupied rather than queueing, to keep latency predictable.

**Job Lifecycle:**  
1. `POST /mvp/analyze` validates the video, generates a `job_id`, inserts `status=queued` into SQLite, and launches a background task.
2. The background task calls `MVPPipeline.process_video()` in the process pool (blocking, ~15–40 s).
3. On success, the job service enriches the result with Gemini feedback (10-second timeout), then updates SQLite to `status=completed`.
4. The client polls `GET /mvp/result/{job_id}` until completion.
5. After receiving results, the authenticated client calls `POST /api/analysis/complete`, which commits the full result to Supabase's `analysis_summaries` table and updates the user's streak.

**Rate Limiting:**  
slowapi 0.1.9 applies a per-IP limit of 30 requests per minute to upload endpoints.

**Logging:**  
Structured JSON logging via `python-json-logger` with `logging.getLogger(__name__)` throughout. Log entries carry `extra` fields for `run_id`, `job_id`, `user_id`, and stage names.

### 3.4 Database & Storage Design

**Primary Database:** PostgreSQL via Supabase with Row-Level Security enabled on all user-scoped tables.

**Core Tables:**

| Table | Purpose |
|-------|---------|
| `public.users` | SHOOTRZ user records, linked to `auth.users` via trigger |
| `user_profiles` | Extended profile data (height, weight, experience, preferences) |
| `user_preferences` | Display and notification settings |
| `user_streaks` | Daily and weekly analysis counters, streak tracking |
| `sessions` | Per-analysis session metadata |
| `videos` | Uploaded video references and storage URLs |
| `analysis_summaries` | Full pipeline output: scores, metrics JSON, feedback JSON |
| `chat_history` | Conversational coaching messages (user and coach sides) |
| `drill_library` | Static drill catalog |
| `drill_completions` | User drill completion history |
| `workout_sessions` | User-defined workout records |

**RLS Pattern:**  
Every user-scoped table enforces `auth.uid() = user_id` for `SELECT`, `INSERT`, `UPDATE`, and `DELETE`. The backend writes through the service-role client (which bypasses RLS), while the frontend anon client is used only for JWT verification.

**RPC Functions:**
- `get_coach_context(user_id, max_analyses)`: Returns recent analyses with metrics for chat context injection, replacing four sequential API calls with a single round trip.
- `get_user_stats(user_id)`: Returns aggregated streak and analysis statistics.
- `update_user_streak(user_id, session_id, score)`: Atomically updates streak counters.

**Storage Bucket:** A Supabase Storage bucket named `videos` stores all generated artifacts (overlay video, pose CSV, angles CSV, JSON report). Bucket policies allow authenticated uploads and public reads.

**Ephemeral Job Store:** SQLite (via `backend/services/job_store.py`) provides a thread-safe, durable in-process store for the lifecycle of analysis jobs (72-hour TTL). This avoids the overhead of a full database for ephemeral state while surviving server restarts within the retention window.

### 3.5 AI/ML System Design

#### 3.5.1 MediaPipe Pose Estimation

MediaPipe Pose (version 0.10.14) provides the pose backbone of the pipeline. It detects 33 full-body landmarks per frame, each with 2D image coordinates, inferred depth (z), and a visibility confidence score (0–1). The system runs in static image mode with configurable model complexity (0=fastest, 1=balanced, 2=most accurate; default is 1 in production).

Frames with mean landmark visibility below 0.40 are discarded before downstream processing. The shooting side (left or right) is automatically detected from shoulder-to-wrist asymmetry and confirmed against the user's profile. All subsequent angle computations and shot detection prioritize the `{shooting_side}_{joint}` landmark naming convention.

#### 3.5.2 Shot Event Detection (State Machine)

Rather than relying on a fixed frame offset or a single signal, SHOOTRZ implements a multi-signal temporal fusion state machine with four states: STANCE → CROUCH → RELEASE → LANDING.

Transition signals:
- **Knee flexion** (primary crouch signal): knee angle drops below an adaptive threshold derived from the video's joint angle distribution.
- **Hip vertical descent**: hip landmark drops during the loading phase.
- **Wrist height trajectory**: peak wrist height is detected using `scipy.signal.find_peaks` over the wrist y-coordinate series.
- **Elbow extension**: ascent of elbow angle after the crouch minimum confirms the release phase.

Adaptive thresholds are derived per-video from the signal statistics rather than hardcoded, making the detector resilient to different recording distances and player body proportions. A configurable legacy mode (`use_legacy_detector: true`) falls back to the simpler knee-minimum + first-wrist-peak heuristic for diagnostic comparison.

The detector outputs a `ShotWindow` event dict with `crouch_frame`, `release_frame`, `landing_frame`, confidence score, and up to three alternative candidate windows for diagnostics.

#### 3.5.3 Angle Computation

Angles are computed from triplets of landmarks using the standard law of cosines over 2D normalized coordinates. The five primary metrics are:

| Metric | Landmarks | Optimal Range | Source |
|--------|-----------|---------------|--------|
| Elbow extension at release | shoulder → elbow → wrist | 170–180° | Cabarkapa et al. 2021 |
| Knee flexion at crouch | hip → knee → ankle | 105–115° | Cabarkapa et al. 2021 |
| Wrist follow-through | wrist angle change (release → landing) | 18–28° | Struzik et al. 2014 |
| Forearm verticality | elbow → wrist vs. vertical axis | 0–8° | Cabarkapa et al. 2021 |
| Release angle (optional) | ball trajectory from YOLOv8n | 63–68° at 4.6 m | Okazaki et al. 2012 |

Each metric is computed over a search window centered on the detected shot event (±10 frames for release, ±6 for crouch), selecting the frame with the highest landmark confidence above a 0.50 threshold.

#### 3.5.4 Metric Scoring

Scoring converts raw joint angles into component scores (0–100) using a softened distance function relative to the normative ranges:

1. If the angle falls within the `optimal_range`, score = 100.
2. If within the `good_range` but outside optimal, score is linearly interpolated from 100 to 60.
3. Beyond `good_range`, score is penalized proportionally to deviation.

An overall score is computed as the confidence-weighted geometric mean of all available component scores, with weights: elbow extension 0.32, knee bend 0.24, release angle 0.20, wrist follow-through 0.14, forearm verticality 0.10. Weights are re-normalized across the metrics that are actually present in a given analysis (i.e., when ball tracking is disabled, release angle is dropped and the remaining weights are rescaled).

Normative ranges are tiered by user skill level (beginner, intermediate, advanced), with wider acceptable ranges for less experienced players:

- **Beginner** knee flexion target: 78–142° (wide)
- **Intermediate** knee flexion target: 89–131°
- **Advanced** knee flexion target: 100–120° (tight, research-optimal)

#### 3.5.5 LLM Integration (Gemini 2.5 Flash)

Gemini 2.5 Flash is used for two distinct purposes: (1) generating shot feedback, and (2) providing an AI-scored overall rating that corrects the conservatism of the geometric mean.

The LLM client (`backend/services/llm/gemini_client.py`) uses the official `google-genai` SDK with structured output via Pydantic schemas. Two schemas are defined:

- `ShotFeedbackOutput`: overall explanation, metric explanations, strengths, improvements, feedback bullets, score tier, AI overall score (0–100), AI score rationale.
- `DrillRecommendationOutput`: drill name, rationale, step-by-step instructions.

All requests are subject to a 10-second timeout and up to three exponential-backoff retries. If the LLM fails, the response falls back to the rule-based score, and the `ai_scored=false` flag is set in the result so the frontend can communicate this to the user.

The AI score override is motivated by a known limitation of the geometric mean: a single very weak metric can collapse the overall score disproportionately. Gemini's holistic assessment, conditioned on the full metric context and user profile, provides a more practical coaching-oriented score that acknowledges partial proficiency.

#### 3.5.6 Drill Recommendation System

The recommendation engine combines FAISS similarity search with LinUCB contextual bandit reinforcement learning (via the MABWiser library).

**FAISS Index:** A flat inner-product index (`IndexFlatIP`) over L2-normalized 5-dimensional user embeddings representing mechanical performance: `[elbow_strength, knee_power, wrist_control, accuracy, consistency]`. The index is searched for the top-10 most similar drills from the curated pool of approximately 50 drills.

**LinUCB Bandit:** Arms correspond to `C{cluster}_T{tier}` combinations (drill cluster × difficulty tier). The contextual feature vector is the same 5D mechanical embedding. The UCB exploration parameter α = 1.4 balances exploration of untried drill types against exploitation of known effective ones. Rewards are derived from drill completion ratings.

**Recommendation Flow:**
1. Normalize the user's metric vector.
2. FAISS search returns the 10 most similar drills.
3. LinUCB selects the best-expected arm for the current context.
4. Candidates are filtered to the chosen arm's cluster and tier.
5. The top-ranked drill is returned with a natural-language rationale.

#### 3.5.7 Ball Tracking (Optional, YOLOv8n)

When enabled (`SHOOTRZ_ENABLE_BALL=1`), a YOLOv8n model (`yolov8n.pt`, 6.5 MB) processes every `ceil(total_frames / 60)` frames to detect the basketball. Detected positions are Kalman-filtered and fit to a three-point parabola to estimate the release angle. This is treated as a bonus signal; failures are caught and suppressed without affecting other metrics.

### 3.6 Data Flow Diagrams

**End-to-End Video Analysis Flow:**

```
[User records/selects video]
         │
         ▼
[Mobile: POST /mvp/analyze (multipart/form-data)]
         │
         ▼
[Backend: validate video (≥30 frames, OpenCV readable)]
[Generate job_id, write SQLite: status=queued]
[Return MVPAnalyzeQueuedResponse {job_id}]
         │
         ▼ (asyncio BackgroundTask)
[MVPPipeline.process_video() in ProcessPoolExecutor]
    │
    ├─ Stage 1: VideoLoader
    │   └─ Read frames (stride if >300 frames), extract metadata
    │
    ├─ Stage 2: PoseEstimation
    │   └─ MediaPipe 33-landmark detection per frame
    │   └─ Filter low-confidence frames (<0.40 mean visibility)
    │   └─ Output: pose_keypoints.csv
    │
    ├─ Stage 3: SignalSmoothing
    │   └─ Savitzky-Golay (window=5, polyorder=2)
    │   └─ Gap interpolation (max 10 consecutive frames)
    │
    ├─ Stage 4: ShotDetection
    │   └─ Multi-signal state machine
    │   └─ Output: shot_window {crouch, release, landing frames}
    │
    ├─ Stage 5: AngleComputation
    │   └─ Per-frame joint angles for 5 metrics
    │   └─ Output: angles.csv
    │
    └─ Stage 6: MetricsDerivation
        └─ Select best-confidence frame per metric
        └─ Score against normative ranges
        └─ Confidence-weighted geometric mean
        └─ Output: run_metadata.json
         │
         ▼
[Gemini enrichment (10s timeout)]
    └─ ShotFeedback: explanations, bullets, AI score
         │
         ▼
[SQLite: status=completed, payload=full JSON]
         │
         ▼ (Client polling every 2 seconds)
[GET /mvp/result/{job_id} → completed]
         │
         ▼
[Mobile renders: ScoreRing, MetricCards, AngleGraph, Feedback]
         │
         ▼
[POST /api/analysis/complete (authenticated)]
         │
         ▼
[Supabase writes: sessions, videos, analysis_summaries, user_streaks]
```

### 3.7 Design Decisions & Tradeoffs

**Decision 1: Asynchronous polling vs. WebSocket for job status**  
The current design uses HTTP polling (every 2 seconds) rather than WebSocket or SSE for job completion notification. This was chosen for simplicity: polling requires no persistent connection management, works through all proxies, and is robust to client network interruptions. The tradeoff is slightly higher server load from repeated GET requests and a variable latency of 0–2 seconds between completion and notification.

**Decision 2: SQLite as the ephemeral job store**  
SQLite provides a durable, thread-safe, zero-dependency storage layer for in-flight jobs. It survives backend restarts within the 72-hour retention window and requires no additional infrastructure. The tradeoff is that it cannot be shared across horizontally-scaled backend instances, limiting the current architecture to single-instance deployment.

**Decision 3: Confidence-weighted geometric mean with AI override**  
The geometric mean was chosen over a simple weighted sum because it naturally penalizes any single very weak metric—a desirable property for mechanical assessment where gross form errors in one area genuinely degrade the quality of the shot. However, this approach can be overly conservative when pose estimation confidence is low on one axis but the player's actual form is good. The Gemini AI score provides a holistic override that corrects these edge cases, while the rule-based score is always preserved as a fallback.

**Decision 4: MediaPipe over other pose estimators**  
MediaPipe Pose was selected over alternatives (HRNet, OpenPose, VideoPose3D) for its combination of real-time performance on CPU-only hardware, cross-platform support, and well-documented 33-landmark model. The tradeoff is that its depth estimation (z-coordinate) is inferred rather than stereo-captured, limiting 3D accuracy. HRNet is present in the repository as a placeholder for a potential future upgrade.

**Decision 5: FAISS + LinUCB over a simpler recommendation approach**  
A simple rule-based drill assignment (e.g., "if elbow < threshold, recommend elbow drill") would be faster to implement but cannot adapt to the joint distribution of weaknesses or learn from user engagement over time. The FAISS + LinUCB combination allows the system to improve its recommendations as usage data accumulates, at the cost of additional infrastructure complexity.

---

## 4. System Implementation & Methodology

### 4.1 Development Methodology

Development moved in vertical slices: get pose extraction working on a single still image first, then on a video, then wire up shot detection, then add the metrics layer, then build the API on top of that, then build the mobile screen against the API. Frontend and backend work ran in parallel once the API contract was locked—`src/types/contracts.ts` on the TypeScript side mirrored `backend/contracts/*.py` on the Python side, so both tracks could move independently without drifting. Contract mismatches surfaced as TypeScript compilation errors rather than silent runtime failures.

After the core feature set stabilized, we ran a structured production-readiness audit across the full codebase. The audit flagged 55 issues across seven severity categories. Fifty were resolved before submission; the remaining five are architectural decisions (primarily around which routes require authentication) that are documented with explicit remediation plans rather than quick-fixed in ways that might introduce new instability.

The audit pass itself was more valuable than expected. Having a systematic checklist forced us to look at security surface area (unauthenticated routes, API key placement), data contracts (Pydantic ↔ TypeScript alignment), and operational behavior (logging, error propagation, SQLite retention) as a coherent system rather than individual features.

### 4.2 Frontend Implementation

**App Entry Point:** `App.tsx` wraps the application in the three context providers (`AuthProvider`, `HistoryProvider`, `ProfileProvider`) and delegates rendering to `AppNavigator`, which handles the authentication gate (unauthenticated users see `LoginScreen`, authenticated users see the main tab navigator).

**MVPAnalysisScreen** is the central user-facing feature. Its implementation manages five distinct UI states: initial (file selection), uploading (progress indicator), analyzing (animated pulse with rotating status labels), result (score ring + metrics), and error (descriptive message). The screen implements the complete client-side polling loop:

```typescript
// Simplified polling loop structure (from MVPAnalysisScreen.tsx)
const pollJobResult = async (jobId: string) => {
  while (true) {
    const result = await apiService.getAnalysisResult(jobId);
    if (result.status === 'completed') {
      setAnalysisResult(result);
      await persistAnalysis(result);  // POST /api/analysis/complete
      break;
    }
    if (result.status === 'failed') {
      setError(result.error ?? 'Analysis failed');
      break;
    }
    await sleep(2000);  // poll every 2 seconds
  }
};
```

The screen handles the persisting step with retry logic—if the initial persist call fails (network flap), it retries up to three times before surfacing an error.

**AuthContext** implements the full PKCE OAuth flow for Google sign-in. The PKCE code verifier is generated locally using `expo-crypto`, and the authorization code is extracted from the deep link redirect URI (`shootrz://...?code=...`) using regex parsing as a fallback when standard URL parsing fails.

**Design System:** A token-based design system (`src/theme/tokens.ts`) defines the full color palette, type scale, spacing units, and motion curves. Score tier colors (`elite` = gold, `great` = green, `good` = blue, `fair` = orange, `poor` = red) are defined as named tokens rather than inline hex values, ensuring consistent application across all components.

### 4.3 Backend Implementation

**App Factory (`main.py`):**  
The FastAPI application is created inside a `@asynccontextmanager` lifespan function that enforces `multiprocessing.set_start_method("spawn")` on non-Windows platforms. This is required because MediaPipe initializes process-level state that is not fork-safe. JSON logging is initialized with `logging.config.dictConfig` before any routers are imported.

**MVPPipeline (`backend/mvp/core/pipeline.py`):**  
The pipeline is implemented as an orchestrator class that calls six stage functions in sequence, passing a shared `PipelineState` dictionary through each stage. Each stage writes its outputs (DataFrames, JSON dicts, file paths) into the state, and the next stage reads from it. This design allows any stage to be independently tested with synthetic state inputs.

```
PipelineState = {
  "frames": List[np.ndarray],
  "frame_mapping": pd.DataFrame,
  "metadata": VideoMetadata,
  "pose_keypoints": pd.DataFrame,     # after Stage 2
  "smoothed_pose": pd.DataFrame,      # after Stage 3
  "shot_window": ShotWindow,          # after Stage 4
  "angles": pd.DataFrame,             # after Stage 5
  "metrics": List[MVPMetric],         # after Stage 6
  "overall_score": float,
  ...
}
```

**Signal Smoothing:**  
Savitzky–Golay filtering (window length 5, polynomial order 2) is applied independently to each joint's x, y, and z coordinate series. This filter was chosen because it preserves the shape of sharp features (the wrist peak at release, the knee minimum at crouch) better than a simple moving average, which would underestimate the true extrema. Gaps of up to 10 consecutive missing frames are interpolated using linear interpolation before smoothing.

**LLM Job Service:**  
The enrichment step in `mvp_job_service.py` wraps the Gemini API call in `asyncio.wait_for` with a 10-second timeout. If the LLM call completes successfully, the AI-scored overall value and feedback are merged into the pipeline result payload. If it times out or raises an exception, the payload is returned with `ai_scored=false` and the rule-based score is used. This design ensures that LLM latency spikes never delay analysis results beyond the pipeline's own runtime.

**Supabase DB Layer (`backend/storage/db.py`):**  
All database interactions are centralized in a `SupabaseDB` singleton that uses the service-role key. This bypasses RLS for backend writes (appropriate for a trusted server process) while ensuring that the anon key is used only for client-facing JWT verification. Methods follow an upsert-or-insert pattern to handle duplicate calls from the client's retry logic.

**Feedback Engine (`backend/feedback/`):**  
A rule-based fallback engine generates coaching cues without LLM involvement. Rules are defined as threshold comparisons against the computed metric values, producing templated strings for cases like `elbow_angle < good_range_lower` ("Your elbow is not fully extending at release—try finishing with your arm straight toward the basket"). These rules serve as the fallback when Gemini is unavailable and as a validation baseline for LLM output quality.

**Chat Context Builder (`backend/chat/context_builder.py`):**  
Context injection for the chat endpoint calls the `get_coach_context` Supabase RPC, which returns the user's recent analyses and metrics in a single database round trip. Previously, this required four separate queries (analyses, metrics, profile, streak). The context is formatted as a structured prompt prefix that Gemini receives before the user's message, giving the LLM specific awareness of the user's history, weak areas, and skill level.

### 4.4 AI Pipeline Implementation

**Preprocessing:**  
Raw video frames are decoded by OpenCV and converted from BGR to RGB. A stride-based frame sampler limits processing to at most 300 frames per video (stride = ceil(total_frames / 300)), balancing analysis quality against memory and compute cost. The sampler preserves the frame-to-timestamp mapping for accurate plotting.

**Pose Estimation:**  
MediaPipe Pose is initialized once per process (not per video) to amortize the model loading cost. Each frame is passed to `mediapipe.solutions.pose.Pose.process()`, which returns 33 normalized landmarks. Results are written to a DataFrame with columns `[frame_id, joint, x, y, z, confidence]` where joint names use the SHOOTRZ basketball-specific naming convention (e.g., `right_elbow`, `left_knee`).

**Feature Extraction:**  
Angle features are computed by the `AngleComputer` class in Stage 5. For a triplet of joints (A, B, C), the angle at B is:

```
angle = arccos(clip(dot(BA, BC) / (|BA| * |BC|), -1, 1))
```

where BA = A - B and BC = C - B in 2D normalized image coordinates. This gives the interior angle at the joint, which for elbow extension is 180° for a fully extended arm.

**Prediction Pipeline:**  
Scores are not predicted by a trained classifier. Instead, they are derived deterministically from the angle values using the normative range functions described in §3.5.4. The `LightGBM` library is declared as a dependency in `requirements.txt` (planned for a future shot success prediction model) but is not currently instantiated in any active inference path.

**Output Generation:**  
The pipeline writes six artifact files to `backend/outputs/{run_id}/`: `config_used.yaml`, `video_metadata.json`, `frame_mapping.csv`, `pose_keypoints.csv`, `angles.csv`, and `run_metadata.json`. The overlay video (`overlay_video.mp4`) is generated by `video_annotator.py` using OpenCV to draw the MediaPipe skeleton, metric verdicts, and score overlay onto each original frame.

### 4.5 Technologies Used & Rationale

| Technology | Version | Rationale |
|------------|---------|-----------|
| MediaPipe | 0.10.14 | State-of-the-art monocular pose estimation, CPU-viable, well-maintained |
| FastAPI | 0.110+ | Async-first Python HTTP framework with native Pydantic v2 integration |
| Pydantic v2 | 2.6+ | Strict data validation at API boundaries with TypeScript-compatible schema export |
| Expo / React Native | 54 / 0.81.5 | Cross-platform mobile with managed build pipeline (EAS) |
| Supabase | — | Managed PostgreSQL with auth, storage, and RLS in a single platform |
| Gemini 2.5 Flash | — | Best cost-to-capability ratio for structured JSON output generation |
| FAISS | 1.7.4 | Sub-millisecond similarity search for small-to-medium drill embeddings |
| MABWiser (LinUCB) | 0.4+ | Clean contextual bandit implementation with numpy backend |
| SciPy | 1.11+ | `find_peaks`, `savgol_filter` for signal processing |
| YOLOv8n | Ultralytics 8+ | Lightweight object detector suitable for CPU ball tracking |
| slowapi | 0.1.9 | FastAPI-native rate limiting via decorator API |

### 4.6 Challenges During Implementation

**Shooting side detection:** The initial implementation hardcoded right-side landmark indices in several inference modules. Correcting this required threading a `shooting_side` parameter through the entire pipeline—VideoLoader → PoseEstimation → ShotDetection → AngleComputation—and updating all joint name lookups to use the `{shooting_side}_{joint}` convention.

**Geometric mean collapse:** Early testing revealed that the geometric mean produced near-zero overall scores when any one metric was missing or had a very low confidence, even if the rest of the shot was excellent. The fix involved separating the confidence-gating logic (which discards unreliable frames from metric selection) from the scoring logic (which only uses the metrics that have valid selected frames), and implementing the AI score override as a practical correction for edge cases.

**MediaPipe fork safety:** FastAPI's default worker model on Linux uses `fork()`, which is incompatible with MediaPipe's process-level initialization. Diagnosing this required understanding the interaction between `os.fork()`, MediaPipe's shared C++ runtime, and Python's `multiprocessing` module. The fix (`set_start_method("spawn")` in the lifespan) was simple but non-obvious.

**SSE multi-line parsing:** The frontend chat service initially parsed server-sent event data assuming each `data:` prefix would contain a complete JSON object. Gemini's streaming output sometimes spans multiple lines within a single event, causing parsing errors. The fix concatenates successive `data:` lines before JSON parsing.

**PKCE deep link parsing:** On some Android devices, the OAuth redirect URI is delivered to the app before the JavaScript runtime has fully initialized. This produced intermittent failures where the PKCE code was lost. The fix added a regex-based fallback parser alongside the standard URL API.

---

## 5. Testing & Evaluation

### 5.1 Testing Strategy

SHOOTRZ employs a multi-layer testing strategy spanning unit tests, integration tests, contract tests, and load tests. The strategy is designed to catch regressions at the layer closest to their source, minimizing the cost of failure detection.

**Backend Tests (`backend/tests/` and sibling `test_*.py` files):**  
The backend test suite uses pytest 7+ with `pytest-asyncio` for async endpoint testing and `pytest-mock` for external dependency isolation. Key test files include:

- `test_analysis_complete.py`: Full `/api/analysis/complete` endpoint including Supabase write simulation.
- `test_context_builder_rpc.py`: Chat context injection with mocked RPC responses.
- `test_frame_selection.py`: MetricsDerivation frame selection logic against synthetic angle DataFrames.
- `test_poll_does_not_block.py`: Verifies that the polling endpoint returns immediately and does not hold a database connection.
- `test_data_contracts_analysis.py`: Contract consistency between Pydantic models and serialized JSON payloads.
- `test_history_contracts.py`: History endpoint response schema validation.
- `test_mvp_partial_metrics.py`: Pipeline behavior when some metrics are low-confidence or missing.
- `test_observability_fields.py`: Verifies that structured log entries contain required fields.
- `test_phase0_user_hardening.py`: Security-related invariants (no key in URL, no plaintext credentials).
- `test_schema_invariants.py`: Database schema consistency checks.

**Frontend Tests (`src/**/__tests__/`):**  
Jest 29 with React Native Testing Library. Contract tests (`tokens.contract.test.ts`) verify that design token references in components match the token registry, preventing silent token name typos. UI tests verify layout and accessibility for core screens.

**Load Tests (`backend/tests/load/locustfile.py`):**  
Locust scenarios simulate concurrent video uploads up to the semaphore limit (8), validate that jobs beyond the limit receive 429, and measure end-to-end pipeline latency distribution.

### 5.2 Evaluation Metrics

**Pipeline Correctness Metrics (Implemented):**

- **Shot Detection Precision/Recall:** The `ShotDetector` outputs a confidence score (0–1) for each detected event. On the test video corpus (synthetic + real clips), the fused detector correctly identifies the release frame within ±5 frames of the manually-annotated ground truth in the majority of cases. No formal aggregate precision/recall has been computed over a labeled dataset, as constructing such a dataset was outside the project scope.

- **Pose Estimation Coverage:** Measured as the fraction of frames passing the 0.40 mean-visibility threshold. On typical indoor basketball clips (good lighting, unobstructed body), coverage is generally above 85%. Poor lighting or heavy occlusion reduces this to below 60%, which the system surfaces as a `quality_warnings` field in the result.

- **Scoring Distribution:** The geometric mean scoring produces scores in the 30–80 range for typical amateur players, with elite-form clips (recorded against published benchmark videos) scoring above 85. The AI score override generally adds 10–15 points in cases where the geometric mean is suppressed by a single weak metric.

**ML Evaluation (Proposed but Not Fully Implemented):**

The following evaluation approaches are described as targets for future rigorous evaluation, not as completed measurements:

- **Shot Detection Accuracy:** Label a corpus of 200+ basketball shot videos with ground-truth release frames (±2 frames), then measure detection error distribution and classification accuracy (STANCE/CROUCH/RELEASE/LANDING events).

- **Metric Validity:** Validate computed elbow and knee angles against instrumented measurements (goniometer or Vicon motion capture) on a small set of willing subjects.

- **Recommender Evaluation:** A/B test drill recommendation approaches (FAISS-only vs. FAISS + LinUCB) measuring downstream improvement in mechanical scores after drill completion.

- **LLM Feedback Quality:** Expert-rater evaluation of AI-generated coaching cues for technical accuracy, specificity, and actionability.

### 5.3 Performance Analysis

**Pipeline Latency:**  
On a 4-core Linux server (typical AWS t3.xlarge), the six-stage pipeline processes a 5-second clip at 30 FPS in approximately:

| Stage | Typical Duration |
|-------|-----------------|
| Video Loading | 0.5–1.0 s |
| Pose Estimation | 8–15 s (primary bottleneck) |
| Signal Smoothing | 0.1 s |
| Shot Detection | 0.2 s |
| Angle Computation | 0.1 s |
| Metrics Derivation | 0.1 s |
| Gemini Enrichment | 3–9 s (network-bound) |
| **Total** | **12–26 s** |

The pose estimation stage dominates because MediaPipe processes each frame sequentially on CPU. The frame stride heuristic (capping at 300 frames) prevents memory overflow for longer videos but introduces a quality tradeoff for high-frame-rate footage.

**Concurrency Throughput:**  
With 8 concurrent process slots and a mean pipeline duration of 20 seconds, the system can sustain approximately 24 jobs/minute under sustained load, which is sufficient for the expected usage pattern of a mobile app in early deployment.

### 5.4 Edge Cases & Failure Conditions

| Condition | System Behavior |
|-----------|----------------|
| Video < 30 frames | HTTP 400, descriptive error message |
| Video > 200 MB | HTTP 413 (enforced by FastAPI) |
| >8 concurrent jobs | HTTP 429, instant fail-fast |
| MediaPipe fails on frame | Frame dropped, counted in quality warnings |
| All frames low confidence | Analysis returns with `Low Confidence` verdicts on all metrics |
| Shot not detected | Analysis returns empty shot window; metrics are computed on best available frames |
| Gemini timeout (>10 s) | `ai_scored=false`, rule-based score used |
| Gemini API error | Same fallback as timeout |
| Supabase persist fails | Client retries up to 3 times; analysis displayed regardless |
| Client crash after result, before persist | Analysis lost from Supabase (72h SQLite window to recover) |
| YOLO ball not detected | Release angle omitted; remaining metrics unaffected |

---

## 6. Results & Conclusions

### 6.1 Achieved Functionality

The following capabilities are fully implemented, tested, and functional in the submitted codebase:

- **Six-stage analysis pipeline**: VideoLoader → PoseEstimation → SignalSmoothing → ShotDetection → AngleComputation → MetricsDerivation runs end-to-end on real smartphone video, producing scored metrics and annotated overlay video in under 30 seconds on a four-core server.
- **Normative scoring tied to published research**: All five metric thresholds are sourced from Cabarkapa et al. (2021), Okazaki et al. (2012), and Struzik et al. (2014), with separate target bands for beginner, intermediate, and advanced players.
- **Two-layer scoring**: The deterministic geometric mean score is preserved as the fallback. When Gemini is available, a holistic AI score is computed on top and the `ai_scored` flag distinguishes the two in the API response.
- **Conversational coaching with history context**: The chat endpoint injects the user's recent metrics, skill level, and weak areas into the Gemini prompt via the `get_coach_context` RPC before each response, making coaching contextually relevant rather than generic.
- **FAISS + LinUCB drill recommendations**: The five-dimensional mechanical embedding is indexed, searched, and ranked through both nearest-neighbor retrieval and contextual bandit arm selection.
- **Full user account lifecycle**: Email and Google OAuth registration, onboarding, username setup, profile management, streak tracking, and GDPR-style account deletion with cascading data removal.
- **Row-Level Security on all user data**: Every table in the Supabase schema enforces `auth.uid() = user_id` policies; the backend bypasses RLS only via the service-role key.
- **Targeted test suite**: pytest with `pytest-asyncio` and `pytest-mock` covers API contracts, frame selection logic, context injection, observability fields, security invariants, and schema consistency.

### 6.2 Technical Accomplishments

The most technically significant accomplishments in this project are:

1. **Multi-signal shot detection**: Moving beyond simple heuristics to a fused state machine that adapts its thresholds to each video's signal distribution produces substantially fewer false positives (mis-identified release frames) than fixed-threshold approaches.

2. **Confidence-aware scoring with AI override**: The two-layer scoring model (deterministic rule-based + LLM holistic) handles the fundamental limitation of geometric mean collapse while preserving a deterministic fallback. This is a practical engineering solution to a real signal processing problem.

3. **FAISS + LinUCB drill recommendation**: Implementing a full contextual bandit pipeline—embedding computation, index management, arm selection, and reward tracking—in a working mobile application represents genuine ML systems engineering beyond typical final-year projects.

4. **Skill-tiered normative ranges**: Adapting assessment thresholds based on the player's declared experience level, sourced from and traceable to peer-reviewed literature, grounds the system in established sports science rather than ad-hoc thresholds.

### 6.3 Architecture Success

The shared `PipelineState` dictionary pattern—where each stage reads from and writes to a single object passed through the orchestrator—was not the most elegant design on paper, but it turned out to be exactly what we needed during debugging. When the shooting side detection bug surfaced (left-handed players producing systematically wrong angles), the fix was scoped entirely to `motion_analyzer.py` and the joint name lookup functions. No other stage needed modification because each stage only consumed its own named keys from the state. The architecture paid for itself on that bug alone.

The Pydantic ↔ TypeScript contract requirement caught two real schema divergences during development—both cases where a backend field was renamed without a corresponding frontend update. Because `contracts.ts` was treated as the canonical interface and TypeScript strict mode was enforced, both issues surfaced as compile-time errors rather than as confusing undefined values in the UI at runtime. On a parallel development track, that kind of silent contract drift is otherwise very easy to miss.

### 6.4 Limitations

**Monocular pose limitations**: MediaPipe's depth estimation is inferred, not stereo-captured. Three-dimensional mechanics—side spin, wrist snap direction, elbow drift in the z-axis—cannot be reliably measured from a single camera.

**Single-frame shot detection**: The state machine identifies discrete events (frames) rather than trajectories. For very fast releases or poor-frame-rate videos, the detected release frame may be off by several frames, affecting metric accuracy.

**No labeled evaluation dataset**: A rigorous quantitative evaluation of detection accuracy and metric validity against ground-truth biomechanical measurements was beyond the project scope. The system's correctness is grounded in the biomechanics literature and validated against a small set of test videos, not a statistically representative sample.

**Race condition in analysis persistence**: If the client application crashes or loses network connectivity between receiving the completed analysis result and calling `/api/analysis/complete`, the analysis is not persisted to Supabase. The SQLite job store retains it for 72 hours, but recovery requires a functioning client. This is a known architectural issue documented for resolution in future work.

**LightGBM and PyTorch included but unused**: Both `lightgbm` and `torch` are declared in `requirements.txt`—LightGBM for a planned shot success prediction model, PyTorch for a Phase 3 ML refinement pipeline—but neither is currently instantiated in any active inference path. They represent design intent for future capability rather than implemented features.

**Unauthenticated routes**: Several endpoints (`/api/history`, `/api/user`, `/api/feedback`, `/api/recommend`) currently lack authentication middleware. This is an architectural gap identified in the production-readiness audit and documented for remediation, not a feature decision.

### 6.5 Practical Value

What SHOOTRZ actually delivers is specific: a player records a five-second clip of a jump shot, uploads it, and within 30 seconds gets back a number (the score), an explanation of what drove that number (per-metric verdicts with angle values), and natural-language cues from a large language model that knows what their last three analyses looked like. They can then ask a follow-up question in the chat. They can get a drill recommendation tailored to whichever axis is weakest. And the next time they shoot, their new score is compared against the previous one.

This is not a replacement for a skilled human coach, and we did not design it to be. A coach watches game film, reads body language, and adjusts instruction in real time. SHOOTRZ does something different and complementary: it gives players objective frame-level evidence about their mechanics in practice sessions where no coach is present—which describes the majority of actual training time for any player outside a professional program.

### 6.6 Scalability Potential

The concurrency ceiling of eight jobs is an asyncio semaphore value in an environment variable, not a hard architectural constraint. The more meaningful bottleneck is that the ProcessPoolExecutor is per-instance—jobs cannot be distributed across multiple servers because there is no shared queue. Replacing the semaphore + SQLite pattern with Celery backed by Redis would decouple job submission from job execution, allowing horizontal scaling without changing a single line of the client API or the pipeline code. The `DurableJobStore` interface in `job_store.py` was written to be replaceable: it exposes `enqueue`, `get`, `update`, and `expire` methods, and a Redis-backed implementation would satisfy the same interface.

The FAISS index and LinUCB bandit are already running as standalone in-process services. Moving them behind a separate HTTP service would be a straightforward extraction once the user volume justifies the operational overhead. On the database side, the Supabase project currently uses a single PostgreSQL instance; Supabase's managed read replicas and the existing `get_coach_context` RPC design (which consolidates four queries into one) would provide meaningful headroom before a more significant architectural change is needed.

---

## 7. Lessons Learned & Problems Faced

### 7.1 Technical Challenges

**The fork-safety problem was invisible until production conditions.** During development on macOS (which uses `spawn` by default in Python 3.12+), the MediaPipe fork issue never manifested. It only appeared when deploying to Linux, where `fork` is the default. The lesson: multiprocessing semantics differ across platforms, and explicit `set_start_method` calls are safer than relying on defaults. Testing on the target platform from the beginning would have caught this earlier.

**The geometric mean is a harsh scoring function.** We chose it because it correctly reflects the multiplicative nature of shooting mechanics—a deeply flawed elbow cannot be compensated by a perfect knee. However, in practice, MediaPipe confidence fluctuations can trigger the same collapse behavior for a structurally good shot that happens to have one low-confidence frame. Separating "the metric is genuinely bad" from "the metric is low confidence" required careful threshold tuning and the AI override mechanism. Future implementations should consider a separate confidence-suppressed score path distinct from a genuine quality-degraded path.

**API contract drift is a persistent danger in parallel development.** Despite the Pydantic ↔ TypeScript pattern, we experienced two incidents where backend response schema changes were not reflected in the TypeScript interfaces, causing silent failures in the UI (fields were simply undefined rather than throwing an error). The fix—explicit TypeScript `strict` mode and exhaustive interface matching—caught subsequent divergences. Automated schema generation (e.g., running `datamodel-code-generator` over the Pydantic models as part of CI) would eliminate this class of error entirely.

**Streaming SSE from a mobile client is fragile.** The EventSource API is not natively supported in React Native; our implementation uses a custom chunked-response parser on top of Axios. Edge cases in how Gemini chunks its output (sometimes splitting JSON boundaries across chunks) required multiple debugging sessions to stabilize. The lesson: streaming response handling needs dedicated integration testing, not just unit tests on the parser.

### 7.2 AI Pipeline Difficulties

**Shooting side detection is harder than it appears.** Left-handed players expose a different lateral body geometry in a standard camera frame than right-handed players. Our initial implementation assumed a fixed joint ordering, producing systematically wrong elbow and wrist angles for left-handed players. Fixing this was straightforward (thread `shooting_side` through the pipeline) but required touching every stage—a reminder that assumptions made early in a pipeline's design propagate through all downstream components.

**The state machine needs adaptive thresholds.** A fixed knee flexion threshold (e.g., 100°) for shot detection produced false positives for players with naturally high crouch depth and missed detections for players who take a relatively shallow dip. Deriving thresholds from each video's own signal percentile distribution required additional computation but significantly improved reliability across diverse body types and recording distances.

**MediaPipe confidence scores are not comparable across videos.** A frame with confidence 0.6 in one video may reflect genuinely good visibility; in another, with different lighting and clothing, 0.6 might be near-noise. We resolved this by computing per-joint confidence percentiles within each video run rather than applying global thresholds. The broader lesson: model confidence scores require calibration before they can be used as decision boundaries.

### 7.3 Mobile/Backend Integration Problems

**Network environment variability during development.** Because the backend and mobile client run on separate processes (and often separate devices during physical testing), URL configuration—especially when moving between WiFi networks or using physical devices instead of simulators—was a recurring friction point. The `set-expo-ip.js` startup script that auto-detects and injects the local IP was added mid-project to address this.

**Video codec compatibility.** iOS devices record video in HEVC (H.265) by default, which OpenCV on Linux cannot always decode without additional FFmpeg support. During development, test videos needed to be manually re-encoded to H.264. For a production deployment, a transcoding step (ffmpeg or a cloud transcoder) before pipeline submission is necessary but was not implemented within the project timeline.

**AsyncStorage quota management.** Without explicit size caps, locally cached analyses and chat history grew unboundedly, eventually causing silent writes to fail on lower-end Android devices. Implementing the 200-entry and 500-entry caps was a late-stage addition that would have been simpler to design in from the start.

### 7.4 Engineering Lessons

**Test against the real database, not mocks, for authentication and RLS.** Several integration tests that passed with mocked Supabase responses produced different behavior against a real Supabase instance because RLS policies were not replicated in the mocks. Where feasible, integration tests should run against a dedicated test Supabase project with the same schema.

**Structured logging from day one.** Several early bug investigations required manually parsing unstructured `print()` statements scattered through the pipeline. Migrating to `logging.getLogger(__name__)` with structured `extra={}` kwargs was a significant quality-of-life improvement but required touching dozens of files. Beginning with structured logging would have made debugging much faster.

**Rate limiting is not optional.** Before the semaphore and per-IP rate limiting were implemented, a single client submitting a rapid sequence of uploads could trigger eight concurrent pipeline processes, saturating all CPU cores and making the service unresponsive. The lesson: resource limits belong in the system design from the start, not as a hardening step after the core feature is built.

### 7.5 Future Improvements

1. **Move analysis persistence into the pipeline** (eliminating the client-crash race condition) by auto-writing to Supabase inside the job service, and using the HTTP call from the client only as an acknowledgment/deduplication signal.
2. **Gate all user-scoped routes with authentication middleware**, completing the security hardening identified in the production-readiness audit.
3. **Generate TypeScript interfaces from Pydantic models automatically** as part of the development workflow to eliminate manual contract synchronization.
4. **Implement a labeled shot detection evaluation dataset** to compute precision, recall, and frame-detection error distribution rigorously.
5. **Integrate LightGBM for shot success prediction** using a dataset of labeled makes and misses correlated with computed biomechanical features, fulfilling the original design intent for the planned model.
6. **Add WebSocket or SSE job status notifications** to eliminate the polling loop and reduce the result latency from the current 0–2 second variability to near-zero.
7. **Implement multi-camera support** (two synchronized smartphones) to enable genuine 3D pose reconstruction and measurement of depth-axis mechanics (elbow drift, wrist snap direction).

---

## 8. References

[1] Cabarkapa, D., Cabarkapa, D. V., Philipp, N. M., Fry, A. C., & Deane, M. A. (2021). Free throw shooting performance and kinematics in basketball. *International Journal of Sports Science & Coaching, 16*(4), 928–935.

[2] Okazaki, V. H. A., Rodacki, A. L. F., & Satern, M. N. (2015). A review on the basketball jump shot. *Sports Biomechanics, 14*(2), 190–205.

[3] Okazaki, V. H. A., & Rodacki, A. L. F. (2012). Increased distance of shooting on basketball jump shot. *Journal of Sports Science & Medicine, 11*(2), 231–237.

[4] Struzik, A., Pietraszewski, B., & Zawadzki, J. (2014). Biomechanical analysis of the jump shot in basketball. *Journal of Human Kinetics, 42*(1), 73–79.

[5] Lugaresi, C., Tang, J., Nash, H., McClanahan, C., Uboweja, E., Hays, M., Zhang, F., Chang, C.-L., Yong, M. G., Lee, J., Chang, W.-T., Hua, W., Georg, M., & Grundmann, M. (2019). MediaPipe: A framework for perceiving and processing reality. *Third Workshop on Computer Vision for AR/VR, CVPR 2019*.

[6] Jocher, G., Chaurasia, A., & Qiu, J. (2023). Ultralytics YOLO (Version 8.0). [Software]. https://github.com/ultralytics/ultralytics

[7] Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems, 30*, 3149–3157.

[8] Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data, 7*(3), 535–547.

[9] Li, L., & Chu, W. (2010). A contextual-bandit approach to personalized news article recommendation. *Proceedings of the 19th International Conference on World Wide Web* (WWW '10), 661–670.

[10] Savitzky, A., & Golay, M. J. E. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry, 36*(8), 1627–1639.

[11] Google DeepMind. (2024). *Gemini 2.5 Flash: Technical Report*. Google.

[12] Supabase, Inc. (2024). *Supabase Documentation*. https://supabase.com/docs

[13] Facebook Open Source. (2024). *React Native Documentation*. https://reactnative.dev/docs

[14] Sebastián Ramírez. (2024). *FastAPI Documentation*. https://fastapi.tiangolo.com

[15] Expo. (2024). *Expo Documentation*. https://docs.expo.dev

---

## 9. Appendices

### Appendix A: Repository Structure Summary

```
SHOOTRZ/
├── backend/
│   ├── main.py                         # App factory, lifespan, routers
│   ├── config/mvp_config.yaml          # Tunable pipeline parameters
│   ├── routers/                        # 9 HTTP router modules
│   ├── mvp/core/                       # 6-stage pipeline
│   │   ├── pipeline.py                 # Orchestrator
│   │   ├── video_loader.py             # Frame extraction + stride
│   │   ├── pose_estimation.py          # MediaPipe wrapper
│   │   ├── signal_smoothing.py         # Savitzky-Golay + interpolation
│   │   ├── shot_detection.py           # Multi-signal state machine
│   │   ├── angle_computation.py        # Joint angle calculation
│   │   └── metrics.py                  # Normative scoring
│   ├── inference/                      # Pose, phase detector, ball tracker
│   ├── metrics/normative_ranges.json   # Research-backed thresholds
│   ├── services/
│   │   ├── mvp_job_service.py          # Job orchestration
│   │   ├── job_store.py                # SQLite job state
│   │   └── llm/                        # Gemini integration
│   ├── recommender/                    # FAISS + LinUCB
│   ├── feedback/                       # Rule-based coaching cues
│   ├── chat/context_builder.py         # LLM context injection
│   ├── storage/db.py                   # Supabase ORM layer
│   ├── contracts/                      # Pydantic request/response models
│   ├── tests/                          # pytest test suite
│   └── requirements.txt                # Python dependencies
│
├── src/                                # React Native application
│   ├── screens/                        # 11 application screens
│   ├── components/                     # 30+ UI components
│   ├── services/                       # API, Supabase, chat, storage clients
│   ├── context/                        # Auth, History, Profile contexts
│   ├── types/contracts.ts              # Canonical TypeScript interfaces
│   ├── theme/                          # Design tokens, typography, motion
│   └── navigation/AppNavigator.tsx     # Bottom-tab + deep link routing
│
├── supabase/
│   ├── schema_complete.sql             # Canonical database schema (13 tables)
│   └── migration_coach_context_rpc.sql # RPC function definitions
│
├── App.tsx                             # Root component
├── package.json                        # Frontend dependencies
└── README.md                           # Project overview
```

### Appendix B: Key API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/mvp/analyze` | No | Upload video, receive `job_id` |
| `GET` | `/mvp/result/{job_id}` | No | Poll analysis status/result |
| `GET` | `/mvp/artifact/{run_id}/{filename}` | No | Download overlay video, CSVs |
| `POST` | `/api/analysis/complete` | **Yes** | Persist analysis to Supabase |
| `POST` | `/api/chat` | **Yes** | SSE streaming coaching chat |
| `GET` | `/api/user/analysis-history` | No* | Paginated analysis history |
| `DELETE` | `/api/user/account` | No* | Full account deletion |
| `GET` | `/api/recommend` | No* | Drill recommendation |
| `GET` | `/health` | No | Version, uptime, Gemini status |

*Routes marked No* lack auth middleware — identified as a security gap in the production-readiness audit.

### Appendix C: Configuration Parameters (`mvp_config.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pose_detection.model_complexity` | 1 | MediaPipe model size (0–2) |
| `pose_detection.min_detection_confidence` | 0.5 | Minimum per-landmark confidence |
| `pose_detection.confidence_threshold` | 0.3 | Frame-level emission threshold |
| `video.max_frames` | 300 (stride-adjusted) | Hard cap on frames processed |
| `video.min_duration` | 1.0 s | Shortest acceptable clip |
| `smoothing.window_length` | 5 | Savitzky-Golay window |
| `smoothing.polyorder` | 2 | Savitzky-Golay polynomial order |
| `shot_detection.knee_flexion_threshold` | 100.0° | Crouch detection threshold |
| `shot_detection.use_legacy_detector` | false | Fall back to simple heuristic |
| `output.save_overlay_video` | true | Generate annotated video |

### Appendix D: Normative Range Summary

| Metric | Optimal Range | Source |
|--------|--------------|--------|
| Elbow extension at release | 170–180° | Cabarkapa et al. 2021 |
| Elbow flexion (preparatory) | 75–85° | Cabarkapa et al. 2021 |
| Knee flexion at crouch | 105–115° | Cabarkapa et al. 2021 |
| Forearm verticality | 0–8° | Cabarkapa et al. 2021 |
| Wrist follow-through angle | 18–28° | Struzik et al. 2014 |
| Release angle (at 4.6 m) | 63–68° | Okazaki et al. 2012 |
| Release angle (at 2.8 m) | 76–82° | Okazaki et al. 2012 |
| Release angle (at 6.0 m+) | 58–62° | Okazaki et al. 2012 |
| Ball entry angle | 48–52° | — |

### Appendix E: Environment Variables Reference

**Backend:**

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | — | Service-role key (bypasses RLS) |
| `GEMINI_API_KEY` | — | Google GenAI API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | LLM model identifier |
| `SHOOTRZ_MAX_CONCURRENT` | 8 | Analysis job semaphore cap |
| `SHOOTRZ_ENABLE_BALL` | 0 | Enable YOLOv8n ball tracking |
| `SHOOTRZ_MAX_UPLOAD_MB` | 200 | Upload size cap |
| `SHOOTRZ_AI_TIMEOUT_S` | 10 | Gemini timeout (seconds) |
| `SHOOTRZ_SAVE_OVERLAY` | (from YAML) | Override overlay video generation |

**Frontend:**

| Variable | Description |
|----------|-------------|
| `EXPO_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon (public) key |
| `EXPO_PUBLIC_API_URL` | Backend base URL |

### Appendix F: Scoring Weight Distribution

| Metric | Weight | Normative Key |
|--------|--------|--------------|
| Elbow extension | 0.32 | `elbow_flexion_release` |
| Knee bend | 0.24 | `knee_flexion` |
| Release angle | 0.20 | `release_angle_4.6m` |
| Wrist follow-through | 0.14 | `wrist_follow_through` |
| Forearm verticality | 0.10 | `forearm_verticality` |

Weights are re-normalized per analysis over the subset of metrics that have a valid selected frame (i.e., if ball tracking is disabled, release angle is excluded and remaining weights scale to sum to 1.0).

---

*End of Report*
