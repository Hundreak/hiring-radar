from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SkillCatalogEntry:
    """Canonical semantic skill entry."""

    canonical_name: str
    aliases: tuple[str, ...]
    category: str
    skill_type: str = "hard_skill"
    ambiguous: bool = False
    languages: tuple[str, ...] = ("tr", "en", "de")


SKILL_CATALOG: tuple[SkillCatalogEntry, ...] = (
    SkillCatalogEntry("Python", ("python",), "programming_languages"),
    SkillCatalogEntry("Java", ("java",), "programming_languages"),
    SkillCatalogEntry("JavaScript", ("javascript", "js"), "programming_languages"),
    SkillCatalogEntry("TypeScript", ("typescript", "ts"), "programming_languages"),
    SkillCatalogEntry("Go", ("go", "golang"), "programming_languages", ambiguous=True),
    SkillCatalogEntry("Rust", ("rust",), "programming_languages"),
    SkillCatalogEntry("C", ("c",), "programming_languages", ambiguous=True),
    SkillCatalogEntry("C++", ("c++", "cpp"), "programming_languages"),
    SkillCatalogEntry("C#", ("c#", "csharp"), "programming_languages"),
    SkillCatalogEntry("PHP", ("php",), "programming_languages"),
    SkillCatalogEntry("Ruby", ("ruby",), "programming_languages"),
    SkillCatalogEntry("Swift", ("swift",), "programming_languages", ambiguous=True),
    SkillCatalogEntry("Kotlin", ("kotlin",), "programming_languages"),
    SkillCatalogEntry("SQL", ("sql",), "databases"),
    SkillCatalogEntry("PostgreSQL", ("postgresql", "postgres", "postgre sql"), "databases"),
    SkillCatalogEntry("MySQL", ("mysql",), "databases"),
    SkillCatalogEntry("MongoDB", ("mongodb", "mongo"), "databases"),
    SkillCatalogEntry("Redis", ("redis",), "databases"),
    SkillCatalogEntry("Elasticsearch", ("elasticsearch", "elastic search"), "databases"),
    SkillCatalogEntry("Docker", ("docker",), "devops"),
    SkillCatalogEntry("Kubernetes", ("kubernetes", "k8s"), "devops"),
    SkillCatalogEntry("Terraform", ("terraform",), "devops"),
    SkillCatalogEntry("Ansible", ("ansible",), "devops"),
    SkillCatalogEntry("Git", ("git",), "developer_tools"),
    SkillCatalogEntry("GitHub Actions", ("github actions",), "devops"),
    SkillCatalogEntry("GitLab CI", ("gitlab ci",), "devops"),
    SkillCatalogEntry("Jenkins", ("jenkins",), "devops"),
    SkillCatalogEntry("Linux", ("linux",), "platforms"),
    SkillCatalogEntry("AWS", ("aws", "amazon web services"), "cloud_platforms", ambiguous=True),
    SkillCatalogEntry("Azure", ("azure",), "cloud_platforms"),
    SkillCatalogEntry("Google Cloud", ("google cloud", "gcp"), "cloud_platforms"),
    SkillCatalogEntry("FastAPI", ("fastapi",), "backend_frameworks"),
    SkillCatalogEntry("Django", ("django",), "backend_frameworks"),
    SkillCatalogEntry("Flask", ("flask",), "backend_frameworks"),
    SkillCatalogEntry("Spring Boot", ("spring boot",), "backend_frameworks"),
    SkillCatalogEntry("Node.js", ("node.js", "nodejs", "node"), "backend_frameworks", ambiguous=True),
    SkillCatalogEntry("Express", ("express",), "backend_frameworks", ambiguous=True),
    SkillCatalogEntry("NestJS", ("nestjs", "nest js"), "backend_frameworks"),
    SkillCatalogEntry("React", ("react", "reactjs", "react.js"), "frontend_frameworks", ambiguous=True),
    SkillCatalogEntry("Next.js", ("next.js", "nextjs"), "frontend_frameworks"),
    SkillCatalogEntry("Vue.js", ("vue", "vue.js", "vuejs"), "frontend_frameworks", ambiguous=True),
    SkillCatalogEntry("Angular", ("angular",), "frontend_frameworks"),
    SkillCatalogEntry("Svelte", ("svelte",), "frontend_frameworks"),
    SkillCatalogEntry("HTML", ("html", "html5"), "frontend_core"),
    SkillCatalogEntry("CSS", ("css", "css3"), "frontend_core"),
    SkillCatalogEntry("Tailwind CSS", ("tailwind", "tailwind css"), "frontend_frameworks"),
    SkillCatalogEntry("GraphQL", ("graphql",), "api_design"),
    SkillCatalogEntry("REST API", ("rest api", "restful api", "rest apis"), "api_design"),
    SkillCatalogEntry("gRPC", ("grpc",), "api_design"),
    SkillCatalogEntry("Prisma", ("prisma",), "backend_frameworks"),
    SkillCatalogEntry("tRPC", ("trpc", "t-rpc"), "api_design"),
    SkillCatalogEntry("LangChain", ("langchain",), "ai_ml"),
    SkillCatalogEntry("OpenAI", ("openai",), "ai_ml"),
    SkillCatalogEntry("Machine Learning", ("machine learning", "ml"), "ai_ml", ambiguous=True),
    SkillCatalogEntry("Deep Learning", ("deep learning",), "ai_ml"),
    SkillCatalogEntry("PyTorch", ("pytorch",), "ai_ml"),
    SkillCatalogEntry("TensorFlow", ("tensorflow",), "ai_ml"),
    SkillCatalogEntry("Pandas", ("pandas",), "data_engineering"),
    SkillCatalogEntry("NumPy", ("numpy",), "data_engineering"),
    SkillCatalogEntry("dbt", ("dbt",), "data_engineering"),
    SkillCatalogEntry("Airflow", ("airflow",), "data_engineering"),
    SkillCatalogEntry("Spark", ("spark", "apache spark"), "data_engineering", ambiguous=True),
    SkillCatalogEntry("Kafka", ("kafka", "apache kafka"), "messaging"),
    SkillCatalogEntry("RabbitMQ", ("rabbitmq",), "messaging"),
    SkillCatalogEntry("Microservices", ("microservices", "micro services"), "architecture"),
    SkillCatalogEntry("CI/CD", ("ci/cd", "cicd", "ci cd"), "devops"),
    SkillCatalogEntry("Pytest", ("pytest",), "quality_engineering"),
    SkillCatalogEntry("Unit Testing", ("unit testing",), "quality_engineering"),
    SkillCatalogEntry("Integration Testing", ("integration testing",), "quality_engineering"),
    SkillCatalogEntry("Communication", ("communication", "iletişim", "kommunikation"), "soft_skills", skill_type="soft_skill"),
    SkillCatalogEntry("Leadership", ("leadership", "liderlik", "führung"), "soft_skills", skill_type="soft_skill"),
    SkillCatalogEntry("Problem Solving", ("problem solving", "problem çözme", "problemlösung"), "soft_skills", skill_type="soft_skill"),
)


_ALIAS_INDEX: dict[str, SkillCatalogEntry] = {}
for _entry in SKILL_CATALOG:
    for _alias in _entry.aliases:
        _ALIAS_INDEX[_alias.casefold()] = _entry


def iter_skill_catalog_entries() -> tuple[SkillCatalogEntry, ...]:
    """Return the bundled skill catalog."""
    return SKILL_CATALOG


def find_skill_catalog_entry_by_alias(alias: str) -> SkillCatalogEntry | None:
    """Resolve one alias to its canonical skill catalog entry."""
    return _ALIAS_INDEX.get(alias.casefold().strip())
