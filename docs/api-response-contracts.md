# API Response Contracts and Pagination

Patch 22 hardens the public list-response contract without changing existing `items` payloads.

## Goals

- Keep list endpoints predictable under growth.
- Avoid accidental oversized responses from dashboard and candidate surfaces.
- Expose consistent pagination metadata to clients and observability tooling.
- Keep existing frontend-compatible response bodies intact.

## Standard list metadata

Paginated endpoints should return or expose:

- `page`
- `page_size`
- `total_items`
- `total_pages`

The same values are also exposed as response headers when the endpoint is list-like:

- `X-Page`
- `X-Page-Size`
- `X-Total-Items`
- `X-Total-Pages`

## Query limits

- Candidate jobs/matches: max `page_size=50`, max query length 160 chars.
- Saved jobs: max `page_size=100`, optional `status` filter.
- Employer list endpoints: max `page_size=100`.
- Employer dashboard widgets: max `page_size=25`.
- Admin list endpoints: max `page_size=100`, with bounded text filters.

## Compatibility note

Existing clients can continue reading `items`. New clients should prefer the explicit metadata to drive pagination controls and avoid assuming that a list response contains the entire dataset.
