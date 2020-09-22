FROM python:3.8-alpine

ENV DJANGO_SETTINGS_MODULE=fabpolls.settings

RUN \
  apk add --update \
      build-base ca-certificates gcc linux-headers \
      libressl-dev libffi-dev libxml2-dev libxslt-dev python3-dev zlib-dev && \
  rm -rf /var/cache/apk/*

WORKDIR /opt/fabpolls

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD . .

RUN chmod 755 docker-entrypoint.sh

EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
