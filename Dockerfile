# Use a standard, official Python image (3.11 is recommended for stability over 3.13.3 base)
FROM python:3.11-slim-bookworm

# 1. Install System Dependencies: Tesseract OCR, language data, and build essentials
# Tesseract is required by pytesseract.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements and install Python dependencies
COPY requirements.txt .
# Use --no-cache-dir for a smaller image size
RUN pip install --no-cache-dir -r requirements.txt

# 4. CRITICAL: Download and link the spaCy model inside the container
# This must happen AFTER 'spacy' is installed via pip.
RUN python -m spacy download en_core_web_sm

# 5. Copy the entire application source code
# Assuming 'main.py' and the 'app/' directory are in your project root.
COPY . .

# 6. Define the port the container will listen on
EXPOSE 8000

# 7. Command to run the application using Uvicorn
# The --host 0.0.0.0 is necessary for external container access.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
