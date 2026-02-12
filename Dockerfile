# Use a Python base image
FROM python:3.9-slim

# 1. Install SYSTEM dependencies with the updated GL library
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

# 2. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your app
COPY . .

CMD ["streamlit", "run", "main.py"]