# Milestone 1 scope

The mentor asks for Site Risk Monitoring and Hazard Detection during weeks 1–2:
a working Site Risk Agent, integrated site data, site/environmental and equipment
hazards, a documented risk score, and a dashboard. Photograph uploads are our
chosen software-only input approach, not a specific mentor requirement. MySQL is
our database choice.

## Foundation delivered

- React/Vite/Tailwind image upload, preview, optional context, loading and error states.
- FastAPI health and database readiness endpoints.
- Actual JPEG/PNG/WebP verification and decoding using Pillow, format/MIME matching,
  file size and pixel limits, and rejection of animations.
- UUID filenames, original file storage and SQLAlchemy/MySQL metadata persistence.
- History and stored-image retrieval; success only after saving file and metadata.
- Honest unavailable analysis state; no findings, recommendations or numeric score.
- Local configuration examples, reproducible dependency locks, tests and setup docs.

This completes the **first implementation phase**, not all mentor requirements.
The current observation log is the dashboard foundation, not a finished risk
dashboard. Recharts is installed but deliberately unused until real scores exist.

## Still required for Milestone 1

1. Evaluate a small set of feasible **visible** site/equipment hazards and suitable
   models/datasets. Document supported labels, licensing, image-domain suitability,
   quality limits and representative failure cases before promising capabilities.
2. Implement a real vision adapter: either a suitable evaluated model/weights or
   configured vision API. Standard pretrained YOLO object classes do not imply
   construction-hazard recognition. OpenCV can support preprocessing and quality
   checks; it does not supply general hazard understanding.
3. Implement the Site Risk Agent with LangGraph and an LLM API. It should call
   analysis and safety-guidance retrieval tools, verify evidence, request missing
   context and recommend actions, while recording decisions and tool calls.
4. Implement and test a deterministic score with documented assumptions and
   uncertainty handling. Save evidence, hazards, scores and recommendations in MySQL.
5. Extend the dashboard with evidence-linked findings, risk level, recommendations,
   analysis history and supervisor review controls.
6. Test clear hazard examples, images with no supported hazard, unclear images,
   missing context and unavailable/failed model requests. Never label the site safe
   just because no supported hazard was detected.

## Boundaries

No physical sensors. No separate Worker/PPE Safety, Compliance, Insurance or
Reporting agents. Do not infer wind speed, internal equipment faults or other
invisible conditions from a photo. User context remains explicitly unverified.
Findings and recommendations will support supervisor review, not replace it.
There is no automated safety certification or assurance from the current app.

## Storage limitations

Validation is performed before storage. A normal database or disk failure rolls
back metadata and cleans up the image. Filesystem and MySQL cannot share an atomic
transaction: an abrupt process/machine failure can leave an orphan file, and a
lost commit acknowledgement can make the final outcome uncertain. Before wider
use, add reconciliation, idempotent requests, user access control, retention and
backup policies. UUIDs are identifiers, not authorization.
