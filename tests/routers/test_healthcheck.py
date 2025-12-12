from fastapi.testclient import TestClient

from geospatial_api.main import app

client = TestClient(app)


class TestHealthCheck:
    def test_read_healthcheck(self) -> None:
        """Test the read_healthcheck function returns the expected response."""
        response = client.get("/api/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
