# GeoServer K8s Deployment

This directory contains a simple Kubernetes deployment for GeoServer that matches the current `dwg2mvt` architecture:

- GeoServer runs as an independent service in Kubernetes
- the service exposes port `80` and forwards to container port `8080`
- backend uploads each generated GeoPackage to GeoServer over REST
- GeoServer data directory is persisted separately

## Files

- `secret.yaml`: admin credentials
- `pvc-geoserver-data.yaml`: persistent storage for `/opt/geoserver/data_dir`
- `deployment.yaml`: GeoServer deployment
- `service.yaml`: ClusterIP service `80 -> 8080`
- `kustomization.yaml`: convenience manifest set
- `kustomization.harbor.example.yaml`: example image override for Harbor or another local registry
- `overlays/harbor/kustomization.yaml`: ready-to-use Harbor overlay

## Important

GeoServer no longer depends on a shared `/data` PVC with the backend.

The backend publishes by uploading the `.gpkg` file into GeoServer directly, so GeoServer only needs its own persistent data directory.

## Apply

Deploy GeoServer:

```bash
kubectl apply -k k8s/geoserver -n sw-dev
```

## Image pull acceleration

If cluster nodes are slow to pull `docker.osgeo.org/geoserver:2.28.0`, the best option is to mirror that image into your own Harbor and deploy from the in-network registry.

Example workflow:

1. Sync or retag the image into Harbor.
2. Update `overlays/harbor/kustomization.yaml` with your actual Harbor image path.
3. Apply that overlay instead of the default base.

Example:

```bash
kubectl apply -k k8s/geoserver/overlays/harbor -n sw-dev
```

If you prefer a registry mirror instead of Harbor, update the image in `deployment.yaml` directly or create a similar Kustomize overlay that rewrites:

`docker.osgeo.org/geoserver:2.28.0`

## Quick checks

```bash
kubectl get pvc -n sw-dev
kubectl get pods -n sw-dev -l app=geoserver
kubectl describe pod -n sw-dev -l app=geoserver
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

The backend should use the in-cluster GeoServer service. A local work directory inside the backend pod is enough:

```text
APP_WORK_DIR=/data
APP_GEOSERVER_URL=http://geoserver.sw-dev.svc.cluster.local/geoserver
APP_GEOSERVER_PUBLIC_URL=/public/dwgconvert/geoserver
```
