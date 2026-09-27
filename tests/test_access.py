"""Access rules: who can see, save, and administer what.

Real sign-in needs the Auth0 credentials, so these tests run the app with a
stand-in for st.user and dummy [auth] secrets. Pages are selected through
AppTest's private _page_hash (a hash of the page's url_path), because
AppTest.switch_page only resolves file-based pages.

Run with: python -m pytest tests
"""

import sqlite3
from pathlib import Path

import pytest
import streamlit
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash

from engine.data_store import SkillUpStore

APP = str(Path(__file__).resolve().parents[1] / "app.py")
DB = str(Path(__file__).resolve().parents[1] / "skillupindia.db")

ADMIN = {"sub": "test|admin", "email": "admin@example.test", "email_verified": True, "name": "Ada Admin"}
MEMBER = {"sub": "test|member", "email": "member@example.test", "email_verified": True, "name": "Max Member"}
# Same email as the admin, but unverified: must NOT be treated as admin.
SPOOF = {"sub": "test|spoof", "email": "admin@example.test", "email_verified": False, "name": "Sam Spoof"}


class FakeUser:
    """Mimics the parts of st.user the app reads."""

    def __init__(self, claims):
        self._claims = claims or {}

    @property
    def is_logged_in(self):
        return bool(self._claims)

    def get(self, key, default=None):
        return self._claims.get(key, default)


@pytest.fixture
def seeded_profiles():
    store = SkillUpStore(DB)
    ids = {
        "admin": store.add_student(ADMIN["sub"], ADMIN["email"], "Test Admin Profile", "Data Analyst", ["SQL"]),
        "member": store.add_student(MEMBER["sub"], MEMBER["email"], "Test Member Profile", "Data Engineer", ["ETL"]),
    }
    yield ids
    with sqlite3.connect(DB) as c:
        c.execute("DELETE FROM progress WHERE student_id IN (SELECT id FROM students WHERE owner_id LIKE 'test|%')")
        c.execute("DELETE FROM students WHERE owner_id LIKE 'test|%'")


def run_app(monkeypatch, claims, url_path=None, auth=True):
    monkeypatch.setattr(streamlit, "user", FakeUser(claims))
    at = AppTest.from_file(APP, default_timeout=60)
    if auth:
        at.secrets["auth"] = {
            "redirect_uri": "http://localhost:8501/oauth2callback",
            "cookie_secret": "test-only",
            "client_id": "test",
            "client_secret": "test",
            "server_metadata_url": "https://example.test/.well-known/openid-configuration",
        }
        at.secrets["access"] = {"admins": ["Admin@Example.test"]}
    at.run()
    if url_path:
        at._page_hash = calc_hash(url_path)
        at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def headers(at):
    return [h.value for h in at.header]


def texts(at):
    return " ".join(m.value for m in at.markdown) + " " + " ".join(c.value for c in at.caption)


def expander_labels(at):
    # AppTest reports an expander that has an icon as a Status element.
    return [e.label for e in list(at.expander) + list(at.status)]


@pytest.mark.parametrize("claims", [None, MEMBER, SPOOF])
def test_admin_pages_are_not_reachable_by_non_admins(monkeypatch, claims):
    for url_path, header in [("data-ingestion", "Live data ingestion"), ("curriculum-upload", "Curriculum upload")]:
        assert header not in headers(run_app(monkeypatch, claims, url_path))


def test_admin_pages_are_reachable_by_a_verified_admin(monkeypatch):
    assert "Live data ingestion" in headers(run_app(monkeypatch, ADMIN, "data-ingestion"))
    assert "Curriculum upload" in headers(run_app(monkeypatch, ADMIN, "curriculum-upload"))


def test_signed_out_visitors_get_a_sign_in_prompt_instead_of_progress(monkeypatch):
    at = run_app(monkeypatch, None, "progress-tracking")
    assert "Sign in to track progress" in texts(at)
    assert not at.selectbox


def test_members_see_only_their_own_profiles(monkeypatch, seeded_profiles):
    options = run_app(monkeypatch, MEMBER, "progress-tracking").selectbox[0].options
    assert any("Test Member Profile" in o for o in options)
    assert not any("Test Admin Profile" in o for o in options)


def test_admins_see_every_profile_with_its_owner(monkeypatch, seeded_profiles):
    options = run_app(monkeypatch, ADMIN, "progress-tracking").selectbox[0].options
    assert any("Test Member Profile" in o and "member@example.test" in o for o in options)
    assert any("Test Admin Profile" in o for o in options)


def test_feedback_needs_sign_in_and_only_admins_see_the_inbox(monkeypatch):
    assert "Sign in to send feedback" in texts(run_app(monkeypatch, None, "feedback"))
    member = run_app(monkeypatch, MEMBER, "feedback")
    assert member.text_area and not any("Feedback inbox" in label for label in expander_labels(member))
    admin = run_app(monkeypatch, ADMIN, "feedback")
    assert any("Feedback inbox" in label for label in expander_labels(admin))


def test_signed_out_visitors_can_still_preview_readiness(monkeypatch):
    at = run_app(monkeypatch, None, "student-profile")
    assert [b.label for b in at.button if b.label == "Check readiness"]
    assert not [b.label for b in at.button if b.label == "Save profile"]


def test_without_auth_secrets_nothing_is_admin_and_saving_is_explained(monkeypatch):
    assert "Live data ingestion" not in headers(run_app(monkeypatch, ADMIN, "data-ingestion", auth=False))
    assert "isn't set up" in texts(run_app(monkeypatch, None, "student-profile", auth=False))
