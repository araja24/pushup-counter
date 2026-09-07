"""The same origin serves the page and the API, so `/` has to behave for both."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from pushform.static_site import mount_frontend


@pytest.fixture
def built_dist(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<h1>PushForm</h1>", encoding="utf-8")
    (dist / "app.js").write_text("// built bundle", encoding="utf-8")
    return dist


def client_for(dist) -> TestClient:
    app = FastAPI()
    mount_frontend(app, dist)
    return TestClient(app)


def test_serves_the_build_at_the_root(built_dist):
    response = client_for(built_dist).get("/")

    assert response.status_code == 200
    assert "PushForm" in response.text


def test_serves_built_assets(built_dist):
    response = client_for(built_dist).get("/app.js")

    assert response.status_code == 200
    assert response.text == "// built bundle"


def test_unknown_paths_fall_back_to_the_app_so_refresh_works(built_dist):
    """A phone refreshing on a client-side route must get the app, not a 404."""
    response = client_for(built_dist).get("/set/42")

    assert response.status_code == 200
    assert "PushForm" in response.text


def test_serves_a_placeholder_when_the_frontend_has_not_been_built(tmp_path):
    response = client_for(tmp_path / "never-built").get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PushForm" in response.text
    assert "npm run build" in response.text


def test_unknown_api_paths_still_report_not_found(built_dist):
    """An API typo must fail loudly, not quietly return the page as 200 HTML."""
    response = client_for(built_dist).get("/api/nope")

    assert response.status_code == 404
