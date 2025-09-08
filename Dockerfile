# AI Agent Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for mcp-atlassian integration
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Copy requirements first for better caching
COPY requirements.txt* ./

# Install base Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi && \
    pip install --no-cache-dir python-dateutil atlassian-python-api keyring beautifulsoup4 markdownify

# Download NLTK data
RUN python -c "import nltk; \
    nltk.download('punkt', quiet=True); \
    nltk.download('stopwords', quiet=True); \
    nltk.download('wordnet', quiet=True); \
    nltk.download('averaged_perceptron_tagger', quiet=True); \
    print('NLTK data downloaded')"

# Copy application code and repository files
COPY . .

# Install the application in editable mode if pyproject.toml exists
RUN if [ -f pyproject.toml ]; then pip install --no-cache-dir -e .; fi

# Set environment variable for code repository path
ENV CODE_REPO_PATH=/app

# Create necessary directories
RUN mkdir -p cache logs data

# Set permissions
RUN chmod +x run.sh build.sh

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run directly in Docker without virtual environment
CMD ["python", "start_api.py", "--host", "0.0.0.0", "--port", "8000"]
