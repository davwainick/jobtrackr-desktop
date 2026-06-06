"""Markdown export for Gap Analysis."""

from datetime import datetime
from typing import Any


def generate_gap_analysis_markdown(
    profile: dict[str, Any],
    strengths: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    full_name: str = "",
) -> str:
    export_date = datetime.now().strftime("%B %d, %Y")
    sal_min = f"${profile.get('target_salary_min') or 'N/A'}K"
    sal_max = f"${profile.get('target_salary_max') or 'N/A'}K"

    md = f"# Gap Analysis — {full_name or 'Job Seeker'}\n"
    md += f"*Exported: {export_date}*\n\n"
    md += "## Target Profile\n"
    md += f"- **Target Role:** {profile.get('target_role') or 'N/A'}\n"
    md += f"- **Target Salary:** {sal_min} – {sal_max}\n"
    md += f"- **Location:** {profile.get('target_location') or 'N/A'}\n"
    md += f"- **Relocation Date:** {profile.get('relocation_date') or 'N/A'}\n"
    md += f"- **Work Authorization:** {profile.get('work_authorization') or 'N/A'}\n"
    if profile.get("summary"):
        md += f"\n**Summary:**\n{profile['summary']}\n"
    md += "\n"

    md += "## 💪 Strengths to Lead With\n\n"
    if not strengths:
        md += "_No strengths added yet._\n\n"
    else:
        for s in strengths:
            md += f"### {s['strength']}\n"
            if s.get("talking_point"):
                md += f"**Talking Point:** {s['talking_point']}\n"
            md += "\n"

    md += "## ⚠️ Gaps & Objections to Prepare For\n\n"
    if not gaps:
        md += "_No gaps added yet._\n\n"
    else:
        for g in gaps:
            md += f"### {g['objection']}\n"
            if g.get("rebuttal"):
                md += f"**Rebuttal:** {g['rebuttal']}\n"
            if g.get("mitigation"):
                md += f"**Mitigation:** {g['mitigation']}\n"
            md += "\n"

    return md
