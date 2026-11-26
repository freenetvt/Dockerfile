FROM ghcr.io/mhsanaei/3x-ui:latest

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

COPY xuipanel/nginx.conf /etc/nginx/nginx.conf
COPY xuipanel/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
