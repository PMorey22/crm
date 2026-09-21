from fastapi.testclient import TestClient

from poc20.database import Base, engine
from poc20.main import app


Base.metadata.create_all(
    bind=engine
)

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get(
        "/api/poc20/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert (
        data["service"]
        == "real-estate-crm-agent"
    )


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"
    assert data["version"] == "2.0.0"