FROM python:3.11-slim-bookworm AS builder
ENV MARK="9.9.0"
ADD . /app
WORKDIR /app
RUN pip install --target=/app -r requirements.txt && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl gnupg2 && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_Linux_x86_64.tar.gz && \
    tar -xvzf mark_Linux_x86_64.tar.gz && chmod +x mark && mv mark /usr/local/bin/mark && rm mark_Linux_x86_64.tar.gz \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM chromedp/headless-shell:latest
RUN apt-get update \
&& apt-get install --no-install-recommends -qq ca-certificates bash sed git dumb-init python3 \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/mark /usr/bin/mark
WORKDIR /app
ENV PYTHONPATH /app
ENV DOC_PREFIX /github/workspace/
ENV LOGURU_FORMAT "<lvl>{level:7} {message}</lvl>"
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python3", "/app/mark2confluence/main.py"]
