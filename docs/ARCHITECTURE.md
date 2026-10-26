# Architecture

The React client uses Axios through Vite's `/api` proxy. FastAPI validates request bodies with Pydantic, persists records with SQLAlchemy in SQLite, and exposes a typed JSON API. The database file is local and Git-ignored. The assessment route reads only blood values and calls an OpenAI-compatible external chat endpoint from Python. API credentials stay in backend environment variables. Provider errors map to an honest failed status with no stored remarks.

`POST /api/patients` creates a pending record; `GET /api/patients` and `GET /api/patients/{id}` read; `PUT` replaces editable fields and clears assessment if blood values change; `DELETE` removes; `POST /api/patients/{id}/assess` requests AI remarks; `GET /api/health` reports service and configuration status. Names and emails may repeat; the integer ID is the record identity.
