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
# Pydantic: describes and validates the JSON bodies the API accepts.
from pydantic import BaseModel



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



# The JSON body expected by POST /polls.
class PollIn(BaseModel):
    # The question of the poll.
    question: str
    # The list of answers a voter can choose from.
    options: list[str]


# Register the function below as the handler for POST /polls; success answers 201 "created".
@app.post("/polls", status_code=201)
# "poll" is filled by FastAPI from the JSON body, already validated by PollIn.
def create_poll(poll: PollIn):
    # A poll needs a non-empty question and at least two options.
    if not poll.question.strip() or len(poll.options) < 2:
        # Refuse with HTTP 400 "bad request" and a readable message.
        raise HTTPException(status_code=400, detail="a poll needs a question and at least 2 options")
    # Open a connection.
    conn = get_conn()
    # Always close it at the end.
    try:
        # "with conn" commits everything together, or rolls back if an error occurs.
        with conn:
            # A cursor sends SQL to the database.
            with conn.cursor() as cur:
                # Insert the poll; %s is a placeholder, the value is sent separately (no SQL injection).
                cur.execute("INSERT INTO polls (question) VALUES (%s) RETURNING id", (poll.question,))
                # RETURNING gave us the new id; read it from the result.
                poll_id = cur.fetchone()[0]
                # One row per option, each pointing at the new poll.
                for label in poll.options:
                    # Insert one option.
                    cur.execute("INSERT INTO options (poll_id, label) VALUES (%s, %s)", (poll_id, label))
    finally:
        # Release the connection.
        conn.close()
    # Answer with what was created.
    return {"id": poll_id, "question": poll.question, "options": poll.options}


# Register the function below as the handler for GET /polls/{poll_id}.
@app.get("/polls/{poll_id}")
# poll_id comes from the URL; FastAPI converts it to an integer (HTTP 422 if it isn't one).
def get_poll(poll_id: int):
    # Open a connection.
    conn = get_conn()
    # Always close it at the end.
    try:
        # A cursor sends SQL to the database.
        with conn.cursor() as cur:
            # One row per option: its label and how many votes point at it.
            cur.execute(
                # LEFT JOIN keeps options that have no votes yet (their count is 0).
                "SELECT p.question, o.id, o.label, COUNT(v.id) "
                "FROM polls p "
                "JOIN options o ON o.poll_id = p.id "
                "LEFT JOIN votes v ON v.option_id = o.id "
                "WHERE p.id = %s "
                "GROUP BY p.question, o.id, o.label "
                "ORDER BY o.id",
                # The value of %s, passed separately from the SQL text.
                (poll_id,),
            )
            # Fetch all the result rows.
            rows = cur.fetchall()
    # Release the connection.
    finally:
        conn.close()
    # No rows means the poll doesn't exist (or has no options).
    if not rows:
        # Answer HTTP 404 "not found".
        raise HTTPException(status_code=404, detail="poll not found")
    # Build the answer: the question (same on every row) and the list of options with counts.
    return {
        # The poll id from the URL.
        "id": poll_id,
        # The question, taken from the first row.
        "question": rows[0][0],
        # One dictionary per option.
        "options": [{"id": r[1], "label": r[2], "votes": r[3]} for r in rows],
    }
