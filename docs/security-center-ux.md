# Security Center UX

Patch 26 upgrades the candidate security settings page from a list of forms into an action-oriented security center.

## What changed

- The page now starts with a security posture hero.
- A lightweight security score is derived from existing client-side security signals:
  - verified two-factor authentication,
  - active session hygiene,
  - recent failed-login activity.
- Users get three focused action cards:
  - update password,
  - enable or review 2FA,
  - review active sessions.
- Existing password, login method, session, login history, email-change, and account-deletion flows are preserved.

## Non-goals

This patch does not change backend authentication rules, token handling, session storage, or TOTP verification. It is a frontend UX upgrade on top of the hardened security APIs added in earlier patches.

## Verification

Run:

```bash
bash scripts/verify_patch_26_security_center_ux.sh .
```

With frontend dependencies installed, also run:

```bash
cd frontend
npm run ci:verify
```
