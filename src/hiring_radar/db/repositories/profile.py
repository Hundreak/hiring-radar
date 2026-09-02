from __future__ import annotations

from .base import RepositoryDomain


class ProfileRepository(RepositoryDomain):
    """Candidate profile, CV and profile intelligence repository facade.

    This facade delegates to the legacy root repository for now. It gives
    services and routers a stable domain-specific seam before the SQL
    implementations are moved out of ``repository.py`` in smaller patches.
    """

    def get_subscriber_keyword_preference(self, *args, **kwargs):
        return self._call("get_subscriber_keyword_preference", *args, **kwargs)

    def upsert_subscriber_keyword_preference(self, *args, **kwargs):
        return self._call("upsert_subscriber_keyword_preference", *args, **kwargs)

    def get_subscriber_profile(self, *args, **kwargs):
        return self._call("get_subscriber_profile", *args, **kwargs)

    def upsert_subscriber_profile(self, *args, **kwargs):
        return self._call("upsert_subscriber_profile", *args, **kwargs)

    def list_subscriber_education_entries(self, *args, **kwargs):
        return self._call("list_subscriber_education_entries", *args, **kwargs)

    def replace_subscriber_education_entries(self, *args, **kwargs):
        return self._call("replace_subscriber_education_entries", *args, **kwargs)

    def list_subscriber_experience_entries(self, *args, **kwargs):
        return self._call("list_subscriber_experience_entries", *args, **kwargs)

    def replace_subscriber_experience_entries(self, *args, **kwargs):
        return self._call("replace_subscriber_experience_entries", *args, **kwargs)

    def list_subscriber_language_entries(self, *args, **kwargs):
        return self._call("list_subscriber_language_entries", *args, **kwargs)

    def replace_subscriber_language_entries(self, *args, **kwargs):
        return self._call("replace_subscriber_language_entries", *args, **kwargs)

    def list_subscriber_language_certificates(self, *args, **kwargs):
        return self._call("list_subscriber_language_certificates", *args, **kwargs)

    def replace_subscriber_language_certificates(self, *args, **kwargs):
        return self._call("replace_subscriber_language_certificates", *args, **kwargs)

    def list_subscriber_certification_entries(self, *args, **kwargs):
        return self._call("list_subscriber_certification_entries", *args, **kwargs)

    def replace_subscriber_certification_entries(self, *args, **kwargs):
        return self._call("replace_subscriber_certification_entries", *args, **kwargs)

    def list_subscriber_skill_details(self, *args, **kwargs):
        return self._call("list_subscriber_skill_details", *args, **kwargs)

    def get_subscriber_skill_detail_by_name(self, *args, **kwargs):
        return self._call("get_subscriber_skill_detail_by_name", *args, **kwargs)

    def upsert_subscriber_skill_detail(self, *args, **kwargs):
        return self._call("upsert_subscriber_skill_detail", *args, **kwargs)

    def rename_subscriber_skill_detail(self, *args, **kwargs):
        return self._call("rename_subscriber_skill_detail", *args, **kwargs)

    def delete_subscriber_skill_detail(self, *args, **kwargs):
        return self._call("delete_subscriber_skill_detail", *args, **kwargs)

    def create_subscriber_ai_audit_log(self, *args, **kwargs):
        return self._call("create_subscriber_ai_audit_log", *args, **kwargs)

    def get_subscriber_ai_audit_log_by_id(self, *args, **kwargs):
        return self._call("get_subscriber_ai_audit_log_by_id", *args, **kwargs)

    def list_subscriber_ai_audit_logs(self, *args, **kwargs):
        return self._call("list_subscriber_ai_audit_logs", *args, **kwargs)

    def update_subscriber_ai_audit_log(self, *args, **kwargs):
        return self._call("update_subscriber_ai_audit_log", *args, **kwargs)

    def get_subscriber_cv_upload_by_id(self, *args, **kwargs):
        return self._call("get_subscriber_cv_upload_by_id", *args, **kwargs)

    def list_subscriber_cv_uploads(self, *args, **kwargs):
        return self._call("list_subscriber_cv_uploads", *args, **kwargs)

    def get_latest_subscriber_cv_upload(self, *args, **kwargs):
        return self._call("get_latest_subscriber_cv_upload", *args, **kwargs)

    def create_subscriber_cv_upload(self, *args, **kwargs):
        return self._call("create_subscriber_cv_upload", *args, **kwargs)

    def update_subscriber_cv_upload_parse_result(self, *args, **kwargs):
        return self._call("update_subscriber_cv_upload_parse_result", *args, **kwargs)

    def create_subscriber_cv_parse_run(self, *args, **kwargs):
        return self._call("create_subscriber_cv_parse_run", *args, **kwargs)

    def get_subscriber_cv_parse_run_by_id(self, *args, **kwargs):
        return self._call("get_subscriber_cv_parse_run_by_id", *args, **kwargs)

    def list_subscriber_cv_parse_runs_for_upload(self, *args, **kwargs):
        return self._call("list_subscriber_cv_parse_runs_for_upload", *args, **kwargs)

    def get_latest_subscriber_cv_parse_run_for_upload(self, *args, **kwargs):
        return self._call("get_latest_subscriber_cv_parse_run_for_upload", *args, **kwargs)

    def update_subscriber_cv_parse_run_apply_state(self, *args, **kwargs):
        return self._call("update_subscriber_cv_parse_run_apply_state", *args, **kwargs)

    def create_subscriber_cv_apply_audit(self, *args, **kwargs):
        return self._call("create_subscriber_cv_apply_audit", *args, **kwargs)

    def get_subscriber_cv_apply_audit_by_id(self, *args, **kwargs):
        return self._call("get_subscriber_cv_apply_audit_by_id", *args, **kwargs)

    def list_subscriber_cv_apply_audits_for_parse_run(self, *args, **kwargs):
        return self._call("list_subscriber_cv_apply_audits_for_parse_run", *args, **kwargs)

    def get_latest_subscriber_cv_parse_run(self, *args, **kwargs):
        return self._call("get_latest_subscriber_cv_parse_run", *args, **kwargs)

    def get_subscriber_profile_feature(self, *args, **kwargs):
        return self._call("get_subscriber_profile_feature", *args, **kwargs)

    def upsert_subscriber_profile_feature(self, *args, **kwargs):
        return self._call("upsert_subscriber_profile_feature", *args, **kwargs)

    def get_subscriber_ai_copilot_conversation(self, *args, **kwargs):
        return self._call("get_subscriber_ai_copilot_conversation", *args, **kwargs)

    def list_subscriber_ai_copilot_conversations(self, *args, **kwargs):
        return self._call("list_subscriber_ai_copilot_conversations", *args, **kwargs)

    def create_subscriber_ai_copilot_conversation(self, *args, **kwargs):
        return self._call("create_subscriber_ai_copilot_conversation", *args, **kwargs)

    def update_subscriber_ai_copilot_conversation(self, *args, **kwargs):
        return self._call("update_subscriber_ai_copilot_conversation", *args, **kwargs)

    def create_subscriber_ai_copilot_message(self, *args, **kwargs):
        return self._call("create_subscriber_ai_copilot_message", *args, **kwargs)

    def list_subscriber_ai_copilot_messages(self, *args, **kwargs):
        return self._call("list_subscriber_ai_copilot_messages", *args, **kwargs)

    def get_subscriber_ai_learned_memory_by_key(self, *args, **kwargs):
        return self._call("get_subscriber_ai_learned_memory_by_key", *args, **kwargs)

    def upsert_subscriber_ai_learned_memory(self, *args, **kwargs):
        return self._call("upsert_subscriber_ai_learned_memory", *args, **kwargs)

    def list_subscriber_ai_learned_memories(self, *args, **kwargs):
        return self._call("list_subscriber_ai_learned_memories", *args, **kwargs)
