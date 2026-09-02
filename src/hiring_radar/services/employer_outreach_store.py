"""Small JSON-backed persistence for employer outreach drafts and candidate workflow.

This store is intentionally lightweight for the employer demo surface. It gives the
frontend real persistence without introducing a DB migration yet. The data shape is
kept close to the future API contract so it can be moved to SQLite/Postgres later.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_STORE_LOCK = threading.RLock()


def _store_path() -> Path:
    return Path(
        os.getenv(
            "HIRING_RADAR_EMPLOYER_OUTREACH_STORE_PATH",
            "data/employer_outreach_store.json",
        )
    )


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"version": 1, "campaigns": [], "workflow": {}, "send_queues": {}}


def _read_store() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return _empty_store()

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return _empty_store()

    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("version", 1)
    data.setdefault("campaigns", [])
    data.setdefault("workflow", {})
    data.setdefault("send_queues", {})
    return data


def _write_store(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _candidate_key(candidate_id: int | str) -> str:
    return str(candidate_id)


def _ensure_employer_workflow(data: dict[str, Any], employer_id: str) -> dict[str, Any]:
    workflow = data.setdefault("workflow", {})
    employer_workflow = workflow.setdefault(employer_id, {})
    if not isinstance(employer_workflow, dict):
        workflow[employer_id] = {}
        employer_workflow = workflow[employer_id]
    return employer_workflow


def _ensure_candidate_workflow(
    data: dict[str, Any], employer_id: str, candidate_id: int | str
) -> dict[str, Any]:
    employer_workflow = _ensure_employer_workflow(data, employer_id)
    candidate = employer_workflow.setdefault(_candidate_key(candidate_id), {"tags": [], "notes": []})
    if not isinstance(candidate, dict):
        candidate = {"tags": [], "notes": []}
        employer_workflow[_candidate_key(candidate_id)] = candidate
    candidate.setdefault("tags", [])
    candidate.setdefault("notes", [])
    return candidate


def list_campaigns(employer_id: str) -> list[dict[str, Any]]:
    with _STORE_LOCK:
        data = _read_store()
        campaigns = [item for item in data.get("campaigns", []) if item.get("employer_id") == employer_id]
        campaigns.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return deepcopy(campaigns)


def get_workflow(employer_id: str) -> dict[str, Any]:
    with _STORE_LOCK:
        data = _read_store()
        return deepcopy(_ensure_employer_workflow(data, employer_id))


def add_tags(employer_id: str, candidate_ids: list[int], tags: list[str]) -> dict[str, Any]:
    normalized_tags = []
    for tag in tags:
        normalized = " ".join(str(tag).strip().split())
        if normalized and normalized.casefold() not in {item.casefold() for item in normalized_tags}:
            normalized_tags.append(normalized)

    if not candidate_ids or not normalized_tags:
        return get_workflow(employer_id)

    with _STORE_LOCK:
        data = _read_store()
        for candidate_id in candidate_ids:
            candidate = _ensure_candidate_workflow(data, employer_id, candidate_id)
            existing = candidate.setdefault("tags", [])
            existing_casefold = {str(item).casefold() for item in existing}
            for tag in normalized_tags:
                if tag.casefold() not in existing_casefold:
                    existing.append(tag)
                    existing_casefold.add(tag.casefold())
        _write_store(data)
        return deepcopy(_ensure_employer_workflow(data, employer_id))


def remove_tag(employer_id: str, candidate_id: int, tag: str) -> dict[str, Any]:
    with _STORE_LOCK:
        data = _read_store()
        candidate = _ensure_candidate_workflow(data, employer_id, candidate_id)
        candidate["tags"] = [item for item in candidate.get("tags", []) if item != tag]
        _write_store(data)
        return deepcopy(_ensure_employer_workflow(data, employer_id))


def add_notes(
    employer_id: str,
    candidate_ids: list[int],
    body: str,
    *,
    author: str = "Sen",
    tone: str = "neutral",
) -> dict[str, Any]:
    normalized_body = str(body).strip()
    if not candidate_ids or not normalized_body:
        return get_workflow(employer_id)

    with _STORE_LOCK:
        data = _read_store()
        for candidate_id in candidate_ids:
            candidate = _ensure_candidate_workflow(data, employer_id, candidate_id)
            note = {
                "id": f"note-{candidate_id}-{uuid4().hex[:12]}",
                "author": author,
                "body": normalized_body,
                "createdAt": _now_iso(),
                "tone": tone,
            }
            candidate.setdefault("notes", []).insert(0, note)
        _write_store(data)
        return deepcopy(_ensure_employer_workflow(data, employer_id))


def create_campaign(employer_id: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_ids = [int(item) for item in payload.get("candidate_ids", [])]
    now = _now_iso()
    campaign = {
        "id": f"cmp_{uuid4().hex[:12]}",
        "employer_id": employer_id,
        "name": payload.get("name") or "Davet kampanyası",
        "status": "draft",
        "candidate_ids": candidate_ids,
        "channel": payload.get("channel"),
        "tone": payload.get("tone"),
        "template": payload.get("template"),
        "include_salary": bool(payload.get("include_salary", True)),
        "include_calendar": bool(payload.get("include_calendar", True)),
        "message_preview": payload.get("message_preview") or "",
        "response_rate": int(payload.get("response_rate") or 0),
        "metadata": payload.get("metadata") or {},
        "created_at": now,
        "updated_at": now,
    }

    with _STORE_LOCK:
        data = _read_store()
        data.setdefault("campaigns", []).insert(0, campaign)
        for candidate_id in candidate_ids:
            candidate = _ensure_candidate_workflow(data, employer_id, candidate_id)
            tags = candidate.setdefault("tags", [])
            if "Davet gönderilecek" not in tags:
                tags.append("Davet gönderilecek")
            candidate.setdefault("notes", []).insert(
                0,
                {
                    "id": f"campaign-{campaign['id']}-{candidate_id}",
                    "author": "Hiring Radar",
                    "body": f"{campaign['name']} taslağına eklendi. Kanal: {campaign['channel']}, şablon: {campaign['template']}.",
                    "createdAt": now,
                    "tone": "ai",
                },
            )
        _write_store(data)
        return deepcopy(campaign), deepcopy(_ensure_employer_workflow(data, employer_id))


def _find_campaign(data: dict[str, Any], employer_id: str, campaign_id: str) -> dict[str, Any] | None:
    for campaign in data.get("campaigns", []):
        if campaign.get("id") == campaign_id and campaign.get("employer_id") == employer_id:
            return campaign
    return None


def _ensure_send_queue_root(data: dict[str, Any], employer_id: str) -> dict[str, Any]:
    send_queues = data.setdefault("send_queues", {})
    employer_queues = send_queues.setdefault(employer_id, {})
    if not isinstance(employer_queues, dict):
        send_queues[employer_id] = {}
        employer_queues = send_queues[employer_id]
    return employer_queues


def _queue_stats(items: list[dict[str, Any]]) -> dict[str, int]:
    ready = sum(1 for item in items if item.get("status") == "ready")
    review = sum(1 for item in items if item.get("status") == "review")
    blocked = sum(1 for item in items if item.get("status") == "blocked")
    return {"ready_count": ready, "review_count": review, "blocked_count": blocked}


def _append_audit_event(queue: dict[str, Any], *, action: str, actor: str, note: str, metadata: dict[str, Any] | None = None) -> None:
    queue.setdefault("audit", []).insert(
        0,
        {
            "id": f"audit_{uuid4().hex[:12]}",
            "action": action,
            "actor": actor,
            "note": note,
            "metadata": metadata or {},
            "created_at": _now_iso(),
        },
    )
    queue["audit"] = queue.get("audit", [])[:100]


def get_send_queue(employer_id: str, campaign_id: str) -> dict[str, Any] | None:
    with _STORE_LOCK:
        data = _read_store()
        campaign = _find_campaign(data, employer_id, campaign_id)
        if not campaign:
            return None
        queue = _ensure_send_queue_root(data, employer_id).get(campaign_id)
        return deepcopy(queue) if queue else None


def prepare_send_queue(
    employer_id: str,
    campaign_id: str,
    items: list[dict[str, Any]],
    *,
    actor: str = "Sen",
    note: str | None = None,
) -> dict[str, Any] | None:
    now = _now_iso()
    with _STORE_LOCK:
        data = _read_store()
        campaign = _find_campaign(data, employer_id, campaign_id)
        if not campaign:
            return None

        normalized_items: list[dict[str, Any]] = []
        allowed_candidate_ids = {int(item) for item in campaign.get("candidate_ids", [])}
        for raw_item in items:
            candidate_id = int(raw_item.get("candidate_id"))
            if candidate_id not in allowed_candidate_ids:
                continue
            status = raw_item.get("status") if raw_item.get("status") in {"ready", "review", "blocked"} else "review"
            normalized_items.append(
                {
                    "id": raw_item.get("id") or f"qi_{campaign_id}_{candidate_id}",
                    "candidate_id": candidate_id,
                    "subject": str(raw_item.get("subject") or "").strip(),
                    "message": str(raw_item.get("message") or "").strip(),
                    "response_score": max(0, min(100, int(raw_item.get("response_score") or 0))),
                    "status": status,
                    "checks": [str(item) for item in raw_item.get("checks", []) if str(item).strip()],
                    "metadata": raw_item.get("metadata") or {},
                    "updated_at": now,
                }
            )

        stats = _queue_stats(normalized_items)
        queue = {
            "id": f"queue_{campaign_id}",
            "campaign_id": campaign_id,
            "employer_id": employer_id,
            "status": "blocked" if stats["blocked_count"] else "ready_for_review",
            "channel": campaign.get("channel"),
            "items": normalized_items,
            "ready_count": stats["ready_count"],
            "review_count": stats["review_count"],
            "blocked_count": stats["blocked_count"],
            "created_at": now,
            "updated_at": now,
            "audit": [],
        }
        _append_audit_event(
            queue,
            action="queue_prepared",
            actor=actor,
            note=note or f"{len(normalized_items)} aday için gönderim kuyruğu hazırlandı.",
            metadata=stats,
        )

        employer_queues = _ensure_send_queue_root(data, employer_id)
        previous_queue = employer_queues.get(campaign_id)
        if previous_queue and previous_queue.get("audit"):
            queue["audit"].extend(previous_queue.get("audit", [])[:50])
            queue["audit"] = queue["audit"][:100]
        employer_queues[campaign_id] = queue

        campaign["status"] = "queued" if not stats["blocked_count"] else "draft"
        campaign["updated_at"] = now
        campaign.setdefault("metadata", {})["send_queue"] = {
            "status": queue["status"],
            **stats,
            "prepared_at": now,
        }

        for item in normalized_items:
            candidate = _ensure_candidate_workflow(data, employer_id, item["candidate_id"])
            tags = candidate.setdefault("tags", [])
            if item["status"] == "ready" and "Gönderim kuyruğunda" not in tags:
                tags.append("Gönderim kuyruğunda")
            candidate.setdefault("notes", []).insert(
                0,
                {
                    "id": f"queue-{campaign_id}-{item['candidate_id']}-{uuid4().hex[:8]}",
                    "author": "Hiring Radar",
                    "body": f"{campaign.get('name', 'Davet kampanyası')} gönderim kuyruğunda: {item['status']}.",
                    "createdAt": now,
                    "tone": "ai",
                },
            )

        _write_store(data)
        return deepcopy(queue)


def update_send_queue_item(
    employer_id: str,
    campaign_id: str,
    item_id: str,
    *,
    status: str | None = None,
    checks: list[str] | None = None,
    note: str | None = None,
    actor: str = "Sen",
) -> dict[str, Any] | None:
    now = _now_iso()
    with _STORE_LOCK:
        data = _read_store()
        campaign = _find_campaign(data, employer_id, campaign_id)
        if not campaign:
            return None
        queue = _ensure_send_queue_root(data, employer_id).get(campaign_id)
        if not queue:
            return None

        target = None
        for item in queue.get("items", []):
            if item.get("id") == item_id:
                target = item
                break
        if not target:
            return None

        if status in {"ready", "review", "blocked"}:
            target["status"] = status
        if checks is not None:
            target["checks"] = [str(item) for item in checks if str(item).strip()]
        target["updated_at"] = now
        stats = _queue_stats(queue.get("items", []))
        queue.update(stats)
        queue["status"] = "blocked" if stats["blocked_count"] else "ready_for_review"
        queue["updated_at"] = now
        _append_audit_event(
            queue,
            action="queue_item_updated",
            actor=actor,
            note=note or f"{target.get('candidate_id')} adayının kuyruk durumu güncellendi.",
            metadata={"item_id": item_id, "status": target.get("status")},
        )
        campaign.setdefault("metadata", {})["send_queue"] = {"status": queue["status"], **stats, "prepared_at": queue.get("created_at")}
        campaign["updated_at"] = now
        _write_store(data)
        return deepcopy(queue)

