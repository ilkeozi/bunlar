ARG UBUNTU_VERSION=22.04
FROM ubuntu:${UBUNTU_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

ARG FREECAD_APPIMAGE_URL=https://github.com/FreeCAD/FreeCAD/releases/download/1.0.2/FreeCAD_1.0.2-conda-Linux-x86_64-py311.AppImage
ARG FREECAD_APPIMAGE_SHA256=e00be00ad9fdb12b05c5002bfd1aa2ea8126f2c1d4e2fb603eb7423b72904f61

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    python3 \
  && curl -L -o /tmp/FreeCAD.AppImage "${FREECAD_APPIMAGE_URL}" \
  && echo "${FREECAD_APPIMAGE_SHA256}  /tmp/FreeCAD.AppImage" | sha256sum -c - \
  && chmod +x /tmp/FreeCAD.AppImage \
  && /tmp/FreeCAD.AppImage --appimage-extract \
  && mv squashfs-root /opt/freecad \
  && printf '%s\n' '#!/bin/sh' 'exec /opt/freecad/AppRun freecadcmd "$@"' > /usr/local/bin/freecadcmd \
  && chmod +x /usr/local/bin/freecadcmd \
  && rm -rf /var/lib/apt/lists/* /tmp/FreeCAD.AppImage

WORKDIR /app
COPY cad-converter /app

ENTRYPOINT ["python3", "scripts/convert.py"]
