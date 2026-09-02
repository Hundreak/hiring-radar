# Changelog

All notable production-oriented changes should be documented here.

## 0.1.0-release-candidate — 2026-05-25

### Added

- Production release gate with `make release-check`.
- Production environment validator for secrets, cookies, CSRF, rate limits, HTTPS URLs,
  SMTP, storage and employer demo/mock flags.
- Disposable SQLite migration dry-run for release validation.
- Release checklist and production gate documentation.
- Manual GitHub Actions release gate workflow.

### Security

- Release validation now fails on placeholder/default auth secrets.
- Release validation now fails when production cookies are not secure.
- Release validation now fails when CSRF/rate limiting are disabled in production.
- Release validation now fails when employer demo/mock auth is enabled in production.

### Operations

- Source hygiene, backend CI, frontend CI and migration checks are grouped under one
  final release command.
