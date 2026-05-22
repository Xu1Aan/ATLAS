FROM docker.osgeo.org/geoserver:2.28.0

# Switch to root to install packages
USER root

RUN chmod 1777 /tmp && \
    apt-get update && \
    apt-get install -y --no-install-recommends wget unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Vector Tiles Plugin
# The plugin version must match the GeoServer image version exactly.
RUN wget -c https://sourceforge.net/projects/geoserver/files/GeoServer/2.28.0/extensions/geoserver-2.28.0-vectortiles-plugin.zip -O /tmp/vectortiles.zip && \
    GS_LIB_DIR="$(find / -type d -path '*/webapps/geoserver/WEB-INF/lib' 2>/dev/null | head -n 1)" && \
    test -n "${GS_LIB_DIR}" && \
    unzip /tmp/vectortiles.zip -d "${GS_LIB_DIR}" && \
    rm /tmp/vectortiles.zip

# Switch back to geoserver user
USER geoserver
