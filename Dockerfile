FROM python:3-slim AS builder

ADD . /app
WORKDIR /app

RUN pip install --target=/app -r requirements.txt

FROM python:3-slim
ENV MARK="6.7"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl sudo && \
  rm -rf /var/lib/apt/lists/*
RUN curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_${MARK}_Linux_x86_64.tar.gz && \
  tar -xvzf mark_${MARK}_Linux_x86_64.tar.gz && \
  chmod +x mark && \
  sudo mv mark /usr/local/bin/mark

COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app
ENV DOC_PREFIX /github/workspace/
ENV LOGURU_FORMAT "<lvl>{level:7} {message}</lvl>"
ENTRYPOINT [ "python" ]
CMD ["/app/src/main.py"]
