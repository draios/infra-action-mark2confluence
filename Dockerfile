FROM python:3-slim AS builder

ADD . /app
WORKDIR /app

RUN pip install --target=/app -r requirements.txt

FROM python:3-slim
ENV MARK="9.2.1"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y tar curl sudo && \
  rm -rf /var/lib/apt/lists/*
RUN curl -LO https://github.com/kovetskiy/mark/releases/download/${MARK}/mark_${MARK}_Linux_x86_64.tar.gz && \
  tar -xvzf mark_${MARK}_Linux_x86_64.tar.gz && \
  chmod +x mark && \
  sudo mv mark /usr/local/bin/mark
  
# mermaid-go mermaid provider would err "google-chrome: executable file not found" if google chrome executable is not present
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install -y wget
RUN apt-get update && apt-get install -y gnupg2
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \ 
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable

COPY --from=builder /app /app
WORKDIR /app
ENV PYTHONPATH /app
ENV DOC_PREFIX /github/workspace/
ENV LOGURU_FORMAT "<lvl>{level:7} {message}</lvl>"
ENTRYPOINT [ "python" ]
CMD ["/app/mark2confluence/main.py"]
