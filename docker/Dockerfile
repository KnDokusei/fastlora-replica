# Entorno de simulación para la réplica de FAST-LoRa:
# OMNeT++ 6.0.3 (core, sin IDE ni Qtenv) + INET 4.4.1 + Python 3.10 con las dependencias de MultiAgent-MARLTC.
# FLoRa no se compila aquí: se compila desde el repo montado con scripts/build_flora.sh.
FROM ubuntu:22.04

ARG OMNETPP_VERSION=6.0.3
ARG INET_VERSION=4.4.1
ARG JOBS=2
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential clang lld gdb bison flex perl \
        python3 python3-dev python3-pip python3-venv \
        libxml2-dev zlib1g-dev git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# OMNeT++: solo Cmdenv, en modo release
WORKDIR /opt
RUN curl -fsSL https://github.com/omnetpp/omnetpp/releases/download/omnetpp-${OMNETPP_VERSION}/omnetpp-${OMNETPP_VERSION}-core.tgz | tar xz \
    && mv omnetpp-${OMNETPP_VERSION} omnetpp
WORKDIR /opt/omnetpp
RUN source setenv -q \
    && ./configure WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no \
    && make -j${JOBS} MODE=release \
    && rm -rf out
ENV PATH=/opt/omnetpp/bin:$PATH \
    LD_LIBRARY_PATH=/opt/omnetpp/lib

# INET: el tarball se extrae como inet4.4/, el mismo nombre que espera MultiAgent-MARLTC
WORKDIR /opt
RUN curl -fsSL https://github.com/inet-framework/inet/releases/download/v${INET_VERSION}/inet-${INET_VERSION}-src.tgz | tar xz
WORKDIR /opt/inet4.4
RUN source /opt/omnetpp/setenv -q && source setenv -q \
    && make makefiles \
    && make -j${JOBS} MODE=release \
    && rm -rf out
ENV INET_ROOT=/opt/inet4.4 \
    PATH=/opt/inet4.4/bin:$PATH \
    LD_LIBRARY_PATH=/opt/inet4.4/src:/opt/omnetpp/lib

# Python de los scripts de validación de los autores. torch en su build CPU (el GPU solo se usa en Colab).
COPY requirements-marltc.txt /tmp/requirements-marltc.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements-marltc.txt
ENV PATH=/opt/venv/bin:$PATH

# Rutas que usan los scripts de FastLoRa (test/flora.py)
ENV FLORA_ROOT=/work/third_party/MultiAgent-MARLTC/flora/flora

RUN groupadd -g ${GID} sim && useradd -m -u ${UID} -g ${GID} sim
USER sim
WORKDIR /work
