# GeoServer Docker Compose

This directory provides a standalone Docker Compose setup that deploys **only GeoServer**.
It matches the current backend behavior where the backend publishes by **uploading GeoPackage files over GeoServer REST**, so no shared `/data` mount is required.

## Start

```bash
cd geoserver_docker
cp .env.example .env
docker compose up -d --build
```

If this GeoServer runs on `10.20.124.71`, keep the default:

```text
GEOSERVER_PUBLIC_URL=http://10.20.124.71:18081/geoserver
```

## Default URL

`http://10.20.124.71:18081/geoserver`

## Notes

- GeoServer data directory is persisted in the named volume `geoserver_data`.
- The backend can publish directly to this GeoServer over REST; no shared filesystem is needed.
- The image is built locally from `Dockerfile` so the vector tiles plugin is bundled in.

## Example backend settings

If your backend should talk to this standalone GeoServer:

```text
APP_GEOSERVER_URL=http://10.20.124.71:18081/geoserver
APP_GEOSERVER_PUBLIC_URL=http://10.20.124.71:18081/geoserver
APP_GEOSERVER_USER=admin
APP_GEOSERVER_PASSWORD=geoserver
```
