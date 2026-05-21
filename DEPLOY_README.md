# Docker Deployment Guide

## Architecture
This project now ships with a Linux-oriented Docker Compose deployment that includes:

- `web`: Nginx single entrypoint for the frontend and reverse proxy
- `backend`: FastAPI with LibreDWG and GDAL installed
- `geoserver`: GeoServer with the vectortiles plugin preinstalled

Persistent volumes:

- `shared_jobs`: uploaded DWG files and generated DXF/GPKG data, mounted at `/data`
- `geoserver_data`: GeoServer data directory

## Environment Variables
Set these before production deployment, either in the shell or in a root `.env` file:

```ini
APP_GEOSERVER_USER=admin
APP_GEOSERVER_PASSWORD=geoserver
APP_GEOSERVER_WORKSPACE=dwg
APP_GEOSERVER_PUBLIC_URL=http://your-host:18081/geoserver
APP_GAUSS_KRUGER_ZONE=39
APP_ENABLE_GAUSS_KRUGER_TRANSFORM=true
```

Notes:

- `APP_GEOSERVER_URL` is fixed to the internal Compose address `http://geoserver:8080/geoserver`
- `APP_GEOSERVER_PUBLIC_URL` is still used by the GeoServer container as `PROXY_BASE_URL`
- Tile URLs returned by the backend are now relative `/geoserver/...` paths, so frontend tile loading does not depend on `APP_GEOSERVER_PUBLIC_URL`

## Start
Run from the repository root:

```bash
docker compose up --build -d
```

Endpoints:

- Frontend: `http://<host>:18081/`
- Backend health: `http://<host>/api/healthz`
- GeoServer UI: `http://<host>:18081/geoserver/web/`

## Verification
Useful checks:

```bash
docker compose ps
docker compose logs backend
docker compose logs geoserver
```

Then verify in the browser:

- `/` loads the frontend
- `/api/healthz` returns `{"status":"ok"}`
- `/geoserver/web/` opens the GeoServer console
- Uploading a DWG generates files under `/data/jobs/<job_id>` and renders both vector and raster map modes

## Persistence and Restart
- Rebuilding containers keeps `shared_jobs` data intact
- `geoserver_data` preserves workspaces, styles, stores, and published layers

Useful commands:

```bash
docker compose restart
docker compose down
docker volume ls
```

## Troubleshooting
- `backend` startup logs include the resolved `dwg2dxf` and `ogr2ogr` executables
- `backend` waits for a healthy `geoserver` before it starts
- If GeoServer generates incorrect self-links or admin redirects, check that `APP_GEOSERVER_PUBLIC_URL` matches the real external address
