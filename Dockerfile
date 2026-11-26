FROM ghcr.io/mhsanaei/3x-ui:latest

RUN apk add --no-cache nginx

COPY xuipanel/nginx.conf /etc/nginx/nginx.conf
COPY xuipanel/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
