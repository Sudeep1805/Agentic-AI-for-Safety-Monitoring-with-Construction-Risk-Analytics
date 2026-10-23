# Initial MySQL schema

The application uses MySQL 8 and SQLAlchemy 2. Its upload records are stored in
`site_uploads`, YOLO detection results are stored in `detections`, and authenticated
project records are stored in `projects`.

1. Create the `construction_risk` database and application user as described in
   [setup](../docs/setup.md).
2. Configure `backend/.env` locally.
3. Run `python -m app.init_db` from `backend/` using its virtual environment.

`app.init_db` creates missing tables from the SQLAlchemy models. It does not drop,
replace or automatically migrate existing tables. `001_initial.sql` is the fresh
installation schema reference and can alternatively be run after selecting the
database in MySQL Workbench. Existing installations created before detection
persistence must run `002_add_detections.sql` once after selecting the database.
Existing installations adding project management must also run
`003_add_projects.sql` once. Both migrations are additive and preserve existing rows.
Do not assume the initial schema script migrates a different existing schema.
Future structural changes should use numbered migrations (or Alembic) with explicit
review and backups.

Image bytes live in `backend/uploads/` by default; the database stores their generated
names, original display names, MIME type, dimensions, byte size, SHA-256 hash,
optional unverified site context, and UTC creation time. Back up the database and
upload directory together. API retrieval uses UUIDs, not user-provided file paths.
