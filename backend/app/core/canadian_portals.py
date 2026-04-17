from typing import TypedDict


class PortalConfig(TypedDict):
    name: str
    city: str
    province: str
    ats: str            # "greenhouse" | "lever" | "ashby" | "workday" | "custom"
    url: str            # direct careers page URL
    greenhouse_id: str | None
    lever_id: str | None
    ashby_id: str | None


CANADIAN_PORTALS: list[PortalConfig] = [
    # === GREENHOUSE ===
    {"name": "Shopify", "city": "Ottawa", "province": "ON", "ats": "greenhouse",
     "url": "https://www.shopify.com/careers", "greenhouse_id": "shopify", "lever_id": None, "ashby_id": None},
    {"name": "Wealthsimple", "city": "Toronto", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/wealthsimple", "greenhouse_id": "wealthsimple", "lever_id": None, "ashby_id": None},
    {"name": "Clio", "city": "Vancouver", "province": "BC", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/clio", "greenhouse_id": "clio", "lever_id": None, "ashby_id": None},
    {"name": "Hootsuite", "city": "Vancouver", "province": "BC", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/hootsuite", "greenhouse_id": "hootsuite", "lever_id": None, "ashby_id": None},
    {"name": "Lightspeed", "city": "Montreal", "province": "QC", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/lightspeedhq", "greenhouse_id": "lightspeedhq", "lever_id": None, "ashby_id": None},
    {"name": "Nuvei", "city": "Montreal", "province": "QC", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/nuvei", "greenhouse_id": "nuvei", "lever_id": None, "ashby_id": None},
    {"name": "PointClickCare", "city": "Mississauga", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/pointclickcare", "greenhouse_id": "pointclickcare", "lever_id": None, "ashby_id": None},
    {"name": "ApplyBoard", "city": "Kitchener", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/applyboard", "greenhouse_id": "applyboard", "lever_id": None, "ashby_id": None},
    {"name": "Clearco", "city": "Toronto", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/clearco", "greenhouse_id": "clearco", "lever_id": None, "ashby_id": None},
    {"name": "League", "city": "Toronto", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/league", "greenhouse_id": "league", "lever_id": None, "ashby_id": None},

    {"name": "D2L", "city": "Kitchener", "province": "ON", "ats": "greenhouse",
     "url": "https://boards.greenhouse.io/D2L", "greenhouse_id": "D2L", "lever_id": None, "ashby_id": None},

    # === LEVER ===
    {"name": "Koho", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/koho", "greenhouse_id": None, "lever_id": "koho", "ashby_id": None},
    {"name": "1Password", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/1password", "greenhouse_id": None, "lever_id": "1password", "ashby_id": None},
    {"name": "Ritual", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/ritual", "greenhouse_id": None, "lever_id": "ritual", "ashby_id": None},
    {"name": "Konrad Group", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/konrad", "greenhouse_id": None, "lever_id": "konrad", "ashby_id": None},
    {"name": "Financeit", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/financeit", "greenhouse_id": None, "lever_id": "financeit", "ashby_id": None},
    {"name": "Benevity", "city": "Calgary", "province": "AB", "ats": "lever",
     "url": "https://jobs.lever.co/benevity", "greenhouse_id": None, "lever_id": "benevity", "ashby_id": None},
    {"name": "Axiom Zen", "city": "Vancouver", "province": "BC", "ats": "lever",
     "url": "https://jobs.lever.co/axiomzen", "greenhouse_id": None, "lever_id": "axiomzen", "ashby_id": None},
    {"name": "Tulip Retail", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/tulip", "greenhouse_id": None, "lever_id": "tulip", "ashby_id": None},
    {"name": "Nudge", "city": "Toronto", "province": "ON", "ats": "lever",
     "url": "https://jobs.lever.co/nudge", "greenhouse_id": None, "lever_id": "nudge", "ashby_id": None},

    # === ASHBY ===
    {"name": "Cohere", "city": "Toronto", "province": "ON", "ats": "ashby",
     "url": "https://jobs.ashbyhq.com/cohere", "greenhouse_id": None, "lever_id": None, "ashby_id": "cohere"},
    {"name": "Properly", "city": "Toronto", "province": "ON", "ats": "ashby",
     "url": "https://jobs.ashbyhq.com/properly", "greenhouse_id": None, "lever_id": None, "ashby_id": "properly"},
    {"name": "Ramp Network", "city": "Toronto", "province": "ON", "ats": "ashby",
     "url": "https://jobs.ashbyhq.com/ramp", "greenhouse_id": None, "lever_id": None, "ashby_id": "ramp"},

    {"name": "FDM Group", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://www.fdmgroup.com/careers/our-opportunities/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},

    # === GOVERNMENT / PUBLIC SECTOR ===
    {"name": "Government of Canada (GC Jobs)", "city": "Ottawa", "province": "ON", "ats": "custom",
     "url": "https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page1710?poster=1&noOfJobs=25",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Ontario Public Service", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://www.gojobs.gov.on.ca/Jobs.aspx",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "City of Toronto", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://jobs.toronto.ca/jobsatcity/search/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},

    # === MAJOR CANADIAN TECH / ENTERPRISE ===
    {"name": "RBC (Royal Bank)", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://jobs.rbc.com/ca/en/search-results?keywords=software",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "TD Bank", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://jobs.td.com/en-CA/job-search-results/?keyword=developer",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Telus", "city": "Vancouver", "province": "BC", "ats": "custom",
     "url": "https://www.telus.com/en/about/careers/job-opportunities",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Bell Canada", "city": "Montreal", "province": "QC", "ats": "custom",
     "url": "https://jobs.bell.ca/ca/en/search-results",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "CGI Group", "city": "Montreal", "province": "QC", "ats": "custom",
     "url": "https://www.cgi.com/canada/en-ca/careers",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "OpenText", "city": "Waterloo", "province": "ON", "ats": "custom",
     "url": "https://careers.opentext.com/search/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "BlackBerry", "city": "Waterloo", "province": "ON", "ats": "custom",
     "url": "https://careers.blackberry.com/en/search-jobs",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Manulife", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://careers.manulife.com/global/en/search-results",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "CIBC", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://cibc.wd3.myworkdayjobs.com/en-US/CIBC_ExternalCareers",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Scotiabank", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://jobs.scotiabank.com/search/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},

    # === CLOUD / DEVOPS FOCUSED (Canada offices) ===
    {"name": "AWS Canada", "city": "Vancouver", "province": "BC", "ats": "custom",
     "url": "https://www.amazon.jobs/en/locations/vancouver-british-columbia",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Google Canada", "city": "Waterloo", "province": "ON", "ats": "custom",
     "url": "https://careers.google.com/locations/waterloo/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Microsoft Canada", "city": "Vancouver", "province": "BC", "ats": "custom",
     "url": "https://careers.microsoft.com/us/en/search-results?locations=Canada",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "IBM Canada", "city": "Markham", "province": "ON", "ats": "custom",
     "url": "https://www.ibm.com/employment/search/?country=CA",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
    {"name": "Limelight Networks / Edgio", "city": "Toronto", "province": "ON", "ats": "custom",
     "url": "https://edg.io/company/careers/",
     "greenhouse_id": None, "lever_id": None, "ashby_id": None},
]
