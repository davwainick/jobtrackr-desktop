"""Main application window for JobTrackr."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Optional
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from database import Database
from ui.widgets import DataTableView, DetailView, FormDialog, FormField
from export.csv_export import generate_csv
from export.markdown_export import generate_gap_analysis_markdown

# ── Option constants ─────────────────────────────────────────────────

COMPANY_STATUSES = ["Researching", "Targeting", "Contacted", "Applied", "Phone Screen", "Interview", "Offer", "Closed", "Watching"]
TIERS = ["Tier 1", "Tier 2", "Tier 3"]
REMOTE_POSTURES = ["Fully Remote", "Hybrid", "On-Site", "Flexible"]
COMPANY_SIZES = ["1-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10000+"]
FUNDING_STAGES = ["Bootstrapped", "Seed", "Series A", "Series B", "Series C+", "Public", "Private Equity"]
ROLE_TYPES = ["Full-Time", "Contract", "Part-Time", "Internship", "Other"]
QUALIFY_OPTIONS = ["Yes", "Partially", "No"]
APPLY_STATUSES = ["Yes", "No", "Later", "Applied", "Closed"]
CONTACT_TYPES = ["Hiring Manager", "Peer in Role", "Recruiter", "Executive", "Alumni", "Referral Source"]
PRIORITIES = ["HIGH", "MED", "LOW"]
CONNECTION_DEGREES = ["1st", "2nd", "3rd", "No connection"]
CHANNELS = ["LinkedIn DM", "Email", "LinkedIn InMail", "Phone", "Referral", "Other"]
MESSAGE_TYPES = ["Connection Request", "Introduction", "Role Inquiry", "Informational Ask", "Application Follow-Up", "Thank You", "Check-In"]
OUTCOMES = ["Pending", "Positive Response", "Call Scheduled", "Referred", "No Response", "Closed"]


class JobTrackrApp:
    """Main application class."""

    def __init__(self) -> None:
        self.db = Database()
        self.root = ttkb.Window(
            title="JobTrackr",
            themename="cosmo",
            size=(1200, 800),
            minsize=(900, 600),
        )
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Main layout: sidebar + content
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self._build_sidebar()

        # Content area
        self.content = ttk.Frame(self.root)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.current_view: Optional[ttk.Frame] = None

        # Show dashboard by default
        self._show_dashboard()

    def run(self) -> None:
        self.root.mainloop()

    def _on_close(self) -> None:
        self.db.close()
        self.root.destroy()

    # ── Sidebar ──────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        sidebar = ttk.Frame(self.root, width=220, style="secondary.TFrame")
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        # Logo
        logo_frame = ttk.Frame(sidebar)
        logo_frame.pack(fill="x", padx=15, pady=(15, 20))
        ttk.Label(logo_frame, text="📋 JobTrackr", font=("", 18, "bold"),
                  foreground="#4f46e5").pack(anchor="w")

        # Nav buttons
        nav_items = [
            ("📊  Dashboard", self._show_dashboard),
            ("🏢  Companies", self._show_companies),
            ("💼  Job Postings", self._show_job_postings),
            ("👤  Contacts", self._show_contacts),
            ("📤  Outreach Log", self._show_outreach),
            ("🎯  Gap Analysis", self._show_gap_analysis),
        ]

        for label, cmd in nav_items:
            btn = ttk.Button(
                sidebar, text=label, command=cmd, style="secondary.TButton", width=22,
            )
            btn.pack(fill="x", padx=10, pady=2)

        # Spacer
        ttk.Frame(sidebar).pack(fill="both", expand=True)

        # Settings + data location
        ttk.Separator(sidebar).pack(fill="x", padx=10, pady=5)
        ttk.Button(
            sidebar, text="⚙  Settings", command=self._show_settings,
            style="secondary.TButton", width=22,
        ).pack(fill="x", padx=10, pady=2)

        ttk.Label(sidebar, text=f"Data: local SQLite", font=("", 7),
                  foreground="gray").pack(padx=10, pady=(5, 10))

    def _switch_view(self, view: ttk.Frame) -> None:
        if self.current_view:
            self.current_view.destroy()
        self.current_view = view
        view.grid(row=0, column=0, sticky="nsew", in_=self.content)

    # ── Dashboard ────────────────────────────────────────────────────

    def _show_dashboard(self) -> None:
        frame = ttk.Frame(self.content)
        self._switch_view(frame)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # Title
        ttk.Label(frame, text="Dashboard", font=("", 20, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 5)
        )
        ttk.Label(frame, text="Your job search at a glance.", foreground="gray").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15)
        )

        # Summary cards
        counts = self.db.get_counts()
        cards_frame = ttk.Frame(frame)
        cards_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        for i, (label, count) in enumerate([
            ("Companies", counts["companies"]),
            ("Job Postings", counts["job_postings"]),
            ("Contacts", counts["contacts"]),
            ("Outreach This Month", counts["outreach_month"]),
        ]):
            cards_frame.columnconfigure(i, weight=1)
            card = ttk.LabelFrame(cards_frame, text=label, padding=15)
            card.grid(row=0, column=i, padx=5, sticky="ew")
            ttk.Label(card, text=str(count), font=("", 28, "bold")).pack(anchor="w")

        # Due Today
        due_frame = ttk.LabelFrame(frame, text="⚠ Due Today", padding=10)
        due_frame.grid(row=3, column=0, sticky="nsew", padx=(15, 5), pady=5)

        due_items = self.db.get_due_items()
        if not due_items:
            ttk.Label(due_frame, text="Nothing due today!", foreground="gray").pack(pady=20)
        else:
            for item in due_items[:8]:
                row = ttk.Frame(due_frame)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=f"[{item['type']}]", foreground="gray", width=10).pack(side="left")
                ttk.Label(row, text=item["name"], font=("", 10, "bold")).pack(side="left", padx=5)
                ttk.Label(row, text=item.get("action") or "", foreground="gray").pack(side="right")

        # Recent Activity
        recent_frame = ttk.LabelFrame(frame, text="🕐 Recent Activity", padding=10)
        recent_frame.grid(row=3, column=1, sticky="nsew", padx=(5, 15), pady=5)

        recent = self.db.get_recent_activity(8)
        if not recent:
            ttk.Label(recent_frame, text="No activity yet.", foreground="gray").pack(pady=20)
        else:
            for item in recent:
                row = ttk.Frame(recent_frame)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=f"[{item['type']}]", foreground="gray", width=12).pack(side="left")
                ttk.Label(row, text=item["name"], font=("", 10)).pack(side="left", padx=5)
                if item.get("status"):
                    ttk.Label(row, text=item["status"], foreground="#4f46e5").pack(side="right")

    # ── Companies ────────────────────────────────────────────────────

    def _show_companies(self) -> None:
        table = DataTableView(
            self.content,
            columns=[
                ("company_name", "Company", 180), ("tier", "Tier", 70),
                ("status", "Status", 100), ("hq_location", "Location", 120),
                ("remote_posture", "Remote", 100), ("open_role", "Open Role", 80),
                ("due_date", "Due Date", 100),
            ],
            on_select=lambda rid: self._show_company_detail(rid),
            on_add=self._add_company,
            on_delete=lambda ids: (self.db.delete_companies(ids), self._show_companies()),
            on_export=lambda: self._export_table("companies"),
            status_options=COMPANY_STATUSES,
            title="Companies",
            subtitle="Track your target companies and their status.",
        )
        self._switch_view(table)
        table.load_data(self.db.get_companies(), status_key="status")

    def _add_company(self, data: Optional[dict[str, Any]] = None, edit_id: str = "") -> None:
        dlg = FormDialog(self.root, "Edit Company" if edit_id else "Add Company", height=700)
        dlg.add_field("company_name", "Company Name", required=True)
        dlg.add_field("tier", "Tier", widget_type="combo", values=TIERS)
        dlg.add_field("status", "Status", widget_type="combo", values=COMPANY_STATUSES)
        dlg.add_field("product_platform", "Product/Platform")
        dlg.add_field("hq_location", "HQ Location")
        dlg.add_field("remote_posture", "Remote Posture", widget_type="combo", values=REMOTE_POSTURES)
        dlg.add_field("company_size", "Company Size", widget_type="combo", values=COMPANY_SIZES)
        dlg.add_field("funding_stage", "Funding Stage", widget_type="combo", values=FUNDING_STAGES)
        dlg.add_field("open_role", "Open Role", widget_type="check")
        dlg.add_field("why_you_fit", "Why You Fit", widget_type="text")
        dlg.add_field("website_url", "Website URL")
        dlg.add_field("careers_url", "Careers URL")
        dlg.add_field("linkedin_url", "LinkedIn URL")
        dlg.add_field("last_checked", "Last Checked (YYYY-MM-DD)")
        dlg.add_field("next_action", "Next Action")
        dlg.add_field("due_date", "Due Date (YYYY-MM-DD)")
        dlg.add_field("notes", "Notes", widget_type="text")

        if data:
            dlg.set_data(data)

        def on_save() -> None:
            form = dlg.get_data()
            if not form.get("company_name"):
                messagebox.showwarning("Validation", "Company name is required.")
                return
            if edit_id:
                self.db.update_company(edit_id, form)
            else:
                self.db.create_company(form)
            dlg.destroy()
            self._show_companies()

        dlg.save_btn.config(command=on_save)

    def _show_company_detail(self, company_id: str) -> None:
        company = self.db.get_company(company_id)
        if not company:
            return
        view = DetailView(self.content)
        self._switch_view(view)
        view.back_btn.config(command=self._show_companies)
        view.title_label.config(text=company["company_name"])
        view.edit_btn.config(command=lambda: self._add_company(data=company, edit_id=company_id))
        view.delete_btn.config(command=lambda: self._delete_and_back(
            lambda: self.db.delete_companies([company_id]), self._show_companies, company["company_name"]
        ))

        view.add_section_header("Details")
        for label, key in [
            ("Tier", "tier"), ("Status", "status"), ("Product/Platform", "product_platform"),
            ("HQ Location", "hq_location"), ("Remote Posture", "remote_posture"),
            ("Company Size", "company_size"), ("Funding Stage", "funding_stage"),
            ("Open Role", "open_role"), ("Last Checked", "last_checked"),
            ("Due Date", "due_date"), ("Next Action", "next_action"),
        ]:
            view.add_field_row(label, company.get(key))

        for label, key in [
            ("Website", "website_url"), ("Careers", "careers_url"), ("LinkedIn", "linkedin_url"),
        ]:
            if company.get(key):
                view.add_field_row(label, company[key])

        view.add_text_block("Why You Fit", company.get("why_you_fit") or "")
        view.add_text_block("Notes", company.get("notes") or "")

        # Related job postings
        postings = self.db.get_job_postings_for_company(company_id)
        if postings:
            view.add_section_header(f"Job Postings ({len(postings)})")
            for jp in postings:
                row = ttk.Frame(view.content)
                row.pack(fill="x", padx=15, pady=2)
                lbl = ttk.Label(row, text=jp["job_title"], foreground="#4f46e5", cursor="hand2", font=("", 10, "underline"))
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, pid=jp["id"]: self._show_jp_detail(pid))
                ttk.Label(row, text=jp.get("apply_status") or "", foreground="gray").pack(side="right")

        # Related contacts
        contacts = self.db.get_contacts_for_company(company_id)
        if contacts:
            view.add_section_header(f"Contacts ({len(contacts)})")
            for ct in contacts:
                row = ttk.Frame(view.content)
                row.pack(fill="x", padx=15, pady=2)
                lbl = ttk.Label(row, text=ct["full_name"], foreground="#4f46e5", cursor="hand2", font=("", 10, "underline"))
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, cid=ct["id"]: self._show_contact_detail(cid))
                ttk.Label(row, text=ct.get("priority") or "", foreground="gray").pack(side="right")

    # ── Job Postings ─────────────────────────────────────────────────

    def _show_job_postings(self) -> None:
        table = DataTableView(
            self.content,
            columns=[
                ("job_title", "Job Title", 180), ("company_name", "Company", 140),
                ("role_type", "Type", 90), ("location", "Location", 120),
                ("apply_status", "Apply Status", 100), ("do_you_qualify", "Qualify?", 80),
            ],
            on_select=lambda rid: self._show_jp_detail(rid),
            on_add=self._add_job_posting,
            on_delete=lambda ids: (self.db.delete_job_postings(ids), self._show_job_postings()),
            on_export=lambda: self._export_table("job_postings"),
            status_options=APPLY_STATUSES,
            title="Job Postings",
            subtitle="Track job opportunities and application status.",
        )
        self._switch_view(table)
        table.load_data(self.db.get_job_postings(), status_key="apply_status")

    def _add_job_posting(self, data: Optional[dict[str, Any]] = None, edit_id: str = "") -> None:
        dlg = FormDialog(self.root, "Edit Job Posting" if edit_id else "Add Job Posting", height=700)
        dlg.add_field("job_title", "Job Title", required=True)
        company_names = self.db.get_company_names()
        comp_map = {c["company_name"]: c["id"] for c in company_names}
        dlg.add_field("company_id", "Company", widget_type="combo", values=list(comp_map.keys()))
        dlg.add_field("role_type", "Role Type", widget_type="combo", values=ROLE_TYPES)
        dlg.add_field("date_found", "Date Found (YYYY-MM-DD)")
        dlg.add_field("location", "Location")
        dlg.add_field("salary_range", "Salary Range")
        dlg.add_field("job_post_url", "Job Post URL")
        dlg.add_field("required_technical_skills", "Required Technical Skills", widget_type="text")
        dlg.add_field("platform_tool_mentioned", "Platform/Tool Mentioned")
        dlg.add_field("preferred_skills", "Preferred Skills", widget_type="text")
        dlg.add_field("soft_skills_emphasized", "Soft Skills Emphasized")
        dlg.add_field("interesting_keywords", "Interesting Keywords")
        dlg.add_field("do_you_qualify", "Do You Qualify?", widget_type="combo", values=QUALIFY_OPTIONS)
        dlg.add_field("gaps_identified", "Gaps Identified", widget_type="text")
        dlg.add_field("apply_status", "Apply Status", widget_type="combo", values=APPLY_STATUSES)
        dlg.add_field("notes", "Notes", widget_type="text")

        if data:
            # Convert company_id to company_name for the combo
            if data.get("company_id"):
                for c in company_names:
                    if c["id"] == data["company_id"]:
                        data = {**data, "company_id": c["company_name"]}
                        break
            dlg.set_data(data)

        def on_save() -> None:
            form = dlg.get_data()
            if not form.get("job_title"):
                messagebox.showwarning("Validation", "Job title is required.")
                return
            # Convert company name back to ID
            form["company_id"] = comp_map.get(form.get("company_id", ""), "")
            if edit_id:
                self.db.update_job_posting(edit_id, form)
            else:
                self.db.create_job_posting(form)
            dlg.destroy()
            self._show_job_postings()

        dlg.save_btn.config(command=on_save)

    def _show_jp_detail(self, post_id: str) -> None:
        jp = self.db.get_job_posting(post_id)
        if not jp:
            return
        view = DetailView(self.content)
        self._switch_view(view)
        view.back_btn.config(command=self._show_job_postings)
        view.title_label.config(text=jp["job_title"])
        view.edit_btn.config(command=lambda: self._add_job_posting(data=jp, edit_id=post_id))
        view.delete_btn.config(command=lambda: self._delete_and_back(
            lambda: self.db.delete_job_postings([post_id]), self._show_job_postings, jp["job_title"]
        ))

        view.add_section_header("Details")
        for label, key in [
            ("Company", "company_name"), ("Role Type", "role_type"),
            ("Date Found", "date_found"), ("Location", "location"),
            ("Salary Range", "salary_range"), ("Do You Qualify?", "do_you_qualify"),
            ("Apply Status", "apply_status"),
        ]:
            view.add_field_row(label, jp.get(key))

        if jp.get("job_post_url"):
            view.add_field_row("Job Post URL", jp["job_post_url"])

        for label, key in [
            ("Required Technical Skills", "required_technical_skills"),
            ("Platform/Tool Mentioned", "platform_tool_mentioned"),
            ("Preferred Skills", "preferred_skills"),
            ("Soft Skills Emphasized", "soft_skills_emphasized"),
            ("Interesting Keywords", "interesting_keywords"),
            ("Gaps Identified", "gaps_identified"),
            ("Notes", "notes"),
        ]:
            view.add_text_block(label, jp.get(key) or "")

    # ── Contacts ─────────────────────────────────────────────────────

    def _show_contacts(self) -> None:
        table = DataTableView(
            self.content,
            columns=[
                ("full_name", "Name", 160), ("company_name", "Company", 140),
                ("title", "Title", 140), ("contact_type", "Type", 110),
                ("priority", "Priority", 70), ("connection_degree", "Degree", 70),
                ("warm_intro_available", "Warm Intro", 80),
            ],
            on_select=lambda rid: self._show_contact_detail(rid),
            on_add=self._add_contact,
            on_delete=lambda ids: (self.db.delete_contacts(ids), self._show_contacts()),
            on_export=lambda: self._export_table("contacts"),
            status_options=PRIORITIES,
            title="Contacts",
            subtitle="Manage your professional network.",
        )
        self._switch_view(table)
        table.load_data(self.db.get_contacts(), status_key="priority")

    def _add_contact(self, data: Optional[dict[str, Any]] = None, edit_id: str = "") -> None:
        dlg = FormDialog(self.root, "Edit Contact" if edit_id else "Add Contact", height=650)
        dlg.add_field("full_name", "Full Name", required=True)
        company_names = self.db.get_company_names()
        comp_map = {c["company_name"]: c["id"] for c in company_names}
        dlg.add_field("company_id", "Company", widget_type="combo", values=list(comp_map.keys()))
        dlg.add_field("title", "Title")
        dlg.add_field("contact_type", "Contact Type", widget_type="combo", values=CONTACT_TYPES)
        dlg.add_field("priority", "Priority", widget_type="combo", values=PRIORITIES)
        dlg.add_field("email", "Email")
        dlg.add_field("linkedin_url", "LinkedIn URL")
        dlg.add_field("connection_degree", "Connection Degree", widget_type="combo", values=CONNECTION_DEGREES)
        dlg.add_field("warm_intro_available", "Warm Intro Available", widget_type="check")
        dlg.add_field("how_you_know_them", "How You Know Them")
        dlg.add_field("date_connected", "Date Connected (YYYY-MM-DD)")
        dlg.add_field("last_touchpoint", "Last Touchpoint (YYYY-MM-DD)")
        dlg.add_field("next_action", "Next Action")
        dlg.add_field("due_date", "Due Date (YYYY-MM-DD)")
        dlg.add_field("notes_intel", "Notes / Intel", widget_type="text")

        if data:
            if data.get("company_id"):
                for c in company_names:
                    if c["id"] == data["company_id"]:
                        data = {**data, "company_id": c["company_name"]}
                        break
            dlg.set_data(data)

        def on_save() -> None:
            form = dlg.get_data()
            if not form.get("full_name"):
                messagebox.showwarning("Validation", "Full name is required.")
                return
            form["company_id"] = comp_map.get(form.get("company_id", ""), "")
            if edit_id:
                self.db.update_contact(edit_id, form)
            else:
                self.db.create_contact(form)
            dlg.destroy()
            self._show_contacts()

        dlg.save_btn.config(command=on_save)

    def _show_contact_detail(self, contact_id: str) -> None:
        ct = self.db.get_contact(contact_id)
        if not ct:
            return
        view = DetailView(self.content)
        self._switch_view(view)
        view.back_btn.config(command=self._show_contacts)
        view.title_label.config(text=ct["full_name"])
        view.edit_btn.config(command=lambda: self._add_contact(data=ct, edit_id=contact_id))
        view.delete_btn.config(command=lambda: self._delete_and_back(
            lambda: self.db.delete_contacts([contact_id]), self._show_contacts, ct["full_name"]
        ))

        view.add_section_header("Details")
        for label, key in [
            ("Company", "company_name"), ("Title", "title"), ("Contact Type", "contact_type"),
            ("Priority", "priority"), ("Email", "email"), ("LinkedIn", "linkedin_url"),
            ("Connection Degree", "connection_degree"), ("Warm Intro", "warm_intro_available"),
            ("How You Know Them", "how_you_know_them"), ("Date Connected", "date_connected"),
            ("Last Touchpoint", "last_touchpoint"), ("Next Action", "next_action"),
            ("Due Date", "due_date"),
        ]:
            view.add_field_row(label, ct.get(key))
        view.add_text_block("Notes / Intel", ct.get("notes_intel") or "")

        # Related outreach
        outreach = self.db.get_outreach_for_contact(contact_id)
        if outreach:
            view.add_section_header(f"Outreach Log ({len(outreach)})")
            for o in outreach:
                row = ttk.Frame(view.content)
                row.pack(fill="x", padx=15, pady=2)
                lbl = ttk.Label(row, text=o["subject_purpose"], foreground="#4f46e5", cursor="hand2", font=("", 10, "underline"))
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, oid=o["id"]: self._show_outreach_detail(oid))
                ttk.Label(row, text=o.get("outcome") or "", foreground="gray").pack(side="right")

    # ── Outreach Log ─────────────────────────────────────────────────

    def _show_outreach(self) -> None:
        table = DataTableView(
            self.content,
            columns=[
                ("subject_purpose", "Subject", 180), ("contact_name", "Contact", 120),
                ("channel", "Channel", 100), ("date_sent", "Date Sent", 100),
                ("response_received", "Response?", 80), ("outcome", "Outcome", 110),
                ("follow_up_due", "Follow-Up Due", 100),
            ],
            on_select=lambda rid: self._show_outreach_detail(rid),
            on_add=self._add_outreach,
            on_delete=lambda ids: (self.db.delete_outreach(ids), self._show_outreach()),
            on_export=lambda: self._export_table("outreach_log"),
            status_options=OUTCOMES,
            title="Outreach Log",
            subtitle="Track your messages, follow-ups, and responses.",
        )
        self._switch_view(table)
        table.load_data(self.db.get_outreach(), status_key="outcome")

    def _add_outreach(self, data: Optional[dict[str, Any]] = None, edit_id: str = "") -> None:
        dlg = FormDialog(self.root, "Edit Outreach" if edit_id else "Add Outreach Entry", height=700)
        dlg.add_field("subject_purpose", "Subject / Purpose", required=True)
        contact_names = self.db.get_contact_names()
        ct_map = {c["full_name"]: c["id"] for c in contact_names}
        company_names = self.db.get_company_names()
        comp_map = {c["company_name"]: c["id"] for c in company_names}
        dlg.add_field("contact_id", "Contact", widget_type="combo", values=list(ct_map.keys()))
        dlg.add_field("company_id", "Company", widget_type="combo", values=list(comp_map.keys()))
        dlg.add_field("date_sent", "Date Sent (YYYY-MM-DD)")
        dlg.add_field("channel", "Channel", widget_type="combo", values=CHANNELS)
        dlg.add_field("message_type", "Message Type", widget_type="combo", values=MESSAGE_TYPES)
        dlg.add_field("personalization_hook", "Personalization Hook", widget_type="text")
        dlg.add_field("response_received", "Response Received", widget_type="check")
        dlg.add_field("response_date", "Response Date (YYYY-MM-DD)")
        dlg.add_field("response_summary", "Response Summary", widget_type="text")
        dlg.add_field("follow_up_due", "Follow-Up Due (YYYY-MM-DD)")
        dlg.add_field("follow_up_sent", "Follow-Up Sent", widget_type="check")
        dlg.add_field("outcome", "Outcome", widget_type="combo", values=OUTCOMES)
        dlg.add_field("notes", "Notes", widget_type="text")

        if data:
            if data.get("contact_id"):
                for c in contact_names:
                    if c["id"] == data["contact_id"]:
                        data = {**data, "contact_id": c["full_name"]}
                        break
            if data.get("company_id"):
                for c in company_names:
                    if c["id"] == data["company_id"]:
                        data = {**data, "company_id": c["company_name"]}
                        break
            dlg.set_data(data)

        def on_save() -> None:
            form = dlg.get_data()
            if not form.get("subject_purpose"):
                messagebox.showwarning("Validation", "Subject/Purpose is required.")
                return
            form["contact_id"] = ct_map.get(form.get("contact_id", ""), "")
            form["company_id"] = comp_map.get(form.get("company_id", ""), "")
            if edit_id:
                self.db.update_outreach(edit_id, form)
            else:
                self.db.create_outreach(form)
            dlg.destroy()
            self._show_outreach()

        dlg.save_btn.config(command=on_save)

    def _show_outreach_detail(self, entry_id: str) -> None:
        o = self.db.get_outreach_entry(entry_id)
        if not o:
            return
        view = DetailView(self.content)
        self._switch_view(view)
        view.back_btn.config(command=self._show_outreach)
        view.title_label.config(text=o["subject_purpose"])
        view.edit_btn.config(command=lambda: self._add_outreach(data=o, edit_id=entry_id))
        view.delete_btn.config(command=lambda: self._delete_and_back(
            lambda: self.db.delete_outreach([entry_id]), self._show_outreach, o["subject_purpose"]
        ))

        view.add_section_header("Details")
        for label, key in [
            ("Contact", "contact_name"), ("Company", "company_name"),
            ("Date Sent", "date_sent"), ("Channel", "channel"),
            ("Message Type", "message_type"), ("Response Received", "response_received"),
            ("Response Date", "response_date"), ("Follow-Up Due", "follow_up_due"),
            ("Follow-Up Sent", "follow_up_sent"), ("Outcome", "outcome"),
        ]:
            view.add_field_row(label, o.get(key))
        for label, key in [
            ("Personalization Hook", "personalization_hook"),
            ("Response Summary", "response_summary"),
            ("Notes", "notes"),
        ]:
            view.add_text_block(label, o.get(key) or "")

    # ── Gap Analysis ─────────────────────────────────────────────────

    def _show_gap_analysis(self) -> None:
        frame = ttk.Frame(self.content)
        self._switch_view(frame)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        profile = self.db.get_or_create_profile()
        profile_id = profile["id"]

        # Title bar
        title_bar = ttk.Frame(frame)
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 10))
        ttk.Label(title_bar, text="Gap Analysis", font=("", 20, "bold")).pack(side="left")
        ttk.Button(title_bar, text="Export Markdown", command=lambda: self._export_gap_md(profile_id)).pack(side="right")

        # Left panel — Profile
        left = ttk.LabelFrame(frame, text="🎯 Job Seeker Profile", padding=10)
        left.grid(row=1, column=0, sticky="nsew", padx=(15, 5), pady=(0, 15))

        profile_fields: dict[str, FormField] = {}
        for key, label, wtype in [
            ("target_role", "Target Role", "entry"),
            ("target_salary_min", "Target Salary Min ($K)", "entry"),
            ("target_salary_max", "Target Salary Max ($K)", "entry"),
            ("target_location", "Target Location", "entry"),
            ("relocation_date", "Relocation Date (YYYY-MM-DD)", "entry"),
            ("work_authorization", "Work Authorization", "entry"),
            ("summary", "Summary / Bio", "text"),
        ]:
            f = FormField(left, label, widget_type=wtype, height=4)
            f.pack(fill="x", pady=2)
            f.set(profile.get(key) or "")
            profile_fields[key] = f

        def save_profile() -> None:
            data = {k: f.get() for k, f in profile_fields.items()}
            # Convert salary fields to int or None
            for sk in ("target_salary_min", "target_salary_max"):
                try:
                    data[sk] = int(data[sk]) if data[sk] else None
                except ValueError:
                    data[sk] = None
            self.db.update_profile(profile_id, data)
            messagebox.showinfo("Saved", "Profile saved.")

        ttk.Button(left, text="Save Profile", style="primary.TButton", command=save_profile).pack(pady=(10, 0))

        # Right panel — Strengths & Gaps
        right_container = ttk.Frame(frame)
        right_container.grid(row=1, column=1, sticky="nsew", padx=(5, 15), pady=(0, 15))
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(0, weight=1)

        # Canvas for scrolling
        r_canvas = tk.Canvas(right_container, highlightthickness=0)
        r_scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=r_canvas.yview)
        right = ttk.Frame(r_canvas)
        right.bind("<Configure>", lambda e: r_canvas.configure(scrollregion=r_canvas.bbox("all")))
        r_canvas.create_window((0, 0), window=right, anchor="nw", tags="rw")
        r_canvas.bind("<Configure>", lambda e: r_canvas.itemconfig("rw", width=e.width))
        r_canvas.configure(yscrollcommand=r_scrollbar.set)
        r_canvas.grid(row=0, column=0, sticky="nsew")
        r_scrollbar.grid(row=0, column=1, sticky="ns")

        def _scroll_right(event: tk.Event) -> None:
            r_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        r_canvas.bind("<MouseWheel>", _scroll_right)

        # Strengths section
        str_header = ttk.Frame(right)
        str_header.pack(fill="x", padx=5, pady=(5, 5))
        ttk.Label(str_header, text="💪 Strengths", font=("", 14, "bold")).pack(side="left")

        strengths_container = ttk.Frame(right)
        strengths_container.pack(fill="x", padx=5)

        def refresh_strengths() -> None:
            for w in strengths_container.winfo_children():
                w.destroy()
            for s in self.db.get_strengths(profile_id):
                card = ttk.LabelFrame(strengths_container, padding=8)
                card.pack(fill="x", pady=3)
                s_var = tk.StringVar(value=s["strength"])
                tp_var = tk.StringVar(value=s.get("talking_point") or "")
                ttk.Entry(card, textvariable=s_var, width=40, font=("", 10, "bold")).pack(fill="x")
                ttk.Entry(card, textvariable=tp_var, width=40).pack(fill="x", pady=(2, 0))
                btn_row = ttk.Frame(card)
                btn_row.pack(fill="x", pady=(4, 0))
                ttk.Button(btn_row, text="Save", command=lambda sid=s["id"], sv=s_var, tv=tp_var: (
                    self.db.update_strength(sid, {"strength": sv.get(), "talking_point": tv.get()}),
                )).pack(side="left")
                ttk.Button(btn_row, text="Delete", style="danger.Outline.TButton",
                           command=lambda sid=s["id"]: (self.db.delete_strength(sid), refresh_strengths())).pack(side="right")

        refresh_strengths()
        ttk.Button(str_header, text="+ Add", command=lambda: (
            self.db.create_strength(profile_id, sort_order=len(self.db.get_strengths(profile_id))),
            refresh_strengths(),
        )).pack(side="right")

        ttk.Separator(right).pack(fill="x", padx=5, pady=10)

        # Gaps section
        gap_header = ttk.Frame(right)
        gap_header.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Label(gap_header, text="⚠️ Gaps & Objections", font=("", 14, "bold")).pack(side="left")

        gaps_container = ttk.Frame(right)
        gaps_container.pack(fill="x", padx=5)

        def refresh_gaps() -> None:
            for w in gaps_container.winfo_children():
                w.destroy()
            for g in self.db.get_gaps(profile_id):
                card = ttk.LabelFrame(gaps_container, padding=8)
                card.pack(fill="x", pady=3)
                o_var = tk.StringVar(value=g["objection"])
                r_var = tk.StringVar(value=g.get("rebuttal") or "")
                m_var = tk.StringVar(value=g.get("mitigation") or "")
                ttk.Label(card, text="Objection:", font=("", 8), foreground="gray").pack(anchor="w")
                ttk.Entry(card, textvariable=o_var, width=40, font=("", 10, "bold")).pack(fill="x")
                ttk.Label(card, text="Rebuttal:", font=("", 8), foreground="gray").pack(anchor="w", pady=(4, 0))
                ttk.Entry(card, textvariable=r_var, width=40).pack(fill="x")
                ttk.Label(card, text="Mitigation:", font=("", 8), foreground="gray").pack(anchor="w", pady=(4, 0))
                ttk.Entry(card, textvariable=m_var, width=40).pack(fill="x")
                btn_row = ttk.Frame(card)
                btn_row.pack(fill="x", pady=(4, 0))
                ttk.Button(btn_row, text="Save", command=lambda gid=g["id"], ov=o_var, rv=r_var, mv=m_var: (
                    self.db.update_gap(gid, {"objection": ov.get(), "rebuttal": rv.get(), "mitigation": mv.get()}),
                )).pack(side="left")
                ttk.Button(btn_row, text="Delete", style="danger.Outline.TButton",
                           command=lambda gid=g["id"]: (self.db.delete_gap(gid), refresh_gaps())).pack(side="right")

        refresh_gaps()
        ttk.Button(gap_header, text="+ Add", command=lambda: (
            self.db.create_gap(profile_id, sort_order=len(self.db.get_gaps(profile_id))),
            refresh_gaps(),
        )).pack(side="right")

    # ── Settings ─────────────────────────────────────────────────────

    def _show_settings(self) -> None:
        frame = ttk.Frame(self.content)
        self._switch_view(frame)

        ttk.Label(frame, text="Settings", font=("", 20, "bold")).pack(
            anchor="w", padx=15, pady=(15, 5)
        )

        # User name
        name_frame = ttk.LabelFrame(frame, text="Profile", padding=15)
        name_frame.pack(fill="x", padx=15, pady=10)
        name_var = tk.StringVar(value=self.db.get_setting("full_name"))
        ttk.Label(name_frame, text="Full Name:").pack(anchor="w")
        ttk.Entry(name_frame, textvariable=name_var, width=40).pack(fill="x", pady=(2, 8))
        ttk.Button(name_frame, text="Save", style="primary.TButton", command=lambda: (
            self.db.set_setting("full_name", name_var.get()),
            messagebox.showinfo("Saved", "Name saved."),
        )).pack(anchor="w")

        # Data section
        data_frame = ttk.LabelFrame(frame, text="Data", padding=15)
        data_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(data_frame, text=f"Database: {self.db.db_path}", foreground="gray", wraplength=400).pack(anchor="w", pady=(0, 10))

        btn_row = ttk.Frame(data_frame)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Export All CSV", command=self._export_all_csv).pack(side="left", padx=(0, 5))
        ttk.Button(btn_row, text="Export Gap Analysis (MD)", command=lambda: self._export_gap_md(
            self.db.get_or_create_profile()["id"]
        )).pack(side="left", padx=5)

        ttk.Separator(data_frame).pack(fill="x", pady=15)
        ttk.Button(data_frame, text="Delete All Data", style="danger.TButton", command=self._delete_all_data).pack(anchor="w")

        # About
        about_frame = ttk.LabelFrame(frame, text="About", padding=15)
        about_frame.pack(fill="x", padx=15, pady=10)
        ttk.Label(about_frame, text="JobTrackr v1.0.0").pack(anchor="w")
        ttk.Label(about_frame, text="A standalone job-search CRM.", foreground="gray").pack(anchor="w")

    # ── Helpers ──────────────────────────────────────────────────────

    def _delete_and_back(self, delete_fn: Any, back_fn: Any, name: str) -> None:
        if messagebox.askyesno("Confirm Delete", f"Permanently delete \"{name}\"?"):
            delete_fn()
            back_fn()

    def _export_table(self, table: str) -> None:
        rows = self.db.get_all_rows(table)
        if not rows:
            messagebox.showinfo("Export", "No data to export.")
            return
        csv_text = generate_csv(rows)
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            initialfile=f"{table}.csv",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(csv_text)
            messagebox.showinfo("Export", f"Exported to {path}")

    def _export_all_csv(self) -> None:
        folder = filedialog.askdirectory(title="Select folder for export")
        if not folder:
            return
        for table in ("companies", "job_postings", "contacts", "outreach_log"):
            rows = self.db.get_all_rows(table)
            if rows:
                csv_text = generate_csv(rows)
                path = f"{folder}/{table}.csv"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
        messagebox.showinfo("Export", f"All tables exported to {folder}")

    def _export_gap_md(self, profile_id: str) -> None:
        profile = self.db.get_or_create_profile()
        strengths = self.db.get_strengths(profile_id)
        gaps = self.db.get_gaps(profile_id)
        full_name = self.db.get_setting("full_name")
        md = generate_gap_analysis_markdown(profile, strengths, gaps, full_name)
        path = filedialog.asksaveasfilename(
            defaultextension=".md", filetypes=[("Markdown", "*.md")],
            initialfile="gap-analysis.md",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            messagebox.showinfo("Export", f"Exported to {path}")

    def _delete_all_data(self) -> None:
        if not messagebox.askyesno(
            "Delete All Data",
            "This will permanently delete ALL your data. This cannot be undone.\n\nAre you sure?",
        ):
            return
        for table in ("outreach_log", "contacts", "job_postings", "companies", "gaps", "strengths", "job_seeker_profile", "settings"):
            self.db.conn.execute(f"DELETE FROM {table}")
        self.db.conn.commit()
        messagebox.showinfo("Deleted", "All data has been deleted.")
        self._show_dashboard()
