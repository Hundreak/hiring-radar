# Patch 23 — Frontend Pagination / Empty-State UX Integration

Patch 22 hardened the API list contracts with bounded `page`, `page_size`, `total_items`, and `total_pages` metadata. Patch 23 wires that contract into the frontend so list-heavy surfaces no longer assume that every record is already in memory.

## What changed

- Added a shared frontend pagination utility layer in `frontend/src/lib/pagination.ts`.
- Added a reusable `PaginationControls` component.
- Updated React Query list hooks to include page/page-size parameters in the query key.
- Kept previous page data visible while a new page is loading via React Query `placeholderData`.
- Integrated pagination controls into:
  - candidate jobs feed,
  - matches feed,
  - saved jobs pipeline,
  - employer jobs portfolio.
- Added localized pagination labels for Turkish, English, and German.
- Added a pagination UX smoke check to frontend CI.

## Product behavior

The first page keeps the same visual structure, but the user can now move through bounded result pages. Page-size controls reset to page 1 to avoid empty screens after changing density. Local filters still work on the currently loaded page; backend query/status filters are used where Patch 22 exposed them.

## Why this matters

Without frontend pagination, backend page contracts are easy to ignore and list screens can slowly become memory-heavy. This patch keeps large result sets manageable and makes the contract visible in product UI.
