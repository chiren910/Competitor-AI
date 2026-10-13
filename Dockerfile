FROM python:3.11-slim

# Install system dependencies (includes dependencies for headless browsers)
RUN apt-get update && \
    apt-get install -y wget gnupg curl unzip fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgdk-pixbuf2.0-0 \
    libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
    libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 xdg-utils \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_FLAGS="--headless --disable-gpu --no-sandbox --disable-dev-shm-usage --disable-software-rasterizer"

# Install Python dependencies and Playwright browsers
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install --with-deps

# Expose the FastAPI port
EXPOSE 4545

# Run the app with gunicorn for better production performance
CMD ["python","main.py"]