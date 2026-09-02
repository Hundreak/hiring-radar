from __future__ import annotations

from .base import RepositoryDomain


class JobsRepository(RepositoryDomain):
    """Job catalog, matching and saved-job repository facade.

    This facade delegates to the legacy root repository for now. It gives
    services and routers a stable domain-specific seam before the SQL
    implementations are moved out of ``repository.py`` in smaller patches.
    """

    def get_job_by_id(self, *args, **kwargs):
        return self._call("get_job_by_id", *args, **kwargs)

    def get_job_by_fingerprint(self, *args, **kwargs):
        return self._call("get_job_by_fingerprint", *args, **kwargs)

    def list_jobs(self, *args, **kwargs):
        return self._call("list_jobs", *args, **kwargs)

    def get_job_counts(self, *args, **kwargs):
        return self._call("get_job_counts", *args, **kwargs)

    def get_source_summary_rows(self, *args, **kwargs):
        return self._call("get_source_summary_rows", *args, **kwargs)

    def get_company_summary_rows(self, *args, **kwargs):
        return self._call("get_company_summary_rows", *args, **kwargs)

    def list_jobs_first_seen_since(self, *args, **kwargs):
        return self._call("list_jobs_first_seen_since", *args, **kwargs)

    def get_latest_crawl_run(self, *args, **kwargs):
        return self._call("get_latest_crawl_run", *args, **kwargs)

    def list_active_jobs(self, *args, **kwargs):
        return self._call("list_active_jobs", *args, **kwargs)

    def upsert_job(self, *args, **kwargs):
        return self._call("upsert_job", *args, **kwargs)

    def mark_missing_jobs_inactive(self, *args, **kwargs):
        return self._call("mark_missing_jobs_inactive", *args, **kwargs)

    def get_job_source_by_id(self, *args, **kwargs):
        return self._call("get_job_source_by_id", *args, **kwargs)

    def list_job_sources(self, *args, **kwargs):
        return self._call("list_job_sources", *args, **kwargs)

    def get_job_source(self, *args, **kwargs):
        return self._call("get_job_source", *args, **kwargs)

    def upsert_job_source(self, *args, **kwargs):
        return self._call("upsert_job_source", *args, **kwargs)

    def get_job_source_record(self, *args, **kwargs):
        return self._call("get_job_source_record", *args, **kwargs)

    def upsert_job_source_record(self, *args, **kwargs):
        return self._call("upsert_job_source_record", *args, **kwargs)

    def list_job_source_records(self, *args, **kwargs):
        return self._call("list_job_source_records", *args, **kwargs)

    def mark_missing_job_source_records_inactive(self, *args, **kwargs):
        return self._call("mark_missing_job_source_records_inactive", *args, **kwargs)

    def get_canonical_job_by_id(self, *args, **kwargs):
        return self._call("get_canonical_job_by_id", *args, **kwargs)

    def get_canonical_job(self, *args, **kwargs):
        return self._call("get_canonical_job", *args, **kwargs)

    def upsert_canonical_job(self, *args, **kwargs):
        return self._call("upsert_canonical_job", *args, **kwargs)

    def list_canonical_jobs(self, *args, **kwargs):
        return self._call("list_canonical_jobs", *args, **kwargs)

    def list_ranked_canonical_jobs(self, *args, **kwargs):
        return self._call("list_ranked_canonical_jobs", *args, **kwargs)

    def get_canonical_job_feature(self, *args, **kwargs):
        return self._call("get_canonical_job_feature", *args, **kwargs)

    def upsert_canonical_job_feature(self, *args, **kwargs):
        return self._call("upsert_canonical_job_feature", *args, **kwargs)

    def list_canonical_job_features(self, *args, **kwargs):
        return self._call("list_canonical_job_features", *args, **kwargs)

    def prune_canonical_job_features_for_inactive_jobs(self, *args, **kwargs):
        return self._call("prune_canonical_job_features_for_inactive_jobs", *args, **kwargs)

    def get_subscriber_job_interaction(self, *args, **kwargs):
        return self._call("get_subscriber_job_interaction", *args, **kwargs)

    def record_subscriber_job_interaction(self, *args, **kwargs):
        return self._call("record_subscriber_job_interaction", *args, **kwargs)

    def list_subscriber_job_interaction_events(self, *args, **kwargs):
        return self._call("list_subscriber_job_interaction_events", *args, **kwargs)

    def list_subscriber_job_behavioral_affinity_scores(self, *args, **kwargs):
        return self._call("list_subscriber_job_behavioral_affinity_scores", *args, **kwargs)

    def list_matchable_canonical_job_feature_pairs(self, *args, **kwargs):
        return self._call("list_matchable_canonical_job_feature_pairs", *args, **kwargs)

    def upsert_canonical_job_link(self, *args, **kwargs):
        return self._call("upsert_canonical_job_link", *args, **kwargs)

    def list_canonical_job_links(self, *args, **kwargs):
        return self._call("list_canonical_job_links", *args, **kwargs)

    def prune_canonical_job_links_for_inactive_source_records(self, *args, **kwargs):
        return self._call("prune_canonical_job_links_for_inactive_source_records", *args, **kwargs)

    def mark_missing_canonical_jobs_inactive(self, *args, **kwargs):
        return self._call("mark_missing_canonical_jobs_inactive", *args, **kwargs)

    def list_jobs_paginated(self, *args, **kwargs):
        return self._call("list_jobs_paginated", *args, **kwargs)

    def get_job_external_context_snapshot_by_url(self, *args, **kwargs):
        return self._call("get_job_external_context_snapshot_by_url", *args, **kwargs)

    def upsert_job_external_context_snapshot(self, *args, **kwargs):
        return self._call("upsert_job_external_context_snapshot", *args, **kwargs)

    def save_job(self, *args, **kwargs):
        return self._call("save_job", *args, **kwargs)

    def unsave_job(self, *args, **kwargs):
        return self._call("unsave_job", *args, **kwargs)

    def get_saved_job(self, *args, **kwargs):
        return self._call("get_saved_job", *args, **kwargs)

    def get_saved_job_by_id(self, *args, **kwargs):
        return self._call("get_saved_job_by_id", *args, **kwargs)

    def list_saved_jobs(self, *args, **kwargs):
        return self._call("list_saved_jobs", *args, **kwargs)

    def update_saved_job_status(self, *args, **kwargs):
        return self._call("update_saved_job_status", *args, **kwargs)

    def add_saved_job_note(self, *args, **kwargs):
        return self._call("add_saved_job_note", *args, **kwargs)

    def list_saved_job_notes(self, *args, **kwargs):
        return self._call("list_saved_job_notes", *args, **kwargs)

    def update_saved_job_note(self, *args, **kwargs):
        return self._call("update_saved_job_note", *args, **kwargs)
