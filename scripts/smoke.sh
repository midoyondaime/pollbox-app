#!/usr/bin/env bash
# smoke.sh: walks the whole vote journey through nginx
# (nginx -> api -> redis -> worker -> postgres).
# Exits non-zero at the first failure, so a pipeline stops there.
set -euo pipefail

# through nginx, exactly like a browser
BASE="${BASE:-http://127.0.0.1:8080/api}"

# read one value from JSON on stdin; $1 is a python expression on d
field() { python3 -c "import sys,json; d=json.load(sys.stdin); print($1)"; }

echo "1. health through nginx"
# -f makes curl fail on an HTTP error, -s hides the progress bar
curl -fsS "$BASE/health" >"/dev/null"

echo "2. create a poll"
POLL=$(curl -fsS -X POST "$BASE/polls" -H 'Content-Type: application/json' \
  -d '{"question":"smoke test","options":["a","b"]}')
ID=$(echo "$POLL" | field 'd["id"]')

echo "3. read it and take the id of the first option"
OPT=$(curl -fsS "$BASE/polls/$ID" | field 'd["options"][0]["id"]')

echo "4. vote (the api answers 202: accepted, not yet counted)"
curl -fsS -X POST "$BASE/polls/$ID/vote" -H 'Content-Type: application/json' \
  -d "{\"option_id\": $OPT}" >/dev/null

echo "5. wait for the worker to store it (eventual consistency)"
for i in $(seq 1 15); do
  N=$(curl -fsS "$BASE/polls/$ID" | field 'd["options"][0]["votes"]')
  if [ "$N" = "1" ]; then echo "OK: vote counted after ${i}s"; exit 0; fi
  sleep 1
done
echo "FAIL: vote not counted after 15s" >&2
exit 1
