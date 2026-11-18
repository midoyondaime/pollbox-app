# OVERVIEW
# The pollbox API.
# Endpoints so far:
#   GET /health  -> "ok" if the process is alive (never touches the database)
#   GET /ready   -> "ready" if the database answers, else HTTP 503
# At startup the API runs schema.sql so the tables exist.
# The database location comes from environment variables, nothing is hardcoded.

# Standard library: read environment variables.
import os
# Standard library: build the path to schema.sql next to this file.
from pathlib import Path
# Standard library: helper to run code at startup (and shutdown).
from contextlib import asynccontextmanager

# The PostgreSQL driver.
import psycopg2
# FastAPI: the app class, and an exception that turns into an HTTP error.
from fastapi import FastAPI, HTTPException


# Open a new connection to Postgres using the environment variables.
def get_conn():
    # Return the connection object.
    return psycopg2.connect(
        # Host name of the database (the service name in compose, a Service in Kubernetes).
        host=os.environ["DB_HOST"],
        # Database name.
        dbname=os.environ["POSTGRES_DB"],
        # Database user.
        user=os.environ["POSTGRES_USER"],
        # Database password.
        password=os.environ["POSTGRES_PASSWORD"],
    )


# Create the tables if they don't exist yet.
def init_db():
    # Read the SQL text of schema.sql, which sits in the same folder as this file.
    schema = (Path(__file__).parent / "schema.sql").read_text()
    # Open a connection.
    conn = get_conn()
    # Always close it at the end, even if something fails.
    try:
        # "with conn" commits the transaction if no error occurred.
        with conn:
            # A cursor sends SQL to the database.
            with conn.cursor() as cur:
                # Run the whole schema (safe to repeat, thanks to IF NOT EXISTS).
                cur.execute(schema)
    finally:
        # Release the connection.
        conn.close()


# Code that runs once when the API starts (before the "yield") and when it stops.
@asynccontextmanager
async def lifespan(app):
    # Make sure the tables exist before serving requests.
    init_db()
    # The API serves requests while execution is paused here.
    yield


# Create the application and attach the startup code.
app = FastAPI(lifespan=lifespan)


# Register the function below as the handler for GET /health.
@app.get("/health")
# Liveness: no database call on purpose.
def health():
    # FastAPI turns the dictionary into JSON.
    return {"status": "ok"}


# Register the function below as the handler for GET /ready.
@app.get("/ready")
# Readiness: only OK if the database answers.
def ready():
    # Try to talk to the database.
    try:
        # Open a connection.
        conn = get_conn()
        # Always close it at the end.
        try:
            # A cursor sends SQL to the database.
            with conn.cursor() as cur:
                # The simplest possible query: "are you there?".
                cur.execute("SELECT 1")
        finally:
            # Release the connection.
            conn.close()
    # Any failure (host unknown, wrong password, database down)...
    except Exception:
        # ...becomes HTTP 503 "service unavailable".
        raise HTTPException(status_code=503, detail="database not reachable")
    # Everything worked.
    return {"status": "ready"}
