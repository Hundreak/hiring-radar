# Hiring Radar Architecture

## MVP objective
Hiring Radar is a CLI-based system that monitors configured career pages, normalizes job postings, stores them in SQLite, detects new postings, and produces exports and summaries.

## Core layers
- CLI
- Services
- Scrapers
- SQLite persistence

## Current persistence design

### jobs
Stores normalized job postings.

Key fields:
- source_name
- title
- company_name
- location
- canonical_url
- source_type
- source_job_id
- raw_posted_at
- posted_at
- fingerprint
- first_seen_at
- last_seen_at
- is_active
- scraped_at

Rules:
- `fingerprint` is unique
- new fingerprint => new job
- existing fingerprint => update existing row
- `first_seen_at` is preserved
- `last_seen_at` is updated when the job is seen again
- jobs missing from a source crawl can be marked inactive

### crawl_runs
Stores one record per source crawl execution.

Fields:
- id
- started_at
- finished_at
- source_name
- success
- notes

Purpose:
- track crawl history
- record success/failure
- support source-level auditability

## Repository behavior
The repository layer currently supports:
- starting a crawl run
- finishing a crawl run
- upserting jobs by fingerprint
- fetching jobs by fingerprint
- listing active jobs
- marking missing jobs inactive by source

## Testing strategy
Initial tests are deterministic and local:
- no live site dependency
- repository tests use a temporary SQLite database
- parser tests will use HTML fixtures