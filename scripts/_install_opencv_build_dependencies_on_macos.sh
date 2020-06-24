#!/bin/bash
################################
# Install OpenCV dependencies

set -ex

sudo port install \
     clang-5.0 \
     clang_select \
     eigen3-devel \
     freetype \
     gdal \
     google-glog \
     hdf5 \
     harfbuzz \
     lapack \
     leptonica \
     libomp \
     llvm-5.0 \
     llvm_select \
     OpenBLAS-devel \
     py36-h5py-devel \
     py36-gdal \
     tesseract \

# OpenMP
sudo port select clang mp-clang-5.0
sudo port select llvm mp-llvm-5.0

#: needed for python3 bindings
python -m pip install numpy
