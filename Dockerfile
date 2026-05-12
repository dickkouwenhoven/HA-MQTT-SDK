# SDK test container

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default command: run tests
CMD ["python", "-m", "unittest", "discover", "-s", "tests"]

