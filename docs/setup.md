# Windows PowerShell setup

## Tools checked on 13 October 2026

- Python 3.12.5
- Node.js 22.17.1 and npm 10.9.2
- MySQL Community Server 8.0.41; Windows service `MySQL80` running
- MySQL binaries: `C:\Program Files\MySQL\MySQL Server 8.0\bin` (not on PATH)

Use Python 3.12 and the committed dependency locks to reproduce this environment.
The frontend uses Vite 7 and Tailwind 4's Vite plugin. Node 22.17.1 satisfies
[Vite's requirements](https://vite.dev/guide/). The integration follows the
[Tailwind Vite instructions](https://tailwindcss.com/docs/installation/using-vite)
and [FastAPI file upload API](https://fastapi.tiangolo.com/tutorial/request-files/).

Commands below do not require virtual-environment activation or changing
PowerShell execution policy. Use `npm.cmd` if PowerShell blocks `npm.ps1`.

## 1. Install the backend

```powershell
Set-Location E:\construction_agentic_ai
# Create only if it does not exist:
if (-not (Test-Path backend\.venv)) { python -m venv backend\.venv }
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
notepad backend\.env
```

Edit the MySQL connection values **locally**. Never paste credentials into chat or
commit `.env`. Quote a password in `.env` if it contains spaces or `#`, following
dotenv syntax. The application builds the SQLAlchemy URL from separate settings,
so passwords containing `@`, `:` or `/` need no URL encoding. Do not use a public
database or another project's schema for tests.

## 2. Create the application database

Open MySQL Workbench with your existing administrator account, or use the MySQL
client with an interactive password prompt:

```powershell
& 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe' -u root -p
```

Run the following SQL locally. Replace the example password with a locally chosen
password and put that same password in `backend/.env`. These statements create a
dedicated database and user; do not change the existing root password.

```sql
CREATE DATABASE IF NOT EXISTS construction_risk CHARACTER SET utf8mb4;
CREATE USER 'construction_app'@'localhost' IDENTIFIED BY 'REPLACE_LOCALLY';
GRANT SELECT, INSERT, CREATE ON construction_risk.* TO 'construction_app'@'localhost';
```

If that user already exists, use its existing password and have your local database
administrator check grants; do not blindly overwrite credentials. For this local
configuration, `MYSQL_HOST=127.0.0.1` connects through the loopback interface. Check
your server's account/host matching if it reports access denied. An administrator
can create tables using the schema reference instead, allowing the running app to
have only SELECT and INSERT privileges.

Initialize the table:

```powershell
Set-Location E:\construction_agentic_ai\backend
.\.venv\Scripts\python.exe -m app.init_db
```

This command preserves existing tables and creates the `detections` table when it
is missing. For an existing installation created before YOLO detection persistence
was added, run the additive migration in
`database\002_add_detections.sql` once using MySQL Workbench or the MySQL client.
For project management on an existing installation, also run
`database\003_add_projects.sql` once. These migrations use `CREATE TABLE IF NOT
EXISTS`; they do not drop tables or delete data. Startup itself does not create
databases or change their schema.

## 3. Run the backend (terminal 1)

```powershell
Set-Location E:\construction_agentic_ai\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Liveness: <http://127.0.0.1:8000/health>
- MySQL/schema readiness: <http://127.0.0.1:8000/health/ready>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Backend root: <http://127.0.0.1:8000/> returns API status and links. The UI runs on <http://127.0.0.1:5173>.

The MVP includes account authentication: `POST /api/auth/signup` and
`POST /api/auth/login` return short-lived bearer session tokens, and
`GET /api/auth/me` is protected. Passwords are stored using Python's memory-hard
`scrypt`; raw passwords and session tokens are never stored. The frontend keeps
the token only in browser local storage and sends it over the API connection.
For production, use HTTPS, a secure cookie-based session boundary, CSRF
protection, rate limiting, and a managed secret/session store.

Upload, history, metadata, and image-download endpoints require the authenticated
user's bearer session and only return rows owned by that user. `site_uploads.user_id`
is nullable so existing foundation rows remain migratable; legacy rows with
`NULL user_id` are intentionally not visible to authenticated users. For an
existing database, apply the commented `ALTER TABLE site_uploads` migration in
`database/001_initial.sql` before restarting the API.

Liveness can succeed while MySQL is unavailable. Readiness checks both the
connection and the upload table; it returns HTTP 503 if either is unavailable.
Write access to the upload folder is checked when saving an image.

## 4. Run the frontend (terminal 2)

```powershell
Set-Location E:\construction_agentic_ai\frontend
npm.cmd ci
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd run dev
```

Open <http://127.0.0.1:5173>. `VITE_API_BASE_URL` defaults to
`http://127.0.0.1:8000`. The backend allows the localhost and 127.0.0.1 frontend
origins on port 5173. If you change ports, update the frontend URL and backend
`CORS_ORIGINS` together, then restart both services. `VITE_` variables are public:
never place credentials in them. The dev server refuses an occupied port rather
than silently switching to an origin that CORS will reject.

## 5. Try an upload

1. Choose a still JPEG, PNG or WebP photograph, up to 10 MiB and 25 million pixels.
2. Confirm the preview; optionally enter up to 2,000 characters of site context.
3. Select **Save observation** and wait for **Upload saved successfully**.
4. Reload the page and select the saved observation to see persisted metadata.

The UI's “10 MB” label means 10 × 1024 × 1024 bytes. The backend's default limit
is configurable; the current frontend guidance uses these default limits.
Backend validation is authoritative. Original images are retained byte-for-byte,
including any embedded EXIF/location metadata. Upload only images you intend to
store. Test images are not actual hazard examples.

The result explicitly states **Analysis unavailable** and **Risk score: Not
assessed**. There are no AI keys to configure in this phase. Later work must add
and evaluate a vision adapter, LangGraph agent, retrieval and scoring before
analysis can become available; entering an API key alone will not enable it.

## Troubleshooting

- **Setup required / database unavailable:** check the MySQL service, local `.env`,
  database/user grants, and `python -m app.init_db`. No fallback database is used.
- **Cannot reach API:** start FastAPI and check its URL and allowed CORS origins.
- **HTTP 413:** reduce file size; request limits include a small multipart allowance.
- **HTTP 415:** ensure extension and MIME type match JPEG, PNG or WebP content.
- **HTTP 422:** re-export corrupt, truncated, animated or oversized-pixel images;
  shorten site context if needed.
- **HTTP 503 saving an image:** check database availability and folder write access.
- **Timed-out request:** refresh history before retrying; a commit may have completed
  even if its response was lost. Automatic idempotency is not implemented yet.

The application currently binds to loopback. Upload/history remains compatible
with the original foundation flow, while profile access requires authentication.
Keep it local; adding shared or public hosting requires production access-control
and deployment configuration. Stop each development service with Ctrl+C.

## Review and commit when ready

No commit or push is performed automatically.

```powershell
Set-Location E:\construction_agentic_ai
git status --short
git diff -- README.md
git add .gitignore README.md frontend backend database docs scripts
git diff --cached --stat
git diff --cached --check
git diff --cached
# Confirm no .env, uploads, model weights, .local, or dependencies are staged.
git commit -m "Implement image upload foundation for site risk monitoring"
git push
```
