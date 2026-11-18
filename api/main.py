# OVERVIEW
# This is the pollbox API. For now it has one endpoint, /health,
# which answers "ok" if the service is running.
# Kubernetes probes and CI smoke tests will call it later.

# Import the FastAPI class, the web framework we use.
from fastapi import FastAPI

# Create the application object. uvicorn will run this object.
app = FastAPI()


# Register the function below as the handler for GET /health.
@app.get("/health")
# Define the handler. It takes no input.
def health():
    # Return a dictionary; FastAPI turns it into JSON: {"status": "ok"}.
    return {"status": "ok"}
