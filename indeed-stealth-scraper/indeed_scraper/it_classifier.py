"""
it_classifier.py — Strict 4-layer IT job classifier.

Layers
------
1. Title scoring  — strict whitelist (+2) / blacklist (-3) with conditional terms.
2. Semantic sim   — sentence-transformers cosine ≥ 0.72 (fallback: TF-IDF ≥ 0.18).
3. Skill count    — 23 specific technical skills; ≥ 3 → IT.
4. Metadata       — Indeed category/industry contains known IT labels.

Final: is_it = L1 OR L2 OR L3 OR L4
Output: {"is_it": bool, "confidence": float, "reason": str, "layers": {...}}
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

# ---------------------------------------------------------------------------
# Layer 1 — Title scoring
# ---------------------------------------------------------------------------

# Pure whitelist: these terms alone signal IT (+2 each)
_L1_PURE: dict[str, re.Pattern] = {k: re.compile(r"\b" + k + r"\b", re.I) for k in [
    "software", "developer", "devops", "security", "systems", "cloud",
]}
# "data" is IT only when it modifies something — handled in conditional block
# "IT" by itself (as a standalone word) is IT
_L1_PURE["it"] = re.compile(r"(?<![a-z])it(?![a-z])", re.I)   # standalone IT/It

# Conditional whitelist: term is IT only if accompanied by a qualifier (+2 each)
_L1_COND: list[tuple[re.Pattern, re.Pattern, str]] = [
    # (term_pattern, required_context, label)
    (re.compile(r"\bengineer\b", re.I),
     re.compile(r"\b(software|cloud|data|network|systems|security|devops|platform|site reliability|sre)\b", re.I),
     "engineer"),
    (re.compile(r"\banalyst\b", re.I),
     re.compile(r"\b(data|systems?|it|business intelligence|bi|cybersecurity|security|information)\b", re.I),
     "analyst"),
    (re.compile(r"\barchitect\b", re.I),
     re.compile(r"\b(cloud|software|solution|enterprise|security|technical|infrastructure)\b", re.I),
     "architect"),
    (re.compile(r"\btechnologist\b", re.I),
     re.compile(r"\b(it|systems?|information technology)\b", re.I),
     "technologist"),
    (re.compile(r"\bdata\b", re.I),
     re.compile(r"\b(engineer|scientist|analyst|architect|warehouse|platform|pipeline|governance)\b", re.I),
     "data"),
]

# Blacklist: strongly non-IT titles (-3 each)
_L1_BLACK: dict[str, re.Pattern] = {k: re.compile(r"\b" + re.escape(k) + r"\b", re.I) for k in [
    "accountant", "clerk", "trainee", "planner", "estimator",
    "lawyer", "paralegal", "geotechnical", "mining",
    "mechanical", "civil", "electrician",
    "retail", "cashier", "sales",
]}
# Multi-word blacklist entries
_L1_BLACK["customer service"] = re.compile(r"\bcustomer[\s\-]service\b", re.I)
_L1_BLACK["admin"]            = re.compile(r"\badmin(?:istrative)?\b", re.I)  # matches "admin"/"administrative" but NOT "administrator" (sysadmin etc.)
_L1_BLACK["law"]              = re.compile(r"\blaw\b", re.I)
_L1_BLACK["electrical"]       = re.compile(r"\belectrical\b(?!.*\bit\b)", re.I)  # "electrical" alone is blacklisted

_L1_THRESHOLD = 2.0


def _score_title(title: str) -> tuple[float, list[str], list[str]]:
    """Returns (score, matched_whitelist_labels, matched_blacklist_labels)."""
    score = 0.0
    hit_white: list[str] = []
    hit_black: list[str] = []

    for label, pat in _L1_PURE.items():
        if pat.search(title):
            score += 2.0
            hit_white.append(label)

    for term_pat, ctx_pat, label in _L1_COND:
        if term_pat.search(title) and ctx_pat.search(title):
            score += 2.0
            hit_white.append(label)

    for label, pat in _L1_BLACK.items():
        if pat.search(title):
            score -= 3.0
            hit_black.append(label)

    return score, hit_white, hit_black


# ---------------------------------------------------------------------------
# Layer 2 — Semantic similarity
# ---------------------------------------------------------------------------

_EMB_MODEL_NAME = "all-MiniLM-L6-v2"
_emb_model  = None   # None = not yet tried; False = unavailable
_ref_vec    = None

_REF_IT_TEXT = (
    "Software engineer developer programming Python Java JavaScript TypeScript "
    "AWS Azure GCP cloud Kubernetes Docker containers CI/CD DevOps Terraform Ansible "
    "databases SQL PostgreSQL MongoDB Redis REST API GraphQL microservices "
    "machine learning data science neural networks algorithms system design "
    "backend frontend fullstack web mobile Linux infrastructure networking "
    "cybersecurity security firewall penetration testing SIEM Splunk "
    "agile scrum sprint git code review unit testing deployment pipeline SRE "
    "information technology IT systems administrator helpdesk technical support"
)

_EMB_THRESHOLD  = 0.72
_TFIDF_FALLBACK = 0.18


def _load_emb_model():
    global _emb_model
    if _emb_model is not None:
        return None if _emb_model is False else _emb_model
    try:
        from sentence_transformers import SentenceTransformer
        _emb_model = SentenceTransformer(_EMB_MODEL_NAME, device="cpu")
    except Exception:
        _emb_model = False
    return None if _emb_model is False else _emb_model


def _semantic_sim(text: str) -> float:
    if not text:
        return 0.0
    model = _load_emb_model()
    if model is None:
        return _tfidf_sim(text)
    global _ref_vec
    import numpy as np
    if _ref_vec is None:
        _ref_vec = model.encode(_REF_IT_TEXT, normalize_embeddings=True)
    vec = model.encode(text[:1024], normalize_embeddings=True)
    return float(np.dot(vec, _ref_vec))


# TF-IDF fallback
_TFIDF_REF: dict[str, float] = {
    "software": 3, "code": 3, "programming": 3, "algorithm": 3, "deploy": 2,
    "cloud": 3, "aws": 3, "azure": 3, "gcp": 3, "kubernetes": 3, "docker": 3,
    "database": 2, "sql": 3, "api": 3, "rest": 2, "microservices": 3,
    "devops": 3, "linux": 3, "python": 3, "java": 3, "javascript": 3,
    "react": 3, "machine": 2, "learning": 2, "neural": 3, "pipeline": 2,
    "security": 2, "firewall": 2, "network": 2, "infrastructure": 2, "git": 3,
    "agile": 2, "scrum": 2, "system": 2, "technical": 1, "engineer": 1,
}
_TFIDF_MAG = math.sqrt(sum(w * w for w in _TFIDF_REF.values()))


def _tfidf_sim(text: str) -> float:
    tokens = re.findall(r"[a-z][a-z0-9+#.\-/]*", text.lower())
    if not tokens:
        return 0.0
    tf = Counter(tokens)
    n  = len(tokens)
    tf_n = {k: v / n for k, v in tf.items()}
    dot  = sum(tf_n.get(t, 0.0) * w for t, w in _TFIDF_REF.items())
    mag  = math.sqrt(sum(v * v for v in tf_n.values()))
    return (dot / (mag * _TFIDF_MAG)) if mag else 0.0


def _emb_threshold() -> float:
    return _EMB_THRESHOLD if _load_emb_model() is not None else _TFIDF_FALLBACK


def _emb_backend() -> str:
    return "embedding" if _load_emb_model() is not None else "tfidf"


# ---------------------------------------------------------------------------
# Layer 3 — Technical skill extraction (23 specific skills)
# ---------------------------------------------------------------------------

_SKILLS: dict[str, re.Pattern] = {
    "python":          re.compile(r"\bpython\b", re.I),
    "java":            re.compile(r"\bjava\b(?!script)", re.I),
    "c#":              re.compile(r"\bc#", re.I),
    "javascript":      re.compile(r"\b(javascript|js)\b", re.I),
    "sql":             re.compile(r"\bsql\b", re.I),
    "aws":             re.compile(r"\baws\b", re.I),
    "azure":           re.compile(r"\bazure\b", re.I),
    "gcp":             re.compile(r"\bgcp\b", re.I),
    "docker":          re.compile(r"\bdocker\b", re.I),
    "kubernetes":      re.compile(r"\b(kubernetes|k8s)\b", re.I),
    "terraform":       re.compile(r"\bterraform\b", re.I),
    "linux":           re.compile(r"\blinux\b", re.I),
    "windows server":  re.compile(r"\bwindows\s+server\b", re.I),
    "jira":            re.compile(r"\bjira\b", re.I),
    "confluence":      re.compile(r"\bconfluence\b", re.I),
    "servicenow":      re.compile(r"\bservicenow\b", re.I),
    "power bi":        re.compile(r"\bpower\s*bi\b", re.I),
    "tableau":         re.compile(r"\btableau\b", re.I),
    "api":             re.compile(r"\bapi\b", re.I),
    "git":             re.compile(r"\bgit\b", re.I),
    "devops":          re.compile(r"\bdevops\b", re.I),
    "ml":              re.compile(r"\bml\b", re.I),
    "ai":              re.compile(r"\bai\b", re.I),
}

_SKILL_THRESHOLD = 3


def _extract_skills(text: str) -> set[str]:
    return {name for name, pat in _SKILLS.items() if pat.search(text)}


# ---------------------------------------------------------------------------
# Layer 4 — Indeed metadata
# ---------------------------------------------------------------------------

_META_LABELS = [
    re.compile(r"\binformation technology\b", re.I),
    re.compile(r"\bsoftware\b", re.I),
    re.compile(r"\bcomputer\b", re.I),
    re.compile(r"(?<![a-z])it(?![a-z])", re.I),   # standalone "IT"
    re.compile(r"\bsystems\b", re.I),
    re.compile(r"\bcloud\b", re.I),
    re.compile(r"\bcybersecurity\b", re.I),
]


def _score_metadata(meta: dict[str, Any]) -> float:
    if not meta:
        return 0.0
    combined = " ".join(str(v) for v in meta.values() if v)
    return 1.0 if any(p.search(combined) for p in _META_LABELS) else 0.0


# ---------------------------------------------------------------------------
# Level extraction (unchanged)
# ---------------------------------------------------------------------------

_LEVEL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("intern",    re.compile(r"\b(intern|internship|co.?op)\b", re.I)),
    ("junior",    re.compile(r"\b(junior|jr\.?|entry.?level|entry level|associate developer|associate engineer)\b", re.I)),
    ("mid",       re.compile(r"\b(mid.?level|mid level|intermediate|level ii|level 2)\b", re.I)),
    ("senior",    re.compile(r"\b(senior|sr\.?|snr)\b", re.I)),
    ("lead",      re.compile(r"\b(tech lead|technical lead|team lead|lead developer|lead engineer|lead software)\b", re.I)),
    ("principal", re.compile(r"\b(principal|staff engineer|staff developer)\b", re.I)),
    ("manager",   re.compile(r"\b(engineering manager|em\b|development manager|it manager|software manager)\b", re.I)),
    ("executive", re.compile(r"\b(director|head of|vp |vice president|cto|cio|chief technology|chief information)\b", re.I)),
]


def extract_level(title: str) -> str:
    if not title:
        return "unknown"
    for level, pat in _LEVEL_PATTERNS:
        if pat.search(title):
            return level
    return "unknown"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_it_job(
    title: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """
    Classify whether a job is an IT/tech position.

    Returns
    -------
    {
        "is_it":      bool,
        "confidence": float,   # 0.0-1.0
        "reason":     str,     # human-readable explanation
        "layers": {
            "title_score":  float,
            "title_white":  list[str],
            "title_black":  list[str],
            "desc_sim":     float,
            "skill_count":  int,
            "skills":       list[str],
            "meta_score":   float,
            "emb_backend":  str,
        }
    }
    """
    meta    = metadata or {}
    desc    = description or ""
    ttl     = title or ""
    corpus  = f"{ttl} {desc}"   # combined for skill extraction

    # --- Layer 1: title ---
    t_score, t_white, t_black = _score_title(ttl)
    l1 = t_score >= _L1_THRESHOLD

    # --- Layer 2: semantic ---
    sim       = _semantic_sim(desc or ttl)
    threshold = _emb_threshold()
    l2 = sim >= threshold

    # --- Layer 3: skills ---
    skills = _extract_skills(corpus)
    l3 = len(skills) >= _SKILL_THRESHOLD

    # --- Layer 4: metadata ---
    meta_score = _score_metadata(meta)
    l4 = meta_score >= 0.5

    is_it = l1 or l2 or l3 or l4

    # Reason string
    triggers = []
    if l1:
        triggers.append(f"title keywords [{', '.join(t_white)}]")
    if l2:
        triggers.append(f"semantic similarity {sim:.3f} >= {threshold}")
    if l3:
        sample = sorted(skills)[:6]
        triggers.append(f"{len(skills)} skills [{', '.join(sample)}{'...' if len(skills) > 6 else ''}]")
    if l4:
        triggers.append("metadata category matched")

    if is_it:
        reason = "IT job: " + "; ".join(triggers)
    else:
        parts = []
        if t_black:
            parts.append(f"blacklisted title terms [{', '.join(t_black)}]")
        if not t_white:
            parts.append("no IT title keywords")
        if not skills:
            parts.append("no technical skills")
        reason = "Not IT: " + ("; ".join(parts) if parts else "insufficient IT signals")

    # Confidence: normalised weighted average
    c1 = min(1.0, max(0.0, t_score) / (2 * _L1_THRESHOLD))
    c2 = min(1.0, sim / max(threshold, 1e-9))
    c3 = min(1.0, len(skills) / (2 * _SKILL_THRESHOLD))
    c4 = meta_score
    confidence = round(0.35 * c1 + 0.25 * c2 + 0.30 * c3 + 0.10 * c4, 3)

    return {
        "is_it":      is_it,
        "confidence": confidence,
        "reason":     reason,
        "layers": {
            "title_score": round(t_score, 2),
            "title_white": t_white,
            "title_black": t_black,
            "desc_sim":    round(sim, 4),
            "skill_count": len(skills),
            "skills":      sorted(skills),
            "meta_score":  meta_score,
            "emb_backend": _emb_backend(),
        },
    }
