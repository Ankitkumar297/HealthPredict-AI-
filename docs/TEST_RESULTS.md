# Test results

Verified on 26 October 2026 with Python 3.12 and Node 24 after configuring `backend/.env`:

- Backend: `python -m pytest -q tests/test_api.py` — **17 passed**.
- Exact supplied ten-row workflow — **7 accepted, 3 rejected** (John Hunter, Peter Larry, Kris Wu); email update returned and persisted as `gokul@infocare.com`; deletion left **6** records.
- Frontend: `npm run build` — passed; `npm run lint` — passed.
- Running backend `GET /api/health` — `{"status":"ok","ai_configured":true}`.
- Running Vite frontend `GET /` — HTTP 200.
- The backend loaded `AI_API_KEY` from its local `.env` without exposing it. The configured model was `gemini-3.5-flash-lite` at Google's OpenAI-compatible chat-completions endpoint.
- One real Gemini assessment of a synthetic record completed successfully. The returned remarks described possible risk indicators, acknowledged missing units/reference ranges/context, and included the informational medical disclaimer. The completed remarks persisted in SQLite and were returned by `GET /api/patients/1` and through Vite's `/api` proxy.
- The production frontend bundle did not contain the configured key. `.env` is Git-ignored.
- Mocked provider tests confirmed explicit handling of invalid credentials (401), timeout, rate limit (429), and unavailable model/endpoint (404), without fabricating remarks.
- The local patient-detail route returned HTTP 200. Browser Use declined access to the local origin, so a rendered visual browser check could not be completed in this session.

The ten supplied records were verified through the normal API validation path: Robyn Pears (both copies), Darryl Tim, Sam Kerr, Madison XI, Tenille Singh, and Prem Kumar were accepted. John Hunter was rejected for email; Peter Larry for DOB; Kris Wu for DOB and email. The original invalid date remains visible in the validation error. A second Robyn record receives a distinct ID. No automatic AI assessments were attempted during this workflow.

Automated provider tests use mocks and make no paid calls. Only one live Gemini assessment was made. The backend tests use an ignored temporary SQLite database that is removed after the suite. The live synthetic record remains in the ignored local `backend/healthpredict.db` for inspection.
