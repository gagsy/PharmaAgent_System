# 1. Start with Python 3.11 slim image
FROM python:3.11-slim

# 2. Performance & Streamlit Env Variables
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_MODE=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3. Set working directory
WORKDIR /app

# 4. Install System Dependencies (OpenCV, Tesseract, and GL libraries)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Install Python requirements (Fixing Hash Mismatch)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    (pip install --no-cache-dir -r requirements.txt || \
    (pip cache purge && pip install --no-cache-dir -r requirements.txt))

# 6. Prepare Model Directory
# This ensures the folder structure matches your code's path logic
RUN mkdir -p /app/models
COPY ./runs/detect/runs/pharma/exp_augmented_final3/weights/best.onnx /app/models/besttwo.onnx

# 7. Copy remaining application files
COPY . .

# 8. Command to run (Binding to 0.0.0.0 is mandatory for Cloud/Docker access)
EXPOSE 8501
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]