FROM python:3.9-slim

# Install system dependencies for Video/OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libavformat-dev libavcodec-dev \
    libavdevice-dev libavutil-dev libswscale-dev libswresample-dev \
    libavfilter-dev ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for lightning-fast builds
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies using uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

CMD ["streamlit", "run", "main.py"]