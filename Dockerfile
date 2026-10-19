# Stage 1: download & extract krig-miner
FROM python:3.11-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tar ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
# Ubah URL jika versi/rilis berbeda
ENV KRIG_URL="https://github.com/kryptex-miners-org/kryptex-miners/releases/download/krig-1-5-9/krig-miner-1.5.9-linux-x64.tar.gz"
RUN curl -fsSL -o krig.tar.gz "$KRIG_URL" \
 && tar -zxvf krig.tar.gz \
 && ls -l

# Stage 2: runtime based on debian-slim for easier debugging
FROM python:3.11-slim AS runtime

# Install minimal runtime deps and a few debugging tools (procps, iproute2, netcat)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates procps iproute2 netcat \
 && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /opt/krig-miner-1.5.9/krig-miner /usr/local/bin/krig-miner

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
