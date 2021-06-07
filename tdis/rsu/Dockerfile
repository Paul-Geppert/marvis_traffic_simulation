FROM ubuntu:20.04

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install --no-install-recommends -y tshark && \
    apt install --no-install-recommends -y \
    python3.8 python3-pip iproute2 iputils-ping libxmlrpc-core-c3

RUN pip3 install pyshark

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

COPY generator/ /generator/
CMD ["python3", "-m", "generator", "-i", "v2x"]
