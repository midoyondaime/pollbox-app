# OVERVIEW
# Image of the pollbox API. Built by CI and pushed to Docker Hub.
# Listens on port 8000.

# Start from a small official Python image (3.12, "slim" variant).
FROM python:3.12-slim

# Work inside /app in the image; later paths are relative to it.
WORKDIR /app

# Copy only the dependency list first, so this layer is cached when only code changes.
COPY requirements.txt .

# Install the dependencies; --no-cache-dir keeps the image smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY main.py .

# Document that the app listens on port 8000 (it does not publish it by itself).
EXPOSE 8000

# Start the server; 0.0.0.0 makes it reachable from outside the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
