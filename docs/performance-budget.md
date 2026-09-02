# Frontend Performance Budget

Patch 19 introduces an executable frontend performance budget. The goal is to catch performance regressions before they reach production or handoff packages.

## Source of truth

The budget lives in:

```text
frontend/performance-budget.json
```

The check script lives in:

```text
frontend/scripts/check-performance-budget.mjs
```

Run it from the frontend directory:

```bash
npm run check:performance
```

Or from the project root:

```bash
make frontend-performance
```

## What is checked

### Public assets

- Total public image/static asset weight.
- Per-file public asset weight.

Large unused assets are risky because files under `public/` are easy to ship accidentally and are often referenced directly without image optimization.

### Source files

- Large TypeScript/TSX files.
- Route-level files under `src/app`.
- Localization message JSON files.

This complements the component-size guard from Patch 07. The performance budget works in bytes, so it catches huge static copy blocks and route files even when line count looks acceptable.

### Build artifacts

When `.next/static` exists after a production build, the script also checks gzip JS and CSS chunk budgets.

The build-artifact budget is optional by config because the script should also work in lightweight environments before dependencies are installed. In normal CI, `npm run ci:verify` runs the performance check after `next build`, so chunk budgets are evaluated.

## Patch 19 cleanup

The patch removes unused legacy public assets through:

```bash
bash scripts/apply_patch_19_performance_cleanup.sh .
```

Deleted files:

```text
frontend/public/brand/coresift-logo.png
frontend/public/brand/coresift-copliot-logo.png
```

The current frontend brand logo is rendered by `frontend/src/components/brand/brand-logo.tsx` and does not reference these PNG files.

## When to change the budget

Do not raise budgets just to make CI green. Prefer these fixes first:

1. Compress or convert large images to AVIF/WebP.
2. Delete unused public assets.
3. Move heavy optional UI behind dynamic imports.
4. Split route files and large client components.
5. Move large static copy/config out of hot render paths.

Raise the budget only when the product requirement is deliberate and documented in the PR or patch notes.
