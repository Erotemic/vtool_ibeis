#!/bin/bash

set -ex

if command -v yum &> /dev/null
then
    yum install -y \
        pkgconfig \
        eigen3-devel \
        opencv-devel \
        libgomp
else
    apt-get install -y \
        pkg-config \
        libeigen3-dev \
        libopencv-dev \
        libomp5 \
        libomp-dev
fi
