FROM ubuntu:20.04

RUN apt update && \
    apt install --no-install-recommends -y \
        python3 libxmlrpc-core-c3 iproute2 iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

COPY generator/ /generator/
CMD ["python3", "generator/generator.py", "-i", "v2x"]
