"""CSV export for JobTrackr tables."""

import csv
import io
from typing import Any

HEADER_MAP: dict[str, str] = {
    "id": "ID", "company_name": "Company Name", "product_platform": "Product/Platform",
    "tier": "Tier", "status": "Status", "hq_location": "HQ Location",
    "remote_posture": "Remote Posture", "company_size": "Company Size",
    "funding_stage": "Funding Stage", "open_role": "Open Role",
    "why_you_fit": "Why You Fit", "website_url": "Website URL",
    "careers_url": "Careers URL", "linkedin_url": "LinkedIn URL",
    "last_checked": "Last Checked", "next_action": "Next Action",
    "due_date": "Due Date", "notes": "Notes", "created_at": "Created At",
    "updated_at": "Updated At", "job_title": "Job Title", "role_type": "Role Type",
    "date_found": "Date Found", "location": "Location", "salary_range": "Salary Range",
    "job_post_url": "Job Post URL", "required_technical_skills": "Required Technical Skills",
    "platform_tool_mentioned": "Platform/Tool Mentioned",
    "preferred_skills": "Preferred Skills", "soft_skills_emphasized": "Soft Skills Emphasized",
    "interesting_keywords": "Interesting Keywords", "do_you_qualify": "Do You Qualify",
    "gaps_identified": "Gaps Identified", "apply_status": "Apply Status",
    "full_name": "Full Name", "title": "Title", "contact_type": "Contact Type",
    "priority": "Priority", "email": "Email", "connection_degree": "Connection Degree",
    "warm_intro_available": "Warm Intro Available",
    "how_you_know_them": "How You Know Them", "date_connected": "Date Connected",
    "last_touchpoint": "Last Touchpoint", "notes_intel": "Notes/Intel",
    "subject_purpose": "Subject/Purpose", "date_sent": "Date Sent",
    "channel": "Channel", "message_type": "Message Type",
    "personalization_hook": "Personalization Hook",
    "response_received": "Response Received", "response_date": "Response Date",
    "response_summary": "Response Summary", "follow_up_due": "Follow Up Due",
    "follow_up_sent": "Follow Up Sent", "outcome": "Outcome",
    "company_id": "Company ID", "contact_id": "Contact ID",
}


def generate_csv(rows: list[dict[str, Any]]) -> str:
    """Generate CSV string from a list of row dicts."""
    if not rows:
        return ""
    keys = [k for k in rows[0].keys() if k not in ("user_id",)]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([HEADER_MAP.get(k, k) for k in keys])
    for row in rows:
        writer.writerow([
            "Yes" if v is True or v == 1 else "No" if v is False or v == 0 else (v if v is not None else "")
            for k, v in row.items() if k in keys
        ])
    return buf.getvalue()
