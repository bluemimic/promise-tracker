FROM nginx:alpine

COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/www/static /var/www/media