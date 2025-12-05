# Dockerfile for FrankenAgent Lab Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies (no dev dependencies for production)
RUN poetry config virtualenvs.create false \
    && poetry install --without dev --no-interaction --no-ansi --no-root

# Copy application code
COPY frankenagent ./frankenagent
COPY alembic ./alembic
COPY alembic.ini ./
COPY blueprints ./blueprints

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Run application with uvicorn
CMD ["uvicorn", "frankenagent.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
