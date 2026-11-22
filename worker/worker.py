# OVERVIEW
# The pollbox worker.
# It waits for votes in the Redis list "votes", takes the oldest one, and inserts
# one row into the Postgres table "votes". It never talks to the API.
# Configuration comes from environment variables (DB_HOST, POSTGRES_DB,
# POSTGRES_USER, POSTGRES_PASSWORD, REDIS_HOST).

# Standard library: read environment variables.
import os
# Standard library: wait a moment after an error.
import time
# Standard library: turn JSON text back into a dictionary.
import json

# The PostgreSQL driver.
import psycopg2
# The Redis client.
import redis


# Open a new connection to Postgres using the environment variables.
def get_conn():
    # Return the connection object.
    return psycopg2.connect(
        # Host name of the database.
        host=os.environ["DB_HOST"],
        # Database name.
        dbname=os.environ["POSTGRES_DB"],
        # Database user.
        user=os.environ["POSTGRES_USER"],
        # Database password.
        password=os.environ["POSTGRES_PASSWORD"],
    )


# The worker's main loop.
def main():
    # Connect to Redis (6379 is its default port).
    r = redis.Redis(host=os.environ["REDIS_HOST"], port=6379)
    # flush=True makes the line appear in the container logs immediately.
    print("worker started, waiting for votes", flush=True)
    # Run forever.
    while True:
        # Wait up to 5 seconds for an item at the right end of the list "votes" (BRPOP = blocking pop).
        item = r.brpop("votes", timeout=5)
        # Nothing arrived within 5 seconds: go back to waiting.
        if item is None:
            # Skip the rest of the loop body.
            continue
        # BRPOP returns (list name, value); we only need the value, the raw JSON text.
        _, raw = item
        # Try to store the vote; any failure is reported but does not stop the worker.
        try:
            # Turn the JSON text into a dictionary, e.g. {"option_id": 1}.
            vote = json.loads(raw)
            # Open a database connection (one per vote: simple, and it survives a database restart).
            conn = get_conn()
            # Always close it at the end.
            try:
                # "with conn": one transaction, committed at the end or rolled back on error.
                with conn:
                    # A cursor sends SQL to the database.
                    with conn.cursor() as cur:
                        # Insert one vote row; %s is a placeholder, the value is sent separately.
                        cur.execute("INSERT INTO votes (option_id) VALUES (%s)", (vote["option_id"],))
            # Release the connection.
            finally:
                conn.close()
            # Log the success.
            print("vote stored for option", vote["option_id"], flush=True)
        # Something went wrong (bad JSON, database down, unknown option...).
        except Exception as exc:
            # Log it with the raw vote, so it can be investigated.
            print("could not store vote", raw, exc, flush=True)
            # Wait a second before the next attempt, so an outage doesn't spin the CPU.
            time.sleep(1)


# Run main() only when this file is started directly (not when imported).
if __name__ == "__main__":
    # Start the loop.
    main()
