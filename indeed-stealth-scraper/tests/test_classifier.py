"""
tests/test_classifier.py — Unit tests for the strict 4-layer IT classifier.
No network required.  Run:  python tests/test_classifier.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from indeed_scraper.it_classifier import classify_it_job, extract_level

PASS = FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {label}", flush=True)
    else:
        FAIL += 1
        print(f"  FAIL  {label}", flush=True)


# ---------------------------------------------------------------------------
# Level extraction
# ---------------------------------------------------------------------------

def test_levels():
    print("\n--- Level extraction ---", flush=True)
    cases = [
        ("Senior Software Engineer",      "senior"),
        ("Junior Python Developer",        "junior"),
        ("Jr. Backend Developer",          "junior"),
        ("Entry Level Data Analyst",       "junior"),
        ("Lead Software Engineer",         "lead"),
        ("Tech Lead",                      "lead"),
        ("Engineering Manager",            "manager"),
        ("Staff Engineer",                 "principal"),
        ("Principal Architect",            "principal"),
        ("Director of Engineering",        "executive"),
        ("VP of Technology",               "executive"),
        ("CTO",                            "executive"),
        ("Mid-Level Developer",            "mid"),
        ("Software Engineer",              "unknown"),
        ("Intern - Software Development",  "intern"),
        ("Co-op Student",                  "intern"),
    ]
    for title, expected in cases:
        check(f"extract_level({title!r}) == {expected!r}", extract_level(title) == expected)


# ---------------------------------------------------------------------------
# IT true positives
# ---------------------------------------------------------------------------

def test_it_true_positives():
    print("\n--- IT true positives ---", flush=True)
    cases = [
        {
            "title": "Senior Python Developer",
            "desc":  "Build REST APIs using FastAPI and Docker. AWS, PostgreSQL, CI/CD pipelines, Git.",
        },
        {
            "title": "DevOps Engineer",
            "desc":  "Manage Kubernetes clusters on GCP. Jenkins, Terraform, Docker, Ansible, Linux.",
        },
        {
            "title": "Cloud Software Engineer",
            "desc":  "Design microservices with Azure, Terraform, Docker, Python, SQL, and Git.",
        },
        {
            "title": "Machine Learning Engineer",
            "desc":  "PyTorch, TensorFlow, Python, AWS SageMaker, SQL, Docker, Git, ML pipelines.",
        },
        {
            "title": "IT Support Specialist",
            "desc":  "Manage Active Directory, Linux servers, Jira, ServiceNow, Windows Server.",
        },
        {
            "title": "Cybersecurity Analyst",
            "desc":  "SIEM, Splunk, firewall management, Linux, Python, Azure, API security.",
        },
        {
            "title": "Data Engineer",
            "desc":  "Build ETL pipelines using Python, SQL, AWS, Spark, Terraform, and Docker.",
        },
        {
            "title": "Systems Administrator",
            "desc":  "Windows Server, Linux, Active Directory, AWS, Jira, Python scripting, Git.",
        },
    ]
    for job in cases:
        r = classify_it_job(job["title"], job["desc"])
        check(f"is_it=True  {job['title']!r}", r["is_it"] is True)
        check(f"  reason present", bool(r["reason"]))


# ---------------------------------------------------------------------------
# IT true negatives — strict non-IT roles
# ---------------------------------------------------------------------------

def test_it_true_negatives():
    print("\n--- IT true negatives ---", flush=True)
    cases = [
        {
            "title": "Registered Nurse",
            "desc":  "Provide patient care in ICU. Administer medications, monitor vital signs.",
        },
        {
            "title": "Accountant",
            "desc":  "Prepare financial statements, tax returns, payroll. QuickBooks, Excel.",
        },
        {
            "title": "Truck Driver",
            "desc":  "Transport goods between warehouses. Class A licence, clean driving record.",
        },
        {
            "title": "Chef de Cuisine",
            "desc":  "Oversee kitchen operations, create menus, manage kitchen staff.",
        },
        {
            "title": "Civil Engineer",
            "desc":  "Design road and bridge infrastructure. AutoCAD, site inspections, permits.",
        },
        {
            "title": "Mining Estimator",
            "desc":  "Cost estimation for open-pit mining projects. Geotechnical reports, safety.",
        },
        {
            "title": "HR Generalist",
            "desc":  "Recruitment, onboarding, performance reviews, benefits administration.",
        },
        {
            "title": "Sales Manager",
            "desc":  "Lead sales team, build client relationships, negotiate contracts.",
        },
        {
            "title": "Mechanical Engineer",
            "desc":  "Design HVAC systems, CAD modelling, thermodynamics, pressure testing.",
        },
        {
            "title": "Legal Clerk",
            "desc":  "Draft legal documents, file court papers, client intake, legal research.",
        },
    ]
    for job in cases:
        r = classify_it_job(job["title"], job["desc"])
        check(f"is_it=False {job['title']!r}  (reason: {r['reason'][:60]})", r["is_it"] is False)


# ---------------------------------------------------------------------------
# Layer 1: title scoring edge cases
# ---------------------------------------------------------------------------

def test_title_layer():
    print("\n--- Title layer edge cases ---", flush=True)

    # "engineer" alone should NOT pass title layer
    r = classify_it_job("Senior Engineer", "General engineering role, no tech stack mentioned.")
    check("'Senior Engineer' alone: title_score < 2", r["layers"]["title_score"] < 2)

    # "software engineer" should pass
    r = classify_it_job("Software Engineer", "General role.")
    check("'Software Engineer': title_score >= 2", r["layers"]["title_score"] >= 2)

    # "cloud engineer" should pass (conditional)
    r = classify_it_job("Cloud Engineer", "Works with infrastructure.")
    check("'Cloud Engineer': title_score >= 2", r["layers"]["title_score"] >= 2)

    # "business analyst" should NOT pass title (no systems/data/IT)
    r = classify_it_job("Business Analyst", "Gather requirements, liaise with vendors.")
    check("'Business Analyst': title_score < 2", r["layers"]["title_score"] < 2)

    # "data analyst" should pass (data is whitelist + analyst condition met)
    r = classify_it_job("Data Analyst", "BI reporting.")
    check("'Data Analyst': title_score >= 2", r["layers"]["title_score"] >= 2)

    # blacklist: mining estimator
    r = classify_it_job("Mining Estimator", "Cost estimation for mining projects.")
    check("'Mining Estimator': has blacklist hit", len(r["layers"]["title_black"]) > 0)

    # blacklist: civil engineer (civil is blacklisted, engineer conditional requires software/cloud/data)
    r = classify_it_job("Civil Engineer", "Road design, AutoCAD.")
    check("'Civil Engineer': is_it=False", r["is_it"] is False)

    # blacklist should not fire on "IT Systems Administrator"
    r = classify_it_job("IT Systems Administrator", "Manage servers and network.")
    check("'IT Systems Administrator': is_it=True", r["is_it"] is True)


# ---------------------------------------------------------------------------
# Layer 3: skill extraction
# ---------------------------------------------------------------------------

def test_skill_layer():
    print("\n--- Skill extraction ---", flush=True)
    desc = "Proficiency in Python, AWS, Docker, Kubernetes, SQL, Git required."
    r = classify_it_job("Analyst", desc)   # weak title, strong skills
    check("skill_count >= 3", r["layers"]["skill_count"] >= 3)
    check("python in skills",     "python"     in r["layers"]["skills"])
    check("aws in skills",        "aws"        in r["layers"]["skills"])
    check("docker in skills",     "docker"     in r["layers"]["skills"])
    check("kubernetes in skills", "kubernetes" in r["layers"]["skills"])
    check("sql in skills",        "sql"        in r["layers"]["skills"])

    # 2 skills should NOT pass skill layer alone
    r2 = classify_it_job("Consultant", "Uses Python and SQL for reporting.")
    check("2 skills: skill_count < 3", r2["layers"]["skill_count"] < 3)


# ---------------------------------------------------------------------------
# Layer 4: metadata
# ---------------------------------------------------------------------------

def test_metadata_layer():
    print("\n--- Metadata layer ---", flush=True)
    r = classify_it_job(
        "Analyst",
        "General role.",
        metadata={"categoryLabel": "Information Technology"},
    )
    check("metadata IT category boosts", r["layers"]["meta_score"] == 1.0)
    check("metadata makes is_it=True",   r["is_it"] is True)

    r2 = classify_it_job(
        "Analyst",
        "General role.",
        metadata={"categoryLabel": "Finance"},
    )
    check("non-IT metadata: meta_score=0", r2["layers"]["meta_score"] == 0.0)


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

def test_output_schema():
    print("\n--- Output schema ---", flush=True)
    r = classify_it_job("Python Developer", "Python, AWS, Docker, SQL, Git CI/CD Kubernetes.")
    check("is_it key present",        "is_it"      in r)
    check("confidence key present",   "confidence" in r)
    check("reason key present",       "reason"     in r)
    check("layers key present",       "layers"     in r)
    check("confidence in [0,1]",      0.0 <= r["confidence"] <= 1.0)
    check("reason is str",            isinstance(r["reason"], str))
    check("reason non-empty",         bool(r["reason"]))
    check("emb_backend in layers",    "emb_backend" in r["layers"])
    check("emb_backend valid value",  r["layers"]["emb_backend"] in ("embedding", "tfidf"))


# ---------------------------------------------------------------------------
# job_parser integration
# ---------------------------------------------------------------------------

def test_parser_integration():
    print("\n--- job_parser integration ---", flush=True)
    from indeed_scraper.job_parser import parse_job

    raw = {
        "jobkey": "abc123",
        "title": "Senior Python Developer",
        "company": "Acme Corp",
        "formattedLocation": "Toronto, ON",
        "snippet": "Python, FastAPI, Docker, AWS, PostgreSQL, SQL, Git, Kubernetes.",
        "pubDate": 1712534400000,
    }
    job = parse_job(raw)
    check("parse_job returns dict",     isinstance(job, dict))
    check("is_it_job field present",    "is_it_job"  in job)
    check("it_confidence present",      "it_confidence" in job)
    check("it_skills present",          "it_skills"  in job)
    check("it_reason present",          "it_reason"  in job)
    check("is_it_job is True",          job["is_it_job"] is True)
    check("level == 'senior'",          job["level"] == "senior")
    check("it_skills is list",          isinstance(job["it_skills"], list))
    check("it_reason is str",           isinstance(job["it_reason"], str))

    raw_nurse = {
        "jobkey": "nurse01",
        "title": "Registered Nurse",
        "company": "Toronto General",
        "formattedLocation": "Toronto, ON",
        "snippet": "ICU patient care, medication administration, vital signs monitoring.",
    }
    job_nurse = parse_job(raw_nurse)
    check("nurse is_it_job is False",   job_nurse["is_it_job"] is False)
    check("nurse level == 'unknown'",   job_nurse["level"] == "unknown")
    check("nurse reason says Not IT",   job_nurse["it_reason"].startswith("Not IT"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("*" * 60, flush=True)
    print("  IT CLASSIFIER — UNIT TESTS", flush=True)
    print("*" * 60, flush=True)

    test_levels()
    test_it_true_positives()
    test_it_true_negatives()
    test_title_layer()
    test_skill_layer()
    test_metadata_layer()
    test_output_schema()
    test_parser_integration()

    print(f"\n{'*' * 60}", flush=True)
    total = PASS + FAIL
    print(f"  {PASS}/{total} passed  |  {FAIL} failed", flush=True)
    if FAIL:
        print("  SOME TESTS FAILED", flush=True)
        sys.exit(1)
    else:
        print("  ALL TESTS PASSED", flush=True)
        sys.exit(0)
