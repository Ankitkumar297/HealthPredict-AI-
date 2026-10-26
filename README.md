# HealthPredict AI

Candidate 117 · Gokul Infocare Task 2

A local patient record dashboard with validated CRUD and optional external AI remarks for three blood values. The app uses synthetic demonstration data only.

## Features

- Dashboard with patient and assessment counts, recent records, and status overview.
- Searchable patient table; create, view, edit, and confirmed delete actions.
- Frontend and backend validation with original invalid inputs retained in error reports.
- Manual ten-record assessment runner, including documented duplicate handling.
- Backend-only Gemini integration with explicit pending, completed, and failed states.

## Stack

React, TypeScript, Vite, Tailwind CSS, Axios, React Router, and Lucide React; FastAPI, Pydantic, SQLAlchemy, SQLite, and HTTPX.

## Setup

Requires Python 3.11+ and Node.js 20+. From `healthpredict-ai`:

```powershell
cd backend
python -m pip install -r requirements.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://localhost:8000/docs`. The SQLite database is created automatically at `backend/healthpredict.db` and is ignored by Git. No screenshots are bundled; the interface can be demonstrated using the steps in `docs/ASSESSMENT_WALKTHROUGH.md`.

If `python` points to an installation without pip, use a specific installed interpreter for the backend commands.

## AI configuration

Copy `.env.example` to `backend/.env` and set `AI_API_KEY` locally. The default adapter uses Google's Gemini OpenAI-compatible endpoint and the configurable `gemini-3.5-flash-lite` model, which had a free tier when verified on 26 October 2026. `AI_BASE_URL` can target another compatible provider. Verify current provider availability before live use. The backend sends only glucose, haemoglobin, and cholesterol values. No name, email, or DOB is sent. Without a key, records remain pending until assessment is attempted; an attempt reports a configuration error and marks the assessment failed. No fabricated remarks are saved. Do not commit `.env`. One live synthetic assessment succeeded; see `docs/TEST_RESULTS.md`.

## Validation and duplicate policy

Dates are entered as DD/MM/YYYY. The assessment runner converts the supplied DD.MM.YYYY notation, preserving the original row in its report. Invalid dates are rejected without correction. Numeric values must be finite and non-negative. Names and emails are not unique: identical valid rows are accepted as separate records with distinct IDs. This supports the supplied duplicate Robyn Pears case.

## Test and demo

```powershell
cd backend
python -m pytest -q
cd ..\frontend
npm run build
npm run lint
```

Open **Assessment tests** to attempt the ten supplied rows. The runner shows raw input, acceptance, errors, AI attempt status, and saved IDs. Use Patients to view, edit one saved email to `gokul@infocare.com`, delete one record, and show the final list. Re-running the cases creates new valid records. AI assessment is manual on a patient's detail page.

## Limits and medical notice

The three values have no specified units, clinical reference ranges, fasting status, or patient context. AI remarks are informational only and are not a diagnosis or treatment advice. A clinician must interpret laboratory results. The app is a local assessment demonstration, not a production electronic health record. It has no authentication or encryption at rest; use synthetic records only. Running further live AI assessments requires a provider key and network access.
