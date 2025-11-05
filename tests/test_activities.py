from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict before each test."""
    original = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


client = TestClient(app_module.app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect known activity names present
    assert "Chess Club" in data


def test_signup_and_duplicate():
    activity = "Basketball Team"
    email = "tester@example.com"

    # Ensure starting empty
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    resp = client.post(url)
    assert resp.status_code == 200
    assert f"Signed up {email}" in resp.json().get("message", "")

    # Duplicate signup should fail
    resp = client.post(url)
    assert resp.status_code == 400
    assert "already signed up" in resp.json().get("detail", "")


def test_unregister_and_not_found():
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Precondition: michael is in Chess Club (see app.py)
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email in resp.json()[activity]["participants"]

    # Unregister
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    resp = client.delete(url)
    assert resp.status_code == 200
    assert f"Removed {email}" in resp.json().get("message", "")

    # Unregister again should return 404
    resp = client.delete(url)
    assert resp.status_code == 404
    assert "Participant not found" in resp.json().get("detail", "")
