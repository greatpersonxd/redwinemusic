FROM python:3.12-slim-bookworm

# Ffmpeg, git (bot ke liye) aur gcc, python3-dev (tgcrypto ke liye) install karein
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

# Packages install karne ke baad gcc aur python3-dev ko remove kar dein space bachane ke liye
RUN python -m pip install --no-cache-dir --upgrade pip setuptools && \
    python -m pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc python3-dev && \
    apt-get autoremove -y

CMD ["python", "-m", "SHIVMUSIC"]
