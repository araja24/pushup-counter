"""The health endpoint is the liveness contract Render and the phone both poll."""

from pushform.analysis.config import DEFAULT_CONFIG


def test_health_returns_the_documented_shape(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "uptime_s", "model_version"}
    assert body["status"] == "ok"
    assert isinstance(body["uptime_s"], float)
    assert body["uptime_s"] >= 0.0
    assert body["model_version"] == "none"


def test_uptime_does_not_go_backwards(client):
    first = client.get("/api/health").json()["uptime_s"]
    second = client.get("/api/health").json()["uptime_s"]

    assert second >= first


def test_health_is_documented_in_the_openapi_schema(client):
    schema = client.get("/openapi.json").json()

    health = schema["paths"]["/api/health"]["get"]
    ref = health["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    model_name = ref.rsplit("/", 1)[-1]
    properties = schema["components"]["schemas"][model_name]["properties"]
    assert set(properties) == {"status", "uptime_s", "model_version"}


def test_config_returns_the_default_phase_thresholds(client):
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json() == {"down_threshold": 95, "up_threshold": 155}


def test_config_serves_the_analysis_defaults_rather_than_its_own(client):
    response = client.get("/api/config")

    assert response.json() == {
        "down_threshold": DEFAULT_CONFIG.down_threshold_deg,
        "up_threshold": DEFAULT_CONFIG.up_threshold_deg,
    }
