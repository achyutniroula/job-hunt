"""Job archetype detection via Groq (10-token call)."""
from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM = (
    "You classify job postings. Reply with ONLY one of these exact labels: "
    "Cloud/DevOps Engineer, Backend Engineer, Frontend Engineer, Full Stack Engineer, "
    "Data Engineer, ML/AI Engineer, Cybersecurity Analyst, Systems/Infrastructure, "
    "Software Developer, Other. "
    "No explanation. No punctuation. Just the label."
)

_VALID = {
    "Cloud/DevOps Engineer", "Backend Engineer", "Frontend Engineer",
    "Full Stack Engineer", "Data Engineer", "ML/AI Engineer",
    "Cybersecurity Analyst", "Systems/Infrastructure", "Software Developer", "Other",
}

ARCHETYPE_WEIGHTS: dict[str, dict[str, list[str]]] = {
    "Cloud/DevOps Engineer": {
        "high": ["AWS", "GCP", "Azure", "Kubernetes", "Docker", "Terraform", "CI/CD",
                 "GitHub Actions", "Helm", "Jenkins", "CloudFormation", "Ansible",
                 "Linux", "bash", "IaC", "SRE", "monitoring", "Prometheus", "Grafana"],
        "medium": ["Python", "Go", "networking", "security", "microservices", "observability"],
    },
    "Backend Engineer": {
        "high": ["API", "REST", "microservices", "PostgreSQL", "Redis", "Python",
                 "Node.js", "Java", "Go", "FastAPI", "Django", "SQL", "message queue"],
        "medium": ["Docker", "AWS", "testing", "CI/CD", "GraphQL"],
    },
    "Frontend Engineer": {
        "high": ["React", "TypeScript", "JavaScript", "CSS", "HTML", "Vue", "Next.js",
                 "accessibility", "responsive", "webpack", "Vite"],
        "medium": ["Node.js", "REST API", "testing", "performance"],
    },
    "Full Stack Engineer": {
        "high": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST API", "Docker",
                 "Python", "AWS", "Next.js", "SQL"],
        "medium": ["CI/CD", "Redis", "testing", "microservices"],
    },
    "Data Engineer": {
        "high": ["Spark", "Airflow", "dbt", "Snowflake", "BigQuery", "ETL", "pipeline",
                 "Python", "SQL", "Kafka", "data warehouse", "Redshift"],
        "medium": ["AWS", "GCP", "Docker", "orchestration", "Databricks"],
    },
    "ML/AI Engineer": {
        "high": ["PyTorch", "TensorFlow", "Python", "ML", "model", "training",
                 "inference", "LLM", "NLP", "scikit-learn", "MLOps", "RAG"],
        "medium": ["AWS", "Docker", "API", "data pipeline", "GPU", "CUDA"],
    },
    "Cybersecurity Analyst": {
        "high": ["SIEM", "SOC", "incident response", "penetration testing", "firewall",
                 "vulnerability", "compliance", "OSCP", "threat", "CISSP", "zero trust"],
        "medium": ["Python", "Linux", "networking", "AWS", "identity management"],
    },
    "Systems/Infrastructure": {
        "high": ["Linux", "networking", "TCP/IP", "DNS", "load balancer", "storage",
                 "VMware", "bare metal", "RHEL", "kernel", "bash", "sysadmin"],
        "medium": ["Python", "Ansible", "monitoring", "security", "cloud"],
    },
    "Software Developer": {
        "high": ["Java", "Python", "C#", ".NET", "C++", "OOP", "algorithms",
                 "data structures", "Git", "agile", "unit testing"],
        "medium": ["REST API", "SQL", "Docker", "CI/CD"],
    },
    "Other": {
        "high": [],
        "medium": [],
    },
}


def get_archetype_weights(archetype: str) -> dict:
    return ARCHETYPE_WEIGHTS.get(archetype, ARCHETYPE_WEIGHTS["Other"])


async def detect_archetype(job_title: str, job_description: str) -> str:
    api_key = get_settings().groq_api_key
    if not api_key:
        return "Other"
    try:
        user_msg = f"Title: {job_title}\n\nDescription (first 300 chars): {job_description[:300]}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _GROQ_URL,
                json={
                    "model": _MODEL,
                    "messages": [
                        {"role": "system", "content": _SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    "max_tokens": 10,
                    "temperature": 0.0,
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
        if resp.status_code != 200:
            logger.warning("Archetype Groq call failed: %s", resp.status_code)
            return "Other"
        label = resp.json()["choices"][0]["message"]["content"].strip()
        return label if label in _VALID else "Other"
    except Exception as exc:
        logger.warning("Archetype detection failed: %s", exc)
        return "Other"
