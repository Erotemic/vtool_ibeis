#!/bin/bash
################################
# Build OpenCV

set -ex

export OPENCV_VERSION=4.2.0
export WORKSPACE=$PWD

# Checkout source, only if it isn't already laying around
if [ ! -d $WORKSPACE/opencv ]; then
    git clone https://github.com/opencv/opencv.git $WORKSPACE/opencv
    git clone https://github.com/opencv/opencv_contrib.git $WORKSPACE/opencv_contrib
    cd $WORKSPACE/opencv
    git checkout $OPENCV_VERSION
    cd $WORKSPACE/opencv_contrib
    git checkout $OPENCV_VERSION
fi

# Build OpenCV, only if it's not already installed
if [ ! -d /opt/opencv ]; then
    # Create a new build space
    mkdir -p $WORKSPACE/opencv/build
    cd $WORKSPACE/opencv/build
    cmake \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/opt/opencv/ \
        -D OPENCV_EXTRA_MODULES_PATH=$WORKSPACE/opencv_contrib/modules \
        -D PYTHON3_LIBRARY=`python -c 'import subprocess ; import sys ; s = subprocess.check_output("python-config --configdir", shell=True).decode("utf-8").strip() ; (M, m) = sys.version_info[:2] ; print("{}/libpython{}.{}.dylib".format(s, M, m))'` \
        -D PYTHON3_INCLUDE_DIR=`python -c 'import distutils.sysconfig as s; print(s.get_python_inc())'` \
        -D PYTHON3_EXECUTABLE=`which python3.6` \
        -D BUILD_opencv_python2=OFF \
         -D OPENCV_GENERATE_PKGCONFIG=ON \
         -D ENABLE_PRECOMPILED_HEADERS=OFF \
         -D BUILD_opencv_apps=OFF \
         -D BUILD_SHARED_LIBS=OFF \
         -D BUILD_TESTS=OFF \
         -D BUILD_PERF_TESTS=OFF \
         -D BUILD_DOCS=OFF \
         -D BUILD_EXAMPLES=OFF \
         -D BUILD_opencv_java=OFF \
         -D BUILD_opencv_python3=ON \
         -D BUILD_NEW_PYTHON_SUPPORT=ON \
         -D INSTALL_C_EXAMPLES=OFF \
         -D INSTALL_PYTHON_EXAMPLES=OFF \
         -D INSTALL_CREATE_DISTRIB=ON \
         -D BUILD_JPEG=ON \
         -D BUILD_HDR=ON \
         -D WITH_MATLAB=OFF \
         -D WITH_TBB=ON \
         -D WITH_CUDA=OFF \
         -D WITH_CUBLAS=0 \
         -D WITH_EIGEN=ON \
         -D WITH_AVFOUNDATION=ON \
         -D WITH_JPEG=ON \
         -D BUILD_TIFF=ON \
         -D WITH_HDR=ON \
         -D WITH_V4L=ON \
         -D WITH_GDAL=ON \
         -D WITH_WIN32UI=OFF \
         -D WITH_QT=OFF \
         -D ENABLE_FAST_MATH=1 \
         -D CUDA_FAST_MATH=1 \
         -D OPENCV_ENABLE_NONFREE=ON \
         -D OPENCV_EXTRA_MODULES_PATH=$WORKSPACE/opencv_contrib/modules \
         ..
    make -j9

    # Install OpenCV
    sudo make install
    sudo update_dyld_shared_cache
fi

# Return to the workspace
cd $WORKSPACE
