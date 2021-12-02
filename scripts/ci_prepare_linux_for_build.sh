#!/bin/bash

set -ex

apt-get install -y \
	pkg-config \
	libeigen3-dev \
	libopencv-dev \
	libomp-dev
