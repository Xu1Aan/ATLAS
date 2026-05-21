FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG LIBREDWG_VERSION=0.13.3

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gdal-bin \
        libgdal-dev \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://ftp.gnu.org/pub/gnu/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz" -o /tmp/libredwg.tar.xz \
    && mkdir -p /tmp/libredwg-src \
    && tar -xf /tmp/libredwg.tar.xz -C /tmp/libredwg-src --strip-components=1 \
    && cd /tmp/libredwg-src \
    && ./configure --disable-bindings --disable-docs --enable-release \
    && make -j"$(nproc)" \
    && make install \
    && ldconfig \
    && rm -rf /tmp/libredwg.tar.xz /tmp/libredwg-src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
