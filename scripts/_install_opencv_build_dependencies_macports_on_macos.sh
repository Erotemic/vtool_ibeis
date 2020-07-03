#!/bin/bash
###############################
# Install MacPorts dependencies

set -ex

sudo port selfupdate

# Install ports if MacPorts install location is not present
sudo port install \
    pkgconfig \
    libomp-devel \
    gflags \
    eigen3-devel \
    gtk2 \
    # libdc1394 \
    # ffmpeg \
    # gstreamer1-gst-plugins-base

#: needed for python3 bindings
python -m pip install numpy
