# Dockerfile
#
# SDK development and test container.
#
# Build:  docker build -t ha_mqtt_sdk .
# Test:   docker run ha_mqtt_sdk
# Shell:  docker run -it ha_mqtt_sdk bash

FROM python:3.13-slim

# Metadata
LABEL maintainer="Dick Kouwenhoven"
LABEL description="HA-MQTT-SDK development and test container"

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN adduser --disabled-password --gecos "" sdkuser

# ── Install dependencies ───────────────────────────────────────────────────────
#
# Copy only the files needed to resolve dependencies first.
# This layer is cached until pyproject.toml or requirements-dev.txt changes,
# so rebuilds after editing source code are fast.

COPY pyproject.toml .
COPY README.md .

# Install package in editable mode with dev dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# ── Copy source ───────────────────────────────────────────────────────────────

COPY src/ src/
COPY tests/ tests/

# Switch to non-root user
USER sdkuser

# ── Default command: run full test suite ──────────────────────────────────────

CMD ["pytest", "--cov=ha_mqtt_sdk", "--cov-report=term-missing", "--cov-fail-under=100", "-v"]
