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
    gtk2

#: needed for python3 bindings
python -m pip install numpy
