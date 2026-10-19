# Stage 1: download & extract krig-miner
FROM python:3.12-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tar ca-certificates findutils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
# Ubah URL jika versi/rilis berbeda
ENV KRIG_URL="https://github.com/kryptex-miners-org/kryptex-miners/releases/download/krig-1-5-9/krig-miner-1.5.9-linux-x64.tar.gz"

# Download, extract, find the krig-miner binary and place it in a stable path
RUN set -eux; \
    curl -fsSL -o krig.tar.gz "$KRIG_URL"; \
    tar -zxvf krig.tar.gz; \
    # determine top-level extracted directory (if any)
    EXTRACT_DIR=$(tar -tzf krig.tar.gz | head -1 | cut -f1 -d"/"); \
    if [ -z "$EXTRACT_DIR" ]; then echo "failed to determine extracted directory" >&2; exit 1; fi; \
    echo "extracted to: $EXTRACT_DIR"; \
    # locate krig-miner binary anywhere under extracted dir
    BINPATH=$(find "$EXTRACT_DIR" -maxdepth 5 -type f -name krig-miner -print -quit || true); \
    if [ -z "$BINPATH" ]; then echo "krig-miner binary not found in archive" >&2; ls -la; exit 1; fi; \
    mkdir -p /opt/krig-miner; \
    mv "$BINPATH" /opt/krig-miner/krig-miner; \
    chmod 0755 /opt/krig-miner/krig-miner; \
    ls -la /opt/krig-miner

# Stage 2: runtime based on python:3.12-slim (Debian-slim) for easier debugging
FROM python:3.12-slim AS runtime

# Install minimal runtime deps and a few debugging tools (procps, iproute2, netcat-openbsd)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates procps iproute2 netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /opt/krig-miner/krig-miner /usr/local/bin/krig-miner

# Copy our python supervisor app
COPY app.py /app/app.py

# Workdir and minimal env
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Ensure binary is executable and set ownership for non-root user
RUN chmod 755 /usr/local/bin/krig-miner \
 && chown -R 1000:1000 /app

# Run as non-root numeric UID (no passwd entry required)
USER 1000

# Entrypoint: run supervisor Python
ENTRYPOINT ["python3", "/app/app.py"]
