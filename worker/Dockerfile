# worker/Dockerfile - image for the vote worker (no web server, no port).
# A comment must be on its own line in a Dockerfile.

# same base image as the API: already on your machine
FROM python:3.12-slim
# working folder inside the image
WORKDIR /app
# copy the dependency list first, so this layer is cached until requirements change
COPY requirements.txt .
# install psycopg2-binary and redis
RUN pip install --no-cache-dir -r requirements.txt
# then the code (it changes more often, so it comes last)
COPY worker.py .
# -u: unbuffered output, so the logs appear immediately in docker logs
CMD ["python", "-u", "worker.py"]
