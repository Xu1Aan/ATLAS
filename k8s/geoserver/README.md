# GeoServer K8s Deployment

This directory contains a simple Kubernetes deployment for GeoServer that matches the current `dwg2mvt` architecture:

- GeoServer runs as an independent service in Kubernetes
- the service exposes port `80` and forwards to container port `8080`
- GeoServer mounts the same shared jobs volume as the backend at `/data` as read-only
- GeoServer data directory is persisted separately

## Files

- `secret.yaml`: admin credentials
- `pvc-geoserver-data.yaml`: persistent storage for `/opt/geoserver/data_dir`
- `deployment.yaml`: GeoServer deployment
- `service.yaml`: ClusterIP service `80 -> 8080`
- `kustomization.yaml`: convenience manifest set

## Important

GeoServer must be able to read the same `.gpkg` files that the backend writes under `/data/jobs/...`.

That means:

1. The backend and GeoServer must use the same shared PVC.
2. The shared PVC should support `ReadWriteMany` in production.

This deployment assumes the backend shared PVC is already named:

`dwg2mvt-shared-jobs`

If your actual PVC name is different, update `deployment.yaml`.

## Apply

```bash
kubectl apply -k k8s/geoserver -n sw-dev
```

## Expected in-cluster address

```text
http://geoserver.sw-dev.svc.cluster.local
```

## Suggested gateway route

```json
{
  "pattern": "/public/dwgconvert/geoserver/**",
  "uri": "http://geoserver.sw-dev.svc.cluster.local",
  "stripPrefix": "2"
}
```

## Backend settings

The backend should use the in-cluster GeoServer service and the shared `/data` mount:

```text
APP_WORK_DIR=/data
APP_GEOSERVER_URL=http://geoserver.sw-dev.svc.cluster.local/geoserver
APP_GEOSERVER_PUBLIC_URL=/public/dwgconvert/geoserver
```
