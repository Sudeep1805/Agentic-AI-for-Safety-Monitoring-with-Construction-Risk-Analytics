# Agentic-AI-for-Safety-Monitoring-with-Construction-Risk-Analytics
Infosys Springboard Internship 7.0 project: Agentic AI for Safety Monitoring with Construction Risk Analytics

## Current implementation: authenticated upload dashboard MVP

React/Vite/Tailwind frontend + FastAPI backend + MySQL/SQLAlchemy persistence.
Create an account or sign in with a secure scrypt-hashed password, view a
protected profile, upload a JPEG, PNG or WebP photograph, add optional site
context, and browse saved observations. Upload success means the image and
metadata were saved, **not** analyzed. The dashboard includes responsive account
and upload/history sections; future pages are intentionally placeholders.

**Analysis unavailable:** no vision model, Site Risk Agent or scoring engine is
implemented yet. Risk scores are `null`; no mock hazards or safety conclusions are
returned. Recharts is installed for the later dashboard; charts wait for real data.

- [Windows setup and run commands](docs/setup.md)
- [Foundation verification and tests](docs/verification.md)
- [Milestone scope and next phases](docs/scope.md)
- [Scoring status and methodology constraints](docs/scoring.md)
- [Database schema](database/README.md)

```text
frontend/             React upload UI, history, interface and browser tests
backend/app/api/      Health, upload, history and image routes
backend/app/core/     Environment configuration, DB connection, request limits
backend/app/services/ Image validation and persistence
backend/app/models/   SQLAlchemy tables
backend/app/schemas/  API response contracts
backend/app/agents/   Reserved for the next-phase Site Risk Agent
backend/tests/        Validation, persistence and failure-path tests
database/             Initial schema reference
docs/                 Setup, scope, scoring and verification
scripts/              Isolated MySQL + browser verification
```

This is a local learning prototype. Start with [setup](docs/setup.md); persistent
use requires your own local `backend/.env` and initialized MySQL database. Test
verification uses an isolated database and does not configure your existing service.
