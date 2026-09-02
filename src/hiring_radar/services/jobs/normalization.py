from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlsplit, urlunsplit

_WHITESPACE_PATTERN = re.compile(r"\s+")
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_MULTI_SLASH_PATTERN = re.compile(r"/{2,}")
_EXPERIENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:minimum of|at least|min\.?|minimum)\s+(\d{1,2})\+?\s+years?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\+\s+years?", re.IGNORECASE),
    re.compile(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s+years?", re.IGNORECASE),
)

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "role",
        "position",
        "job",
        "team",
        "teams",
        "work",
        "working",
        "lead",
        "senior",
        "junior",
        "mid",
        "level",
        "full",
        "time",
        "part",
        "remote",
        "hybrid",
    }
)

_ROLE_FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("software_engineering", ("software engineer", "backend", "frontend", "full stack", "full-stack", "developer", "mobile engineer", "ios", "android", "platform engineer")),
    ("data", ("data engineer", "data scientist", "analytics", "machine learning", "ml engineer", "bi analyst", "business intelligence", "data analyst")),
    ("devops_cloud", ("devops", "site reliability", "sre", "cloud engineer", "infrastructure", "platform", "kubernetes", "terraform")),
    ("security", ("security engineer", "application security", "soc", "iam", "cyber", "penetration")),
    ("quality_assurance", ("qa", "quality assurance", "test engineer", "automation engineer", "sdet")),
    ("product", ("product manager", "product owner", "product marketing")),
    ("design", ("designer", "ux", "ui", "graphic design", "product design", "architectural designer")),
    ("architecture_construction", ("architect", "architecture", "construction", "civil engineer", "interior", "structural")),
    ("sales", ("sales", "account executive", "business development", "account manager", "inside sales")),
    ("marketing", ("marketing", "seo", "content", "growth", "performance marketing", "brand")),
    ("finance_accounting", ("accountant", "finance", "financial analyst", "controller", "audit", "payroll")),
    ("operations_logistics", ("operations", "logistics", "procurement", "supply chain", "warehouse", "dispatch", "planner")),
    ("customer_support", ("support", "customer success", "customer service", "call center", "help desk")),
    ("hospitality_service", ("waiter", "garson", "barista", "chef", "cook", "kitchen", "restaurant", "hospitality")),
    ("retail_store", ("cashier", "store", "merchandiser", "sales associate", "retail", "shop")),
    ("human_resources", ("recruiter", "talent acquisition", "hr", "human resources", "people operations")),
    ("administration", ("administrative", "office manager", "assistant", "reception", "coordinator")),
    ("education", ("teacher", "instructor", "lecturer", "education", "trainer")),
    ("healthcare", ("nurse", "doctor", "physician", "medical", "clinical", "pharmacist")),
    ("legal_compliance", ("lawyer", "legal", "counsel", "compliance", "privacy")),
    ("manufacturing", ("manufacturing", "production", "operator", "technician", "maintenance")),
    ("research_science", ("research", "scientist", "laboratory", "lab", "r&d")),
)

_DISCIPLINE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("machine_learning", ("machine learning", "ml", "llm", "ai", "deep learning", "nlp")),
    ("data_engineering", ("data engineer", "etl", "pipeline", "spark", "airflow", "warehouse")),
    ("backend", ("backend", "api", "python", "java", "golang", "node.js", "microservices")),
    ("frontend", ("frontend", "react", "next.js", "typescript", "javascript", "angular", "vue")),
    ("mobile", ("ios", "android", "mobile", "react native", "flutter")),
    ("devops", ("devops", "sre", "kubernetes", "terraform", "docker", "aws", "gcp", "azure")),
    ("quality_automation", ("test automation", "qa automation", "selenium", "playwright", "cypress", "sdet")),
    ("product_management", ("product manager", "product owner", "roadmap", "discovery")),
    ("ux_ui", ("ux", "ui", "figma", "design system", "wireframe")),
    ("sales_execution", ("sales", "pipeline", "quota", "crm")),
    ("customer_service", ("customer service", "support", "ticket", "crm", "sla")),
    ("hospitality_floor", ("waiter", "garson", "service", "restaurant", "guest")),
    ("architecture_design", ("architect", "revit", "autocad", "bim", "construction drawings")),
)

_DEPARTMENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("engineering", ("engineer", "developer", "devops", "sre", "architect", "qa", "platform")),
    ("data", ("data", "analytics", "business intelligence", "machine learning")),
    ("product", ("product", "owner", "roadmap")),
    ("design", ("design", "ux", "ui", "creative", "graphic")),
    ("operations", ("operations", "logistics", "warehouse", "supply chain", "procurement")),
    ("commercial", ("sales", "business development", "account executive", "marketing", "growth")),
    ("people", ("recruiter", "talent", "human resources", "people operations", "hr")),
    ("finance", ("finance", "accounting", "audit", "controller", "payroll")),
    ("support", ("support", "customer success", "customer service", "help desk")),
    ("hospitality", ("waiter", "garson", "barista", "chef", "kitchen", "restaurant")),
)

_SKILL_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # ── Core programming languages ──
    ("python", ("python",)),
    ("java", ("java",)),
    ("javascript", ("javascript",)),
    ("typescript", ("typescript",)),
    ("golang", ("golang", "go lang", " go ")),
    ("rust", ("rust",)),
    ("c++", ("c++", "cpp", "c plus plus")),
    ("c#", ("c#", "csharp", "c sharp", ".net")),
    ("ruby", ("ruby", "ruby on rails")),
    ("php", ("php",)),
    ("swift", ("swift",)),
    ("kotlin", ("kotlin",)),
    ("scala", ("scala",)),
    ("r", (" r ", "rstudio", "tidyverse", "ggplot")),
    # ── Web / frontend ──
    ("react", ("react", "react.js", "reactjs")),
    ("next.js", ("next.js", "nextjs")),
    ("vue", ("vue.js", "vuejs", "vue ")),
    ("angular", ("angular",)),
    ("svelte", ("svelte",)),
    ("node.js", ("node.js", "nodejs")),
    ("graphql", ("graphql",)),
    ("html", ("html", "html5", "css", "css3", "tailwind", "sass", "scss")),
    ("webpack", ("webpack", "vite", "rollup", "esbuild")),
    # ── Backend frameworks ──
    ("fastapi", ("fastapi",)),
    ("django", ("django",)),
    ("flask", ("flask",)),
    ("spring", ("spring boot", "spring framework", "spring mvc")),
    ("express", ("express.js", "expressjs")),
    ("rails", ("ruby on rails", "rails")),
    ("grpc", ("grpc", "protocol buffers", "protobuf")),
    ("rest api", ("rest api", "restful", "rest services", "openapi", "swagger")),
    ("graphql", ("graphql", "apollo")),
    # ── Mobile ──
    ("react native", ("react native",)),
    ("flutter", ("flutter", "dart")),
    ("ios", ("ios development", "xcode", "swift ui")),
    ("android", ("android development", "android sdk")),
    # ── Data & ML ──
    ("sql", ("sql", "postgresql", "postgres", "mysql", "sqlite", "mariadb")),
    ("mongodb", ("mongodb", "mongo",)),
    ("redis", ("redis",)),
    ("elasticsearch", ("elasticsearch", "opensearch", "elastic")),
    ("dynamodb", ("dynamodb",)),
    ("cassandra", ("cassandra",)),
    ("neo4j", ("neo4j", "graph database")),
    ("spark", ("spark", "apache spark", "pyspark")),
    ("kafka", ("kafka", "apache kafka", "event streaming")),
    ("airflow", ("airflow", "apache airflow", "workflow orchestration")),
    ("dbt", ("dbt", "data build tool")),
    ("snowflake", ("snowflake",)),
    ("bigquery", ("bigquery", "big query")),
    ("databricks", ("databricks",)),
    ("pandas", ("pandas",)),
    ("numpy", ("numpy",)),
    ("scikit-learn", ("scikit-learn", "sklearn", "scikit learn")),
    ("tensorflow", ("tensorflow", "tf2", "keras")),
    ("pytorch", ("pytorch", "torch")),
    ("hugging face", ("hugging face", "transformers", "llm", "langchain", "llama")),
    ("tableau", ("tableau",)),
    ("power bi", ("power bi", "powerbi")),
    ("excel", ("excel", "advanced excel", "vlookup", "pivot")),
    # ── Cloud & infrastructure ──
    ("aws", ("aws", "amazon web services", "ec2", "s3", "lambda", "rds", "ecs", "eks", "cloudformation", "cdk")),
    ("gcp", ("gcp", "google cloud", "gke", "cloud run", "pubsub")),
    ("azure", ("azure", "azure devops", "aks")),
    ("docker", ("docker", "dockerfile", "container")),
    ("kubernetes", ("kubernetes", "k8s", "helm", "kubectl")),
    ("terraform", ("terraform", "pulumi", "infrastructure as code")),
    ("ansible", ("ansible",)),
    ("prometheus", ("prometheus", "grafana", "datadog", "observability")),
    ("ci/cd", ("ci/cd", "github actions", "gitlab ci", "jenkins", "circle ci", "travis")),
    ("linux", ("linux", "unix", "bash", "shell scripting")),
    ("microservices", ("microservices", "service mesh", "distributed systems", "event-driven")),
    ("git", ("git", "github", "gitlab", "version control")),
    # ── Security ──
    ("security", ("application security", "appsec", "penetration testing", "owasp", "soc", "siem", "iam", "oauth")),
    # ── Design & architecture ──
    ("figma", ("figma",)),
    ("autocad", ("autocad",)),
    ("revit", ("revit",)),
    ("bim", ("bim",)),
    ("system design", ("system design", "software architecture", "distributed architecture", "high availability")),
    # ── Business / domain ──
    ("seo", ("seo", "search engine optimization")),
    ("crm", ("crm", "salesforce", "hubspot")),
    ("project management", ("project management", "scrum", "agile", "kanban", "jira", "confluence")),
    ("product management", ("product management", "product roadmap", "product discovery", "okr")),
    ("data analysis", ("data analysis", "business intelligence", "analytics", "reporting")),
    # ── Operations & logistics ──
    ("customer support", ("customer support", "customer service", "ticketing", "zendesk")),
    ("food service", ("food service", "restaurant service", "guest service")),
    ("cash handling", ("cash handling", " pos ", "point of sale")),
    ("inventory management", ("inventory", "stock management")),
    # ── Soft / transferable ──
    ("leadership", ("leadership", "mentoring", "stakeholder management", "team management", "people management")),
    ("communication", ("communication", "presentation", "written communication", "technical writing")),
    ("problem solving", ("problem solving", "analytical thinking", "critical thinking")),
)

_LANGUAGE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("english", ("english", "ingilizce")),
    ("turkish", ("turkish", "türkçe", "turkce")),
    ("german", ("german", "deutsch", "almanca")),
    ("french", ("french", "français", "fransızca", "fransizca")),
    ("arabic", ("arabic", "arapça", "arapca")),
    ("spanish", ("spanish", "español", "ispanyolca")),
    ("italian", ("italian", "italyanca")),
)

_EDUCATION_HINT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("doctorate", ("phd", "doctorate", "doctoral")),
    ("master", ("master", "msc", "mba", "yüksek lisans", "yuksek lisans")),
    ("bachelor", ("bachelor", "bs", "ba", "lisans")),
    ("associate", ("associate", "ön lisans", "on lisans")),
    ("high_school", ("high school", "lise")),
)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return _WHITESPACE_PATTERN.sub(" ", value).strip()


def normalize_job_title(value: str | None) -> str:
    return normalize_text(value).casefold()


def normalize_company_name(value: str | None) -> str:
    return normalize_text(value).casefold()


def normalize_location_text(value: str | None) -> str | None:
    normalized = normalize_text(value)
    return normalized or None


def normalize_url_for_dedup(value: str | None) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return ""
    parts = urlsplit(normalized)
    scheme = parts.scheme.casefold() or "https"
    netloc = parts.netloc.casefold()
    path = _MULTI_SLASH_PATTERN.sub("/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def extract_location_city(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    lowered = normalized.casefold()
    if "remote" in lowered:
        return "Remote"
    if "hybrid" in lowered and "," not in normalized and " - " not in normalized:
        return "Hybrid"
    for delimiter in (",", " - ", "/"):
        if delimiter in normalized:
            candidate = normalize_text(normalized.split(delimiter, 1)[0])
            return candidate or normalized
    return normalized


def infer_workplace_type(location_text: str | None) -> str | None:
    normalized = normalize_text(location_text).casefold()
    if not normalized:
        return None
    if "hybrid" in normalized:
        return "hybrid"
    if "remote" in normalized:
        return "remote"
    if any(keyword in normalized for keyword in ("on-site", "onsite", "office", "in person", "sahada", "yerinde")):
        return "onsite"
    return None


def extract_location_country(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    lowered = normalized.casefold()
    if "remote" in lowered or "hybrid" in lowered:
        return None
    for delimiter in (",", " - ", "/"):
        if delimiter in normalized:
            parts = [normalize_text(part) for part in normalized.split(delimiter) if normalize_text(part)]
            if len(parts) >= 2:
                candidate = parts[-1]
                return candidate or None
    return None


def compute_description_completeness_score(
    description_text: str | None,
    description_html: str | None = None,
) -> float:
    text_value = strip_html(description_text) or strip_html(description_html)
    if not text_value:
        return 0.2
    length = len(text_value)
    if length >= 1200:
        return 1.0
    if length >= 700:
        return 0.92
    if length >= 350:
        return 0.82
    if length >= 180:
        return 0.68
    if length >= 80:
        return 0.52
    return 0.35


def infer_employment_type(
    title: str | None,
    location_text: str | None = None,
    description_text: str | None = None,
) -> str | None:
    haystack = " ".join(
        part
        for part in (
            normalize_text(title).casefold(),
            normalize_text(location_text).casefold(),
            normalize_text(description_text).casefold(),
        )
        if part
    )
    if not haystack:
        return None
    if any(keyword in haystack for keyword in ("intern", "internship", "staj")):
        return "internship"
    if any(keyword in haystack for keyword in ("contract", "contractor", "freelance", "consultant")):
        return "contract"
    if any(keyword in haystack for keyword in ("part time", "part-time", "yarı zamanlı", "yari zamanli")):
        return "part_time"
    if any(keyword in haystack for keyword in ("temporary", "temp", "fixed term", "fixed-term")):
        return "temporary"
    if any(keyword in haystack for keyword in ("full time", "full-time", "tam zamanlı", "tam zamanli")):
        return "full_time"
    return None


def infer_seniority(
    title: str | None,
    description_text: str | None = None,
) -> str | None:
    title_haystack = normalize_text(title).casefold()
    description_haystack = normalize_text(description_text).casefold()
    if not title_haystack and not description_haystack:
        return None
    ordered_rules = (
        ("executive", ("chief ", "chief-", "vp", "vice president", "cxo", "cto", "ceo", "cfo", "coo")),
        ("director", ("director", "head of", "head ")),
        ("principal", ("principal", "staff ")),
        ("lead", ("lead", "team lead", "manager")),
        ("senior", ("senior", "sr.", "sr ")),
        ("junior", ("junior", "jr.", "jr ", "entry level", "entry-level")),
        ("intern", ("intern", "internship", "staj")),
    )
    for label, keywords in ordered_rules:
        if any(keyword in title_haystack for keyword in keywords):
            return label
    for label, keywords in ordered_rules:
        if any(keyword in description_haystack for keyword in keywords):
            return label
    return "mid"


def tokenize_keywords(*values: str | None, limit: int = 24) -> tuple[str, ...]:
    seen: set[str] = set()
    tokens: list[str] = []
    for value in values:
        normalized = normalize_text(strip_html(value) or value).casefold()
        if not normalized:
            continue
        for token in re.findall(r"[a-zA-Z0-9.+#-]{2,}", normalized):
            cleaned = token.strip(".-")
            if not cleaned or cleaned in _STOPWORDS or cleaned.isdigit():
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            tokens.append(cleaned)
            if len(tokens) >= limit:
                return tuple(tokens)
    return tuple(tokens)


def infer_role_category(title: str | None, description_text: str | None = None) -> str | None:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return None
    for category, keywords in _ROLE_FAMILY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return None


def infer_department_family(title: str | None, description_text: str | None = None) -> str | None:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return None
    for department, keywords in _DEPARTMENT_RULES:
        if any(keyword in haystack for keyword in keywords):
            return department
    return None


def infer_job_discipline(title: str | None, description_text: str | None = None) -> str | None:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return None
    for discipline, keywords in _DISCIPLINE_RULES:
        if any(keyword in haystack for keyword in keywords):
            return discipline
    return None


_REQUIRED_SECTION_RE = re.compile(
    r"(?:required|must.have|must have|essential|minimum requirements?|qualifications?|what you.ll need"
    r"|we require|you must|you should have|hard requirements?|non.negotiable|technical requirements?)",
    re.IGNORECASE,
)
_PREFERRED_SECTION_RE = re.compile(
    r"(?:nice.to.have|nice if|preferred|plus points?|bonus points?|advantageous|would be great"
    r"|it would be|desired|a plus|an advantage|ideally|additional skills|good.to.have|would love)",
    re.IGNORECASE,
)


def extract_required_preferred_skill_terms(
    description_text: str | None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Parse job description into required and preferred sections; extract skill terms from each.

    Returns (required_skill_terms, preferred_skill_terms).
    Falls back to ((), ()) when no section markers are found.
    """
    if not description_text:
        return (), ()
    # Strip HTML tags but preserve newlines so paragraph structure survives
    cleaned = _HTML_TAG_PATTERN.sub(" ", description_text)
    # Collapse runs of spaces but preserve newlines
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned).strip()
    paragraphs = re.split(r"\n\s*\n|\n(?=\s*[-•*◦▪])", cleaned)

    required_parts: list[str] = []
    preferred_parts: list[str] = []
    current_ctx = "general"

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue
        header_zone = stripped[:180]
        if _REQUIRED_SECTION_RE.search(header_zone):
            current_ctx = "required"
        elif _PREFERRED_SECTION_RE.search(header_zone):
            current_ctx = "preferred"

        if current_ctx == "required":
            required_parts.append(stripped)
        elif current_ctx == "preferred":
            preferred_parts.append(stripped)

    if not required_parts and not preferred_parts:
        return (), ()

    required_terms = extract_skill_terms(None, " ".join(required_parts), limit=16) if required_parts else ()
    preferred_terms = extract_skill_terms(None, " ".join(preferred_parts), limit=12) if preferred_parts else ()
    req_set = set(required_terms)
    preferred_terms = tuple(t for t in preferred_terms if t not in req_set)
    return required_terms, preferred_terms


def extract_skill_terms(title: str | None, description_text: str | None = None, *, limit: int = 24) -> tuple[str, ...]:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return ()
    extracted: list[str] = []
    for skill_name, patterns in _SKILL_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            extracted.append(skill_name)
        if len(extracted) >= limit:
            break
    return tuple(extracted)


def extract_language_requirements(description_text: str | None, title: str | None = None) -> tuple[str, ...]:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return ()
    extracted: list[str] = []
    for language, patterns in _LANGUAGE_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            extracted.append(language)
    return tuple(extracted)


def infer_education_level_hint(description_text: str | None, title: str | None = None) -> str | None:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return None
    for education_level, patterns in _EDUCATION_HINT_PATTERNS:
        if any(pattern in haystack for pattern in patterns):
            return education_level
    return None


def infer_years_experience_min(description_text: str | None) -> int | None:
    haystack = normalize_text(description_text).casefold()
    if not haystack:
        return None
    candidates: list[int] = []
    for pattern in _EXPERIENCE_PATTERNS:
        for match in pattern.finditer(haystack):
            if len(match.groups()) == 1:
                candidates.append(int(match.group(1)))
            elif len(match.groups()) >= 2:
                candidates.append(int(match.group(1)))
    if not candidates:
        return None
    return min(candidates)


def infer_management_track(title: str | None, description_text: str | None = None) -> bool:
    haystack = " ".join(part for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold()) if part)
    if not haystack:
        return False
    indicators = (
        "manager",
        "head of",
        "director",
        "vp",
        "vice president",
        "lead a team",
        "manage a team",
        "people management",
        "line manager",
    )
    return any(indicator in haystack for indicator in indicators)


def compute_match_readiness_score(
    *,
    role_family: str | None,
    job_discipline: str | None,
    title_tokens: Iterable[str],
    skill_terms: Iterable[str],
    location_tokens: Iterable[str],
    language_requirements: Iterable[str],
    education_level_hint: str | None,
    years_experience_min: int | None,
    workplace_type: str | None,
    employment_type: str | None,
    seniority: str | None,
    description_text: str | None,
) -> float:
    score = 0.0
    if role_family:
        score += 0.18
    if job_discipline:
        score += 0.12
    if title_tokens:
        score += min(0.16, len(tuple(title_tokens)) * 0.02)
    if skill_terms:
        score += min(0.18, len(tuple(skill_terms)) * 0.025)
    if location_tokens:
        score += min(0.08, len(tuple(location_tokens)) * 0.02)
    if language_requirements:
        score += min(0.05, len(tuple(language_requirements)) * 0.025)
    if education_level_hint:
        score += 0.05
    if years_experience_min is not None:
        score += 0.07
    if workplace_type:
        score += 0.05
    if employment_type:
        score += 0.05
    if seniority:
        score += 0.05
    description_score = compute_description_completeness_score(description_text)
    score += description_score * 0.12
    return round(max(0.2, min(1.0, score)), 4)


def build_canonical_job_key(
    *,
    company_name: str | None,
    title: str | None,
    location_text: str | None,
    apply_url: str | None,
    canonical_url: str | None = None,
    fallback_key: str | None = None,
) -> str:
    normalized_company = normalize_company_name(company_name)
    normalized_title = normalize_job_title(title)
    normalized_location = (normalize_location_text(location_text) or "").casefold()
    normalized_url = normalize_url_for_dedup(apply_url) or normalize_url_for_dedup(canonical_url)
    fallback = normalize_text(fallback_key).casefold()
    return "|".join(
        [
            normalized_company,
            normalized_title,
            normalized_location,
            normalized_url or fallback,
        ]
    )


def strip_html(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if not normalized:
        return None
    stripped = _HTML_TAG_PATTERN.sub(" ", normalized)
    collapsed = normalize_text(stripped)
    return collapsed or None


def serialize_raw_payload(payload: Any) -> str:
    if isinstance(payload, str):
        return normalize_text(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_raw_payload_hash(payload: Any) -> str:
    serialized = serialize_raw_payload(payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


_SENIORITY_RANK: dict[str, int] = {
    "intern": 1,
    "junior": 2,
    "mid": 3,
    "senior": 4,
    "lead": 5,
    "principal": 6,
    "director": 7,
    "executive": 8,
}

# Ordered from most- to least-senior so first match wins.
_PROFILE_SENIORITY_TITLE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("executive",  ("chief ", "cto", "ceo", "cfo", "coo", "vice president", " vp ")),
    ("director",   ("director", "head of ")),
    ("principal",  ("principal", "staff engineer", "distinguished")),
    ("lead",       ("tech lead", "team lead", "engineering lead", "lead engineer", "engineering manager")),
    ("senior",     ("senior", "sr.", "sr ")),
    ("junior",     ("junior", "jr.", "jr ", "entry level", "entry-level", "associate")),
    ("intern",     ("intern", "internship", "trainee")),
)

# Keywords inside description text that bump seniority
_PROFILE_SENIORITY_DESC_INDICATORS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lead",    ("i led", "i managed", "led a team", "managed a team", "line managed", "was responsible for a team")),
    ("senior",  ("architected", "designed the system", "owned the", "drove the", "technical decision", "principal engineer")),
    ("junior",  ("internship", "first role", "entry level", "newly graduated")),
)


def infer_profile_seniority(
    experience_titles: list[str],
    experience_summaries: list[str],
    years_experience_total: int | None,
) -> str | None:
    """Infer a subscriber's effective seniority level from their experience history.

    Prioritises the most recent entries (last in list = most recent by convention).
    Falls back to years_experience_total if title signals are ambiguous.
    """
    if not experience_titles and years_experience_total is None:
        return None

    # Score each level based on title signals across all entries
    level_counts: dict[str, int] = {}
    # Weight recent entries more (last entry weight = n, first = 1)
    len(experience_titles)
    for idx, title in enumerate(experience_titles):
        if not title:
            continue
        title_lower = normalize_text(title).casefold()
        weight = idx + 1  # more recent → higher index → higher weight
        for level, keywords in _PROFILE_SENIORITY_TITLE_RULES:
            if any(kw in title_lower for kw in keywords):
                level_counts[level] = level_counts.get(level, 0) + weight
                break  # first match wins per entry

    # Check description text for additional signals
    for summary in experience_summaries:
        if not summary:
            continue
        summary_lower = normalize_text(summary).casefold()
        for level, indicators in _PROFILE_SENIORITY_DESC_INDICATORS:
            if any(ind in summary_lower for ind in indicators):
                level_counts[level] = level_counts.get(level, 0) + 1

    if level_counts:
        inferred = max(level_counts, key=lambda lvl: (_SENIORITY_RANK.get(lvl, 3), level_counts[lvl]))
        return inferred

    # Fall back to years of experience
    if years_experience_total is not None:
        if years_experience_total <= 0:
            return "junior"
        if years_experience_total <= 2:
            return "junior"
        if years_experience_total <= 5:
            return "mid"
        if years_experience_total <= 9:
            return "senior"
        return "lead"

    return None


_OWNERSHIP_SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("system_ownership", ("owned the", "took ownership", "end-to-end ownership", "responsible for the", "accountable for")),
    ("technical_leadership", ("led the", "tech lead", "technical lead", "mentored", "coached", "reviewed pull requests", "guided the team")),
    ("cross_functional_delivery", ("worked with product", "partnered with design", "collaborated with stakeholders", "cross-functional", "stakeholders")),
    ("architecture", ("architected", "designed the architecture", "defined technical direction", "designed systems")),
    ("operations_reliability", ("on-call", "incident response", "monitoring", "reliability", "sla", "observability")),
)


_IMPACT_SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("delivery", ("delivered", "launched", "shipped", "released", "rolled out", "implemented")),
    ("optimization", ("improved", "optimized", "reduced", "increased", "accelerated", "streamlined")),
    ("scale", ("scaled", "high traffic", "millions of", "large-scale", "distributed system", "high availability")),
    ("automation", ("automated", "automation", "eliminated manual", "reduced manual")),
    ("measurement", ("kpi", "metric", "measured", "a/b", "experiment", "conversion")),
)


def _extract_keyword_signals(
    description_text: str | None,
    rules: tuple[tuple[str, tuple[str, ...]], ...],
    *,
    title: str | None = None,
) -> tuple[str, ...]:
    haystack = " ".join(
        part
        for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold())
        if part
    )
    if not haystack:
        return ()
    return tuple(
        label
        for label, keywords in rules
        if any(keyword in haystack for keyword in keywords)
    )


def extract_ownership_signals(
    description_text: str | None,
    title: str | None = None,
) -> tuple[str, ...]:
    """Extract ownership / leadership / cross-functional evidence from profile or job text."""
    return _extract_keyword_signals(description_text, _OWNERSHIP_SIGNAL_RULES, title=title)


def extract_impact_signals(
    description_text: str | None,
    title: str | None = None,
) -> tuple[str, ...]:
    """Extract delivery / optimization / scale evidence from profile or job text."""
    return _extract_keyword_signals(description_text, _IMPACT_SIGNAL_RULES, title=title)


def infer_profile_responsibility_scope(
    experience_titles: Iterable[str | None],
    experience_summaries: Iterable[str | None],
    *,
    management_preference: bool | None = None,
    seniority_level: str | None = None,
) -> str | None:
    """Infer responsibility scope directly from profile experience text before falling back to seniority."""
    score_by_scope: dict[str, int] = {"ic": 0, "senior-ic": 0, "tech-lead": 0, "architect": 0, "manager": 0}

    for title in experience_titles:
        inferred = infer_responsibility_scope(None, title)
        if inferred is not None:
            score_by_scope[inferred] += 3

    for summary in experience_summaries:
        inferred = infer_responsibility_scope(summary)
        if inferred is not None:
            score_by_scope[inferred] += 2
        for signal in extract_ownership_signals(summary):
            if signal == "technical_leadership":
                score_by_scope["tech-lead"] += 1
            elif signal == "architecture":
                score_by_scope["architect"] += 1
            elif signal == "system_ownership":
                score_by_scope["senior-ic"] += 1

    if management_preference is True:
        score_by_scope["manager"] += 1

    if max(score_by_scope.values(), default=0) > 0:
        return max(score_by_scope, key=score_by_scope.get)

    if seniority_level is None:
        return None
    rank = _SENIORITY_RANK.get(seniority_level, 3)
    if management_preference is True and rank >= 5:
        return "manager"
    if rank >= 6:
        return "architect"
    if rank >= 5:
        return "tech-lead"
    if rank >= 4:
        return "senior-ic"
    return "ic"


_DOMAIN_SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fintech",      ("fintech", "financial technology", "banking", "payment", "lending", "insurance", "wealth management", "trading")),
    ("healthcare",   ("healthcare", "health tech", "medical", "clinical", "pharma", "biotech", "ehr", "emr")),
    ("ecommerce",    ("ecommerce", "e-commerce", "retail", "marketplace", "shopify", "consumer")),
    ("saas",         ("saas", "b2b software", "platform", "enterprise software", "multi-tenant")),
    ("startup",      ("startup", "early stage", "seed", "series a", "series b", "founding team", "fast-paced")),
    ("enterprise",   ("enterprise", "large-scale", "fortune 500", "global organisation")),
    ("gaming",       ("gaming", "game development", "unity", "unreal", "game engine")),
    ("mobility",     ("mobility", "automotive", "connected vehicle", "fleet", "logistics platform")),
    ("edtech",       ("edtech", "ed-tech", "education technology", "e-learning", "lms")),
    ("govtech",      ("govtech", "government", "public sector", "municipality")),
    ("deep_tech",    ("deep tech", "computer vision", "robotics", "embedded", "hardware", "iot", "edge computing")),
    ("cybersecurity",("cybersecurity", "cyber security", "infosec", "information security", "compliance")),
    ("media",        ("media", "content platform", "streaming", "video", "audio", "publishing")),
    ("real_estate",  ("real estate", "proptech", "property management")),
    ("construction", ("construction", "architecture firm", "civil engineering", "bim", "autocad")),
    ("hospitality",  ("hospitality", "hotel", "restaurant", "tourism", "food & beverage")),
    ("supply_chain", ("supply chain", "procurement", "logistics", "warehouse", "inventory")),
)


def extract_domain_signals(
    description_text: str | None,
    title: str | None = None,
) -> tuple[str, ...]:
    """Extract business/industry domain context signals from text."""
    return _extract_keyword_signals(description_text, _DOMAIN_SIGNAL_RULES, title=title)


_RESPONSIBILITY_SCOPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Ordered most→least senior: first match wins
    ("manager",   ("manage a team", "manage engineers", "people manager", "line manager", "grow and mentor")),
    ("architect",  ("architect solutions", "drive architecture", "define technical direction", "technical strategy", "design system architecture")),
    ("tech-lead",  ("technical lead", "tech lead", "lead engineers", "lead the team", "lead backend", "lead frontend", "lead development")),
    ("senior-ic",  ("own the", "you will own", "take ownership", "end-to-end ownership", "independently design", "drive the")),
    ("ic",         ("implement", "develop", "build", "contribute", "maintain", "support the team")),
)


def infer_responsibility_scope(
    description_text: str | None,
    title: str | None = None,
) -> str | None:
    """Infer the expected responsibility scope/level from job content."""
    haystack = " ".join(
        part
        for part in (normalize_text(title).casefold(), normalize_text(description_text).casefold())
        if part
    )
    if not haystack:
        return None
    for scope, keywords in _RESPONSIBILITY_SCOPE_RULES:
        if any(kw in haystack for kw in keywords):
            return scope
    return None
