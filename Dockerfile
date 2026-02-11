# Use the lightweight image you already have [cite: 10, 49]
FROM python:3.9-slim

# Keep your working OpenCV requirements for Trixie 
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx-mesa0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for faster rebuilding [cite: 10, 39]
COPY requirements.txt .
# Ensure bing-image-downloader is in your requirements.txt or add it here [cite: 51]
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir bing-image-downloader ultralytics

# Copy all files (including scraper.py and inventory.json) 
COPY . .

# Ensure the data and dataset directories exist inside the container [cite: 39, 53]
RUN mkdir -p data/logs dataset/images/train dataset/labels/train

EXPOSE 8501

# Default command remains Streamlit to keep the app running [cite: 10, 52]
CMD ["streamlit", "run", "main.py"]