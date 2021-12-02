#!/bin/bash

set -ex

pip install -r requirements/build.txt

if command -v yum &> /dev/null
then
    yum update

    yum install -y \
        pkgconfig \
        eigen3-devel \
        opencv-devel \
        libgomp
else
    apt-get update

    apt-get install -y \
        pkg-config \
        libeigen3-dev \
        libopencv-dev \
        libomp5 \
        libomp-dev
fi
