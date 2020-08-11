FROM python:3.8-alpine

COPY . /app
WORKDIR /app
RUN apk add bash
RUN pip install -U pip && pip install .
RUN addgroup -g 1000 yasha && adduser -h /data -G yasha -D -u 1000 yasha
VOLUME /data
WORKDIR /data
USER yasha
CMD ["bash"]