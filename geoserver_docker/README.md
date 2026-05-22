# GeoServer Docker Compose

This directory provides a standalone Docker Compose setup that deploys **only GeoServer**.

## Start

```bash
cd geoserver_docker
cp .env.example .env
docker compose up -d --build
```

## Default URL

```text
http://localhost:18081/geoserver
```

## Notes

- GeoServer data directory is persisted in the named volume `geoserver_data`.
- Host GPKG/job files are mounted read-only to `/data`.
- If your backend writes files elsewhere, update `GEOSERVER_SHARED_JOBS_DIR` in `.env`.

## Example backend settings

If your backend should talk to this standalone GeoServer:

```text
APP_GEOSERVER_URL=http://<docker-host>:18081/geoserver
APP_GEOSERVER_PUBLIC_URL=http://<docker-host>:18081/geoserver
```
