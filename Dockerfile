FROM python:3-alpine AS builder
ENV MARK="9.11.0"

# From https://github.com/Zenika/alpine-chrome/blob/master/Dockerfile
RUN apk upgrade --no-cache --available \
    && apk add --no-cache \
      chromium-swiftshader \
      ttf-freefont \
      font-noto-emoji \
      curl \
      tar \
    && curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_Linux_x86_64.tar.gz && \
    tar -xvzf mark_Linux_x86_64.tar.gz && chmod +x mark && mv mark /usr/local/bin/mark

RUN mkdir -p /usr/src/app \
    && adduser -D -u 1001 mark \
    && chown -R mark:mark /usr/src/app
USER mark
WORKDIR /usr/src/app

ENV CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/lib/chromium/

ENV CHROMIUM_FLAGS="--disable-software-rasterizer --disable-dev-shm-usage"
ENTRYPOINT ["chromium-browser", "--headless"]
