import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CATEGORIZE_SYSTEM = """You are a SaaS portfolio analyst. Given a list of SaaS vendors,
return a JSON array where each element has:
- vendor: exact vendor name as provided
- category: one of ["Communication & Collaboration", "Identity & Security", "Device Management",
  "ITSM & Project Management", "HR & People", "Sales & CRM", "Marketing", "Engineering & DevTools",
  "Finance & Legal", "Customer Success", "Data & Analytics", "Productivity & Misc"]
- subcategory: specific function (e.g. "Email Security", "MDM", "ATS", "Password Manager")
- duplicate_risk: "High" | "Medium" | "None" — flag if this vendor's function overlaps
  with another vendor in the list
- duplicate_of: vendor name it duplicates, or null
- consolidation_note: one sentence if duplicate_risk is High or Medium, else null

Return ONLY the JSON array. No markdown, no preamble."""

SUMMARY_SYSTEM = """You are a senior IT Operations Manager writing an executive-level SaaS audit
report for the CTO and CFO. Your tone is direct, data-driven, and decisive.

You will receive a JSON summary of audit findings. Write a structured report with these sections:

## Portfolio Overview
2-3 sentences on overall portfolio health, total spend, vendor count.

## Top 3 Findings
Numbered list. Each finding: one bold headline sentence + 2-3 sentences of context and data.

## Security Posture
2-3 sentences on SSO/SAML/SCIM/SOC2 coverage. Flag the highest-risk gaps.

## Waste & Optimization Opportunities
2-3 sentences. Lead with total estimated recoverable waste in dollars.

## Recommended Actions (Next 90 Days)
Numbered list of 5 specific, actionable recommendations. Each should reference specific vendors
or numbers. Format: ACTION — rationale (savings or risk reduction).

Be direct. Use the specific dollar figures and vendor names provided. Do not hedge."""


def categorize_vendors(vendors: list[dict]) -> list[dict]:
    vendor_names = [{"vendor": v["vendor"]} for v in vendors]
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=CATEGORIZE_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(vendor_names)}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_executive_summary(audit_summary: dict) -> str:
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SUMMARY_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(audit_summary)}],
    )
    return msg.content[0].text.strip()
