FROM python:3.11-slim-bookworm AS builder
ENV MARK="9.11.1"

ADD . /app
WORKDIR /app

RUN pip install --target=/app -r requirements.txt && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl gnupg2 && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_Linux_x86_64.tar.gz && \
    tar -xvzf mark_Linux_x86_64.tar.gz && chmod +x mark && mv mark /usr/local/bin/mark \
    && curl -L https://dl-ssl.google.com/linux/linux_signing_key.pub |apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt update && apt-get install -y google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# FROM python:3.11-slim-bookworm
# COPY --from=builder /app /app
# COPY --from=builder /usr/local/bin/mark /usr/bin/mark
# COPY --from=builder /opt/google/chrome/chrome /usr/bin/chrome
# COPY --from=builder /usr/bin/google-chrome /usr/bin/google-chrome
# WORKDIR /app
ENV PYTHONPATH /app
ENV DOC_PREFIX /github/workspace/
ENV LOGURU_FORMAT "<lvl>{level:7} {message}</lvl>"
ENV PATH="${PATH}:/opt/google/chrome"
RUN useradd -ms /bin/bash mark2confluence && \
    chown -R mark2confluence:mark2confluence /app && \
    chmod -R 755 /app && \
    usermod -aG users mark2confluence
USER mark2confluence:users
ENTRYPOINT [ "python" ]
CMD ["/app/mark2confluence/main.py"]
