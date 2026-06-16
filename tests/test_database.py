"""Tests for the JobTrackr database layer.

Run with:  python -m unittest discover -s tests
These exercise the model layer in isolation — no GUI required — using a fresh
in-memory SQLite database per test.
"""

import unittest

from database import Database


class DatabaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # ":memory:" gives each test an isolated, schema-initialized DB.
        self.db = Database(":memory:")

    def tearDown(self) -> None:
        self.db.close()


class CompanyCrudTests(DatabaseTestCase):
    def test_create_and_get_roundtrip(self) -> None:
        cid = self.db.create_company({"company_name": "Acme", "tier": "Tier 1"})
        company = self.db.get_company(cid)
        assert company is not None
        self.assertEqual(company["company_name"], "Acme")
        self.assertEqual(company["tier"], "Tier 1")
        # Timestamps are stamped on insert.
        self.assertTrue(company["created_at"])
        self.assertEqual(company["created_at"], company["updated_at"])

    def test_empty_string_becomes_null_on_create(self) -> None:
        cid = self.db.create_company({"company_name": "Acme", "tier": "", "notes": ""})
        company = self.db.get_company(cid)
        assert company is not None
        self.assertIsNone(company["tier"])
        self.assertIsNone(company["notes"])

    def test_empty_string_becomes_null_on_update(self) -> None:
        cid = self.db.create_company({"company_name": "Acme", "tier": "Tier 1"})
        self.db.update_company(cid, {"tier": ""})
        company = self.db.get_company(cid)
        assert company is not None
        self.assertIsNone(company["tier"])

    def test_open_role_boolean_coercion(self) -> None:
        # Truthy form value -> 1, missing/falsey -> 0.
        on = self.db.create_company({"company_name": "On", "open_role": True})
        off = self.db.create_company({"company_name": "Off"})
        self.assertEqual(self._get(on)["open_role"], 1)
        self.assertEqual(self._get(off)["open_role"], 0)

        self.db.update_company(on, {"open_role": ""})  # falsey -> 0
        self.assertEqual(self._get(on)["open_role"], 0)

    def test_update_does_not_clobber_id(self) -> None:
        cid = self.db.create_company({"company_name": "Acme"})
        # An "id" key in the update payload must be ignored, not written.
        self.db.update_company(cid, {"id": "bogus", "company_name": "Acme Corp"})
        self.assertIsNotNone(self.db.get_company(cid))
        self.assertIsNone(self.db.get_company("bogus"))
        self.assertEqual(self._get(cid)["company_name"], "Acme Corp")

    def _get(self, cid: str) -> dict:
        company = self.db.get_company(cid)
        assert company is not None
        return company

    def test_bulk_delete(self) -> None:
        a = self.db.create_company({"company_name": "A"})
        b = self.db.create_company({"company_name": "B"})
        c = self.db.create_company({"company_name": "C"})
        self.db.delete_companies([a, b])
        remaining = self.db.get_companies()
        self.assertEqual([r["id"] for r in remaining], [c])

    def test_get_company_names_sorted(self) -> None:
        self.db.create_company({"company_name": "Zeta"})
        self.db.create_company({"company_name": "Alpha"})
        names = [r["company_name"] for r in self.db.get_company_names()]
        self.assertEqual(names, ["Alpha", "Zeta"])


class RelationshipTests(DatabaseTestCase):
    def test_job_posting_join_exposes_company_name(self) -> None:
        cid = self.db.create_company({"company_name": "Acme"})
        pid = self.db.create_job_posting({"job_title": "Engineer", "company_id": cid})
        jp = self.db.get_job_posting(pid)
        assert jp is not None
        self.assertEqual(jp["company_name"], "Acme")

    def test_deleting_company_sets_job_posting_fk_null(self) -> None:
        cid = self.db.create_company({"company_name": "Acme"})
        pid = self.db.create_job_posting({"job_title": "Engineer", "company_id": cid})
        self.db.delete_companies([cid])
        jp = self.db.get_job_posting(pid)
        assert jp is not None
        # ON DELETE SET NULL keeps the posting but clears the reference.
        self.assertIsNone(jp["company_id"])

    def test_get_job_postings_for_company(self) -> None:
        cid = self.db.create_company({"company_name": "Acme"})
        other = self.db.create_company({"company_name": "Other"})
        self.db.create_job_posting({"job_title": "A", "company_id": cid})
        self.db.create_job_posting({"job_title": "B", "company_id": cid})
        self.db.create_job_posting({"job_title": "C", "company_id": other})
        titles = {r["job_title"] for r in self.db.get_job_postings_for_company(cid)}
        self.assertEqual(titles, {"A", "B"})

    def test_outreach_join_exposes_contact_and_company(self) -> None:
        cid = self.db.create_company({"company_name": "Acme"})
        ct = self.db.create_contact({"full_name": "Jane Doe", "company_id": cid})
        oid = self.db.create_outreach(
            {"subject_purpose": "Intro", "contact_id": ct, "company_id": cid}
        )
        entry = self.db.get_outreach_entry(oid)
        assert entry is not None
        self.assertEqual(entry["contact_name"], "Jane Doe")
        self.assertEqual(entry["company_name"], "Acme")


class ProfileAndGapTests(DatabaseTestCase):
    def test_profile_is_singleton(self) -> None:
        first = self.db.get_or_create_profile()
        second = self.db.get_or_create_profile()
        self.assertEqual(first["id"], second["id"])

    def test_strengths_crud(self) -> None:
        pid = self.db.get_or_create_profile()["id"]
        sid = self.db.create_strength(pid, strength="Leadership", talking_point="Led a team")
        rows = self.db.get_strengths(pid)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["strength"], "Leadership")

        self.db.update_strength(sid, {"strength": "Mentorship"})
        self.assertEqual(self.db.get_strengths(pid)[0]["strength"], "Mentorship")

        self.db.delete_strength(sid)
        self.assertEqual(self.db.get_strengths(pid), [])

    def test_gaps_ordered_by_sort_order(self) -> None:
        pid = self.db.get_or_create_profile()["id"]
        self.db.create_gap(pid, objection="Second", sort_order=1)
        self.db.create_gap(pid, objection="First", sort_order=0)
        objections = [g["objection"] for g in self.db.get_gaps(pid)]
        self.assertEqual(objections, ["First", "Second"])


class DashboardQueryTests(DatabaseTestCase):
    def test_get_counts(self) -> None:
        self.db.create_company({"company_name": "A"})
        self.db.create_company({"company_name": "B"})
        cid = self.db.create_company({"company_name": "C"})
        self.db.create_contact({"full_name": "Jane", "company_id": cid})
        self.db.create_job_posting({"job_title": "Eng"})
        counts = self.db.get_counts()
        self.assertEqual(counts["companies"], 3)
        self.assertEqual(counts["contacts"], 1)
        self.assertEqual(counts["job_postings"], 1)

    def test_get_due_items_includes_past_due_and_sorts(self) -> None:
        self.db.create_company(
            {"company_name": "Soon", "next_action": "Email", "due_date": "2000-01-02"}
        )
        self.db.create_company(
            {"company_name": "Sooner", "next_action": "Call", "due_date": "2000-01-01"}
        )
        # No due_date -> must not appear.
        self.db.create_company({"company_name": "NoDue"})
        items = self.db.get_due_items()
        names = [i["name"] for i in items]
        self.assertEqual(names, ["Sooner", "Soon"])
        self.assertTrue(all(i["type"] == "Company" for i in items))

    def test_unsent_followups_surface_in_due_items(self) -> None:
        oid = self.db.create_outreach(
            {"subject_purpose": "Ping", "follow_up_due": "2000-01-01"}
        )
        self.assertIn("Ping", [i["name"] for i in self.db.get_due_items()])
        # Once marked sent, it drops off the list.
        self.db.update_outreach(oid, {"follow_up_sent": True})
        self.assertNotIn("Ping", [i["name"] for i in self.db.get_due_items()])


class SettingsTests(DatabaseTestCase):
    def test_get_setting_default(self) -> None:
        self.assertEqual(self.db.get_setting("missing", "fallback"), "fallback")

    def test_set_then_get_setting(self) -> None:
        self.db.set_setting("full_name", "Dana")
        self.assertEqual(self.db.get_setting("full_name"), "Dana")

    def test_set_setting_is_upsert(self) -> None:
        self.db.set_setting("full_name", "Dana")
        self.db.set_setting("full_name", "Dana Scully")
        self.assertEqual(self.db.get_setting("full_name"), "Dana Scully")


class BulkExportAccessTests(DatabaseTestCase):
    def test_get_all_rows_rejects_unknown_table(self) -> None:
        # Guards against arbitrary table names reaching the f-string query.
        self.assertEqual(self.db.get_all_rows("sqlite_master"), [])
        self.assertEqual(self.db.get_all_rows("companies; DROP TABLE companies"), [])

    def test_get_all_rows_returns_known_table(self) -> None:
        self.db.create_company({"company_name": "Acme"})
        rows = self.db.get_all_rows("companies")
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
