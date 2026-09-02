# Patch 28 — Employer Communication Controls

Patch 28 adds an employer-facing communication preference layer for B2B workspaces. The goal is to make notification behavior explicit, role-aware and auditable rather than keeping it as static settings UI copy.

## Backend contract

New endpoint group:

- `GET /api/employer/settings/communication-preferences`
- `PATCH /api/employer/settings/communication-preferences`

The response includes:

- workspace-level communication preferences,
- team coverage summary,
- last updated timestamp.

`PATCH` is restricted to `owner` and `admin` employer roles. Other roles can read the preferences but cannot change workspace policy. Security alerts are mandatory and are normalized back to `true` even if a client tries to disable them.

Preferences are stored inside `employer_companies.settings_json.communication_preferences` so this patch does not require a destructive schema migration. The repository exposes explicit helper methods to keep the JSON contract typed and normalized.

## Frontend behavior

The employer settings page now uses React Query to load and update communication preferences. The Notifications tab becomes a real communication control center with:

- channel toggles,
- mandatory security alert visibility,
- role-based routing,
- quiet hours,
- default delivery channel,
- additional notification email targets,
- active/invited team coverage summary.

## Auditability

Every successful workspace preference update writes an `employer.settings.communication_preferences.updated` audit event.
