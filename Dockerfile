FROM python:3.12-bookworm

# Install X11 and browser dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY . .

RUN playwright install --with-deps chromium

EXPOSE 3000
