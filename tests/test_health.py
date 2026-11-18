# OVERVIEW
# Test for the /health endpoint of the pollbox API.
# CI will run this file on every push and block the release if it fails.

# TestClient lets us call the API in-process, with no real server.
from fastapi.testclient import TestClient

# Import the app object from api/main.py.
from main import app

# Create a client bound to our app.
client = TestClient(app)


# pytest runs every function whose name starts with "test_".
def test_health_returns_ok():
    # Call GET /health on the app.
    response = client.get("/health")
    # The HTTP status code must be 200 (success).
    assert response.status_code == 200
    # The JSON body must be exactly {"status": "ok"}.
    assert response.json() == {"status": "ok"}
