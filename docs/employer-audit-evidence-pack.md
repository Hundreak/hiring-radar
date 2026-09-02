# Patch 29 — Employer Audit Log Export / Compliance Evidence Pack

This patch turns the employer compliance area into an executable audit surface.
It is designed for B2B trust reviews, enterprise demos, and production incident
triage where the team needs to answer: **who did what, when, on which resource,
and can we export proof?**

## Backend scope

New router:

- `GET /api/employer/compliance/audit-events`
- `GET /api/employer/compliance/audit-events/{event_id}`
- `GET /api/employer/compliance/audit-events/export?format=csv|json`

The list endpoint supports bounded pagination and filters:

- `event_type`
- `resource_type`
- `resource_id`
- `actor_user_id`
- `created_from`
- `created_to`

Access is restricted to employer `owner` and `admin` roles. Lower-privileged
roles receive `403 employer_audit_forbidden`.

## Export behavior

CSV and JSON exports are capped at 500 events per request. This keeps the
synchronous endpoint safe for SQLite-backed deployments. Larger evidence packs
should be moved to a queued export job later.

Every export writes an immutable audit event:

```text
employer.audit.exported
```

The response also includes:

- `X-Audit-Export-ID`
- `X-Audit-Export-Items`

## Frontend scope

The previous coming-soon compliance page is replaced by a real employer
compliance dashboard:

- total audit events
- high-sensitivity event count
- filters
- paginated audit timeline
- metadata preview
- CSV export
- JSON evidence export

## Sensitivity model

The API labels events as:

- `high`: auth, team, settings, and export/security-sensitive events
- `medium`: candidate, campaign, send-queue and outreach workflow events
- `low`: other operational events

This is intentionally conservative and can later be extended into a formal
policy engine.

## Verification

Run:

```bash
bash scripts/verify_patch_29_employer_audit.sh .
```

Frontend dependency-aware verification:

```bash
cd frontend
npm run ci:verify
```
