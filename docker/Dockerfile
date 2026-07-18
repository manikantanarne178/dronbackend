FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# -------------------------------------------------------
# Install dependencies
# -------------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    cmake \
    ninja-build \
    pkg-config \
    wget \
    unzip \
    curl \
    python3 \
    python3-pip \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libxxf86vm-dev \
    libxi-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libglu1-mesa-dev \
    libgl1-mesa-dev \
    libeigen3-dev \
    libboost-all-dev \
    libceres-dev \
    libopencv-dev \
    libglew-dev \
    libatlas-base-dev \
    libflann-dev \
    libsqlite3-dev \
    libomp-dev

# -------------------------------------------------------
# Build OpenMVG
# -------------------------------------------------------

WORKDIR /opt

RUN git clone --recursive https://github.com/openMVG/openMVG.git

WORKDIR /opt/openMVG

RUN mkdir build

WORKDIR /opt/openMVG/build

RUN cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -GNinja

RUN ninja

RUN ninja install

# -------------------------------------------------------
# Build OpenMVS
# -------------------------------------------------------

WORKDIR /opt

RUN git clone --recursive https://github.com/cdcseacave/openMVS.git

WORKDIR /opt/openMVS

RUN mkdir build

WORKDIR /opt/openMVS/build

RUN cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -GNinja

RUN ninja

RUN ninja install

# -------------------------------------------------------
# Working directory
# -------------------------------------------------------

WORKDIR /workspace

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]