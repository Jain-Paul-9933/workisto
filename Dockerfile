FROM python:3.12-slim

# Keep Python lean and predictable inside the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# GeoDjango needs these native libraries (GDAL/GEOS/PROJ). This is the whole
# reason we run in Docker instead of fighting these installs on Windows.
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils \
        libproj-dev \
        gdal-bin \
        libgdal-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first so Docker caches this layer unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The actual start command is provided per-service in docker-compose.yml
