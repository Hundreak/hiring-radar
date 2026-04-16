from __future__ import annotations

import hashlib
from dataclasses import dataclass

from hiring_radar.db.repository import HiringRadarRepository
from hiring_radar.models import CareerKnowledgeDocument


@dataclass(slots=True, frozen=True)
class CareerKnowledgeMatch:
    document: CareerKnowledgeDocument
    snippet: str
    score: int


_DEFAULT_CAREER_KNOWLEDGE: tuple[dict[str, str], ...] = (
    {
        "slug": "cv-core-clarity",
        "title": "CV clarity and value communication",
        "category": "cv_writing",
        "locale": "tr",
        "source_name": "CoreSift curated foundation",
        "body_text": (
            "Güçlü bir CV önce adayın hangi problemi çözdüğünü net anlatmalıdır. "
            "Başlık, kısa özet, rol hedefi ve en güçlü beceriler ilk bakışta görünmelidir. "
            "Her deneyim maddesi görev listesi değil, bağlam + eylem + çıktı mantığıyla yazılmalıdır. "
            "Ölçülebilir etki yoksa, sistem karmaşıklığı, ürün katkısı, sahiplenilen kapsam ve teknik zorluk netleştirilmelidir."
        ),
    },
    {
        "slug": "job-search-signal-strategy",
        "title": "Job search signal strategy",
        "category": "job_search",
        "locale": "tr",
        "source_name": "CoreSift curated foundation",
        "body_text": (
            "İş arama sürecinde yalnızca beceri listesi yetmez; rol uyumu sinyalleri gerekir. "
            "Hedef rol adı, ilgili proje örnekleri, kullanılan teknoloji yığını, ekip veya ürün etkisi ve çalışma tercihi görünür olmalıdır. "
            "Adayın profilinde teknik derinlik ile iş sonucu arasındaki bağ kurulursa işveren için daha ikna edici olur."
        ),
    },
    {
        "slug": "learning-plan-principles",
        "title": "Learning plan principles for career growth",
        "category": "learning_plan",
        "locale": "tr",
        "source_name": "CoreSift curated foundation",
        "body_text": (
            "Kariyer gelişimi için öğrenme planı hazırlarken adayın hedef rolüne en yakın eksik sinyaller seçilmelidir. "
            "Plan kısa döngülü, çıktı odaklı ve portföye dönüşebilir olmalıdır. "
            "Öğrenme hedefi, küçük uygulama, görünür çıktı ve profile eklenebilir kanıt birlikte düşünülmelidir."
        ),
    },
)


def _checksum(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ensure_foundation_career_knowledge(
    repository: HiringRadarRepository,
    *,
    updated_at: str,
) -> list[CareerKnowledgeDocument]:
    documents: list[CareerKnowledgeDocument] = []
    for item in _DEFAULT_CAREER_KNOWLEDGE:
        body_text = item["body_text"]
        documents.append(
            repository.upsert_career_knowledge_document(
                slug=item["slug"],
                title=item["title"],
                category=item["category"],
                locale=item.get("locale"),
                source_name=item.get("source_name"),
                source_url=None,
                trust_level="curated",
                freshness_label="foundation",
                body_text=body_text,
                metadata_json={"seed": True},
                checksum=_checksum(body_text),
                updated_at=updated_at,
            )
        )
    return documents


def search_career_knowledge(
    repository: HiringRadarRepository,
    *,
    query: str,
    locale: str | None,
    limit: int = 3,
) -> list[CareerKnowledgeMatch]:
    normalized_terms = {
        term.strip().lower()
        for term in query.replace("\n", " ").split(" ")
        if term.strip() and len(term.strip()) >= 3
    }
    if not normalized_terms:
        return []

    matches: list[CareerKnowledgeMatch] = []
    for document in repository.list_career_knowledge_documents(locale=locale, limit=50):
        haystack = f"{document.title}\n{document.body_text}".lower()
        score = sum(1 for term in normalized_terms if term in haystack)
        if score <= 0:
            continue
        snippet = document.body_text.strip()
        if len(snippet) > 260:
            snippet = snippet[:257].rstrip() + "..."
        matches.append(CareerKnowledgeMatch(document=document, snippet=snippet, score=score))

    matches.sort(key=lambda item: (-item.score, item.document.title.lower()))
    return matches[:limit]
