# Foundation verification

Verified on Windows on **13 October 2026**. This verifies upload/data handling,
not hazard recognition or risk scoring.

| Check | Observed result |
| --- | --- |
| Backend validation/failure tests using SQLite for fast isolation | 21 passed |
| Same backend tests against isolated MySQL 8.0.41 | 21 passed |
| React interaction tests (Vitest) | 5 passed |
| Real Edge browser/API tests (Playwright) | 2 passed |
| Vite production build | Passed |
| npm dependency audit after test-runner update | 0 known vulnerabilities reported |
| Python dependency consistency (`pip check`) | Passed |
| Desktop and 390px mobile rendering | Screenshots reviewed; no horizontal overflow |

The real integration test launched its own MySQL data directory, API and Vite
processes on temporary loopback ports. Edge uploaded a generated image with context,
confirmed HTTP 201, retrieved the saved image, reloaded persisted history, and
checked the mobile layout. A direct SQL query verified the browser upload's row
and context. A corrupt image returned HTTP 422. All owned service processes were
stopped afterward. The existing `MySQL80` Windows service was not modified.

The simple solid-color image is a **test fixture**, not a construction-site sample
or evidence of AI capability. No AI inference ran. Screenshots and logs remain
under ignored `.local/desktop-upload.png`, `.local/mobile-upload.png`, `.local/api.log`
and `.local/frontend.log`; they are not committed.

Testing found and resolved MySQL-specific details: a generated WebP filename needs
41 characters, and creation timestamps need `DATETIME(6)` to preserve microseconds
between the upload response and later history reads. The Windows verification
runner uses its own temporary paths to avoid sandbox/desktop-user temp permissions.

One non-failing upstream warning remains: Starlette's test client deprecates its
httpx integration in favor of httpx2. The pinned test environment passed; no warning
was suppressed. This is a test-tool compatibility warning, not a failed upload.

## Re-run the fast tests

```powershell
Set-Location E:\construction_agentic_ai\backend
$testRunDir = Join-Path '..\.local' ('unit-tests-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp $testRunDir

Set-Location E:\construction_agentic_ai\frontend
npm.cmd test
npm.cmd run build
```

The fast backend tests use an isolated in-memory SQLite database unless the
verification runner supplies its explicit test-MySQL variables. SQLite is a test
fixture only; the application has **no SQLite fallback** and requires MySQL.

Covered cases: JPEG, PNG, WebP; metadata and exact byte round trips; empty,
corrupt and truncated content; extension/MIME mismatch; unsupported formats;
animations; file, multipart-body, chunked-body and pixel limits; missing file and
overlong context; path-like and duplicate filenames; history pagination; unknown
records and missing stored images; disk errors; database failure and file cleanup;
liveness, readiness and CORS. Interface tests cover preview, form data, loading,
duplicate-submit prevention, successful saving, validation and backend errors.

## Re-run real MySQL and browser verification

Requires the installed MySQL server binaries, frontend dependencies, Node and
Microsoft Edge. No existing MySQL credentials or running development servers are
needed. It creates an isolated MySQL server with a randomly generated temporary
password, never printing or persisting that password. Nothing connects to the
existing MySQL service.

```powershell
Set-Location E:\construction_agentic_ai
.\backend\.venv\Scripts\python.exe scripts\verify_foundation.py

# If your server binaries are elsewhere:
.\backend\.venv\Scripts\python.exe scripts\verify_foundation.py --mysql-bin 'D:\MySQL\bin'

# MySQL/API tests only, for a machine without Edge:
.\backend\.venv\Scripts\python.exe scripts\verify_foundation.py --skip-browser
```

Each invocation leaves an isolated data directory under `.local/mysql-verification-*`
for diagnosis; it does not remove directories or reuse your real application data.
The directory can be removed manually after the script has stopped. These test
instances are temporary and are not your application's persistent database.

For everyday use, complete the [local MySQL/.env setup](setup.md). We have verified
persistence using the isolated database; we have not configured your existing
MySQL service's application account or obtained its password.

## API contract

| Endpoint | Meaning |
| --- | --- |
| `GET /health` | API liveness, independent of MySQL |
| `GET /health/ready` | Connection and upload table availability |
| `POST /api/uploads` | Multipart `file` plus optional `site_context`; HTTP 201 only after saving |
| `GET /api/uploads?limit=20&offset=0` | Latest metadata, up to 100 per page, and total count |
| `GET /api/uploads/{uuid}` | One saved observation |
| `GET /api/uploads/{uuid}/image` | Original image bytes associated with that record |

Successful records contain `upload_status: "saved"`, `analysis_status: "unavailable"`,
an explanatory `analysis_message`, and `risk_score: null`. No invented hazards or
recommendations are included. Database/storage failure uses HTTP 503, not success.

## Dependency maintenance

`frontend/package-lock.json` locks npm transitive dependencies; use `npm.cmd ci`.
`backend/requirements.txt` pins the complete Python environment, including tests.
Its source is `requirements.in`, compiled using pip-tools 7.6.2 on Python 3.12.
For an intentional update, install that pip-tools version, run `pip-compile
--strip-extras --output-file requirements.txt requirements.in` from `backend/`,
install the new lock and rerun the checks. Do not treat updating dependencies as
proof that image-analysis behavior is valid; that requires the next-phase tests.
