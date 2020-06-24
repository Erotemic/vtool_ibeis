#!/bin/bash
################################
# Install OpenCV dependencies

set -ex

sudo port install \
     clang-5.0 \
     clang_select \
     llvm-5.0 \
     llvm_select \
     libomp \
     gflags \
     libpng \
     jasper \
     ilmbase \
     openexr \
     webp \
     jpeg \
     tiff \
     tbb \
     libdc1394 \
     eigen3-devel \
     boost \
     bzip2 \
     zlib \
     ffmpeg \
     freeglut \
     mesa \
     gstreamer1-gst-plugins-base \
     qt5-qtbase \
     gtk2 \
     ade

# OpenMP
sudo port select clang mp-clang-5.0
sudo port select llvm mp-llvm-5.0

#: needed for python3 bindings
python -m pip install numpy
