# AI Agent Docker Environment
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir rich>=13.7.0

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True)"

# Create necessary directories
RUN mkdir -p /app/cache /app/logs /app/data

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "from ai_agent.core.config import load_config; load_config()" || exit 1

# Default command - test configuration and exit
CMD ["python", "-c", "from ai_agent.core.config import load_config; from ai_agent.core.agent import AIAgent; config = load_config(); agent = AIAgent(config); print('✅ AI Agent Docker environment ready!'); print('To run interactive mode: docker-compose exec ai-agent python -m ai_agent.api.cli interactive')"]