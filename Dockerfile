FROM python:3.9-slim

# Enable multiarch and update
RUN dpkg --add-architecture amd64 && \
    apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    libgconf-2-4 \
    xvfb \
    libxi6 \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxtst6 \
    libxss1 \
    libasound2 \
    libxrandr2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libcurl4 \
    libcairo2 \
    libatspi2.0-0 \
    libexpat1 \
    libgbm1 \
    libpango-1.0-0 \
    libudev1 \
    libvulkan1 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxfixes3

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY . .
# Create a non-root user for Chrome
RUN playwright install
