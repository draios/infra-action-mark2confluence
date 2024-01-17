FROM python:3.11-slim-bookworm AS builder
ENV MARK="9.11.0"

ADD . /app
WORKDIR /app

RUN pip install --target=/app -r requirements.txt && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl gnupg2 && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_Linux_x86_64.tar.gz && \
    tar -xvzf mark_Linux_x86_64.tar.gz && chmod +x mark && mv mark /usr/local/bin/mark \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    # && curl -L https://dl-ssl.google.com/linux/linux_signing_key.pub |apt-key add - \
    # && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    # && apt update && apt-get install -y google-chrome-stable \

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
ENV PATH="${PATH}:/opt/google/chrome"
ENTRYPOINT [ "python" ]
CMD ["/app/mark2confluence/main.py"]
