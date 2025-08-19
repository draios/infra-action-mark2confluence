FROM python:3.12-slim AS builder
ENV MARK="14.1.1"

ADD . /app
WORKDIR /app

RUN pip install --target=/app -r requirements.txt && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl gnupg2 && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_Linux_x86_64.tar.gz && \
    tar -xvzf mark_Linux_x86_64.tar.gz && chmod +x mark && mv mark /usr/local/bin/mark && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

FROM python:3.12-slim
COPY --from=builder /app /app
COPY --from=builder /usr/local/bin/mark /usr/bin/mark
COPY --from=builder /usr/bin/google-chrome /usr/bin/google-chrome
WORKDIR /app
ENV PYTHONPATH=/app
ENV DOC_PREFIX=/github/workspace/
ENV LOGURU_FORMAT="<lvl>{level:7} {message}</lvl>"
USER 1001:1001
ENTRYPOINT [ "python" ]
CMD ["/app/mark2confluence/main.py"]
