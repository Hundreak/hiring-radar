# Patch 25 — Auth Guard / Session Expiry UX Hardening

This patch standardizes how the frontend reacts when a protected API request returns `401 Unauthorized` after a user or employer session has expired.

## What changed

- Protected `401` responses from `/api/user/*` and `/api/employer/*` now emit a global `noytera:auth-session-expired` browser event.
- Login/register/magic-link/password-reset failures are intentionally excluded, so a wrong password does not trigger a global session-expired modal.
- `SessionExpiryBoundary` listens for the event, clears the React Query cache, and presents a blocking re-authentication dialog.
- Candidate and employer auth guards now use the same login redirect builder, preserving the current route as `redirect`.
- Employer protected pages preserve the current employer route instead of always redirecting to `/employer/dashboard`.
- Logout clears the React Query cache to reduce stale protected data after session termination.

## Why this matters

Cookie-based auth can fail at any time: session expiry, account revocation, device logout, CSRF/session rotation, or production secret rotation. Without a global session-expiry UX, each screen handles `401` differently and users can land in confusing partial-error states.

This patch makes the behavior deterministic:

1. Protected request receives `401`.
2. Frontend emits a session-expired event.
3. Query cache is cleared.
4. User sees a clear re-login dialog.
5. Login route receives the correct `redirect` target and employer role when needed.

## Verification

Run:

```bash
bash scripts/verify_patch_25_auth_session_ux.sh .
```

With frontend dependencies installed, also run:

```bash
cd frontend
npm run ci:verify
```
