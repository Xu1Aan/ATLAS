ARG PYTHON_BASE_IMAGE=docker.m.daocloud.io/library/python:3.11-slim-bookworm
FROM ${PYTHON_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG LIBREDWG_VERSION=0.13.3
ARG APT_MIRROR=mirrors.aliyun.com
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG GNU_MIRROR=https://mirrors.ustc.edu.cn/gnu

WORKDIR /app

RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|http://deb.debian.org|https://${APT_MIRROR}|g; s|http://security.debian.org|https://${APT_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i "s|http://deb.debian.org|https://${APT_MIRROR}|g; s|http://security.debian.org|https://${APT_MIRROR}|g" /etc/apt/sources.list; \
    fi

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gdal-bin \
        libgdal-dev \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    urls="\
${GNU_MIRROR}/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz \
https://mirrors.aliyun.com/gnu/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz \
https://ftpmirror.gnu.org/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz \
https://ftp.gnu.org/gnu/libredwg/libredwg-${LIBREDWG_VERSION}.tar.xz"; \
    downloaded=''; \
    for url in $urls; do \
        if curl -fL --retry 3 --connect-timeout 20 "$url" -o /tmp/libredwg.tar.xz; then \
            downloaded="$url"; \
            break; \
        fi; \
    done; \
    test -n "$downloaded"; \
    mkdir -p /tmp/libredwg-src; \
    tar -xf /tmp/libredwg.tar.xz -C /tmp/libredwg-src --strip-components=1; \
    cd /tmp/libredwg-src; \
    ./configure --disable-bindings --disable-docs --enable-release; \
    make -j"$(nproc)"; \
    make install; \
    ldconfig; \
    rm -rf /tmp/libredwg.tar.xz /tmp/libredwg-src

COPY requirements.txt .
RUN pip install --no-cache-dir -i "${PIP_INDEX_URL}" -r requirements.txt

COPY .env ./.env
COPY app ./app

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
