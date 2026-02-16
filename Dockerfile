# 1. Start with your base image
FROM python:3.11-slim

# 2. Set environment variables for production performance
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_MODE=production
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory
WORKDIR /app

# 4. Install system dependencies (OpenCV needs these)
# 4. Install system dependencies (Updated for OpenCV & Debian Trixie compatibility)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*
# 5. Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. COPY THE MODEL INTO THE IMAGE
# Note: Use best.onnx for production speed
COPY ./runs/detect/runs/pharma/exp_augmented_final/weights/best.onnx /app/models/medicine_v1.onnx

# 7. Copy the rest of your application code
COPY . .

# 8. Command to run the app
CMD ["streamlit", "run", "main.py"]