FROM python:3.12-slim

WORKDIR /app

# Install build deps minimally
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir -e .

# Defaults; override at runtime with -e
ENV GMC_TRANSPORT=sse \
    GMC_HOST=0.0.0.0 \
    GMC_PORT=8000

EXPOSE 8000

ENTRYPOINT ["gmc-mcp"]
CMD ["--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
