FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    unzip \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# نصب هسته Xray
ARG TARGETARCH
RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) XRAY_ARCH="64" ;; \
      arm64) XRAY_ARCH="arm64-v8a" ;; \
      *) XRAY_ARCH="64" ;; \
    esac; \
    curl -fsSL "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-${XRAY_ARCH}.zip" -o /tmp/xray.zip; \
    unzip -q /tmp/xray.zip -d /usr/local/bin/ xray; \
    chmod +x /usr/local/bin/xray; \
    rm -f /tmp/xray.zip

WORKDIR /app

COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh
COPY proxy_gen/uuids.txt /app/proxy_gen/uuids.txt

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

CMD ["/app/entrypoint.sh"]
