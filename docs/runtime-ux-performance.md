# Runtime UX Performance Notes

Patch 20 adds a lightweight runtime UX layer on top of the source and bundle budgets introduced earlier.

## What changed

- Candidate dashboard routes now have a segment-level loading skeleton.
- Employer workspace routes now have a segment-level loading skeleton.
- The AI copilot widget is loaded through a deferred `next/dynamic` client loader.
- CI can verify the runtime UX guardrails with `npm run check:runtime-ux`.

## Why this matters

The authenticated dashboard has heavy client surfaces: saved-job pipeline, match explainability, profile review, employer talent, campaigns and copilot. Users should not see a blank transition while those areas hydrate or chunk-load. The loading skeletons keep navigation responsive and the deferred copilot keeps the primary screen path lighter.

## Commands

```bash
cd frontend
npm run check:runtime-ux
npm run ci:verify
```
