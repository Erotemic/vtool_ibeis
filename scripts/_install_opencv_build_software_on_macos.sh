#!/bin/bash
################################
# Build OpenCV

set -ex

export OPENCV_VERSION=3.4.10

export WORKSPACE=$PWD

export VIRTUAL_ENV="/opt/opencv"

# Checkout source, only if it isn't already laying around
if [ ! -d ${WORKSPACE}/opencv ]; then
    git clone https://github.com/opencv/opencv.git ${WORKSPACE}/opencv
    git clone https://github.com/opencv/opencv_contrib.git ${WORKSPACE}/opencv_contrib
    cd ${WORKSPACE}/opencv
    git checkout ${OPENCV_VERSION}
    cd ${WORKSPACE}/opencv_contrib
    git checkout ${OPENCV_VERSION}
fi

# Build OpenCV, only if it's not already installed
if [ ! -d /opt/opencv ]; then
    rm -rf ${WORKSPACE}/opencv/build
    mkdir -p ${WORKSPACE}/opencv/build
    cd ${WORKSPACE}/opencv/build
    cmake \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=${VIRTUAL_ENV} \
        -D OPENCV_GENERATE_PKGCONFIG=ON \
        -D ENABLE_PRECOMPILED_HEADERS=OFF \
        -D BUILD_SHARED_LIBS=OFF \
        -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF \
        -D BUILD_DOCS=OFF \
        -D BUILD_EXAMPLES=OFF \
        -D BUILD_opencv_apps=OFF \
        -D BUILD_opencv_freetype=OFF \
        -D BUILD_opencv_hdf=OFF \
        -D BUILD_opencv_java=OFF \
        -D BUILD_opencv_python2=OFF \
        -D BUILD_opencv_python3=ON \
        -D BUILD_NEW_PYTHON_SUPPORT=ON \
        -D INSTALL_C_EXAMPLES=OFF \
        -D INSTALL_PYTHON_EXAMPLES=OFF \
        -D INSTALL_CREATE_DISTRIB=ON \
        -D BUILD_ZLIB=ON \
        -D BUILD_JPEG=ON \
        -D BUILD_WEBP=ON \
        -D BUILD_PNG=ON \
        -D BUILD_TIFF=ON \
        -D BUILD_JASPER=ON \
        -D BUILD_OPENEXR=ON \
        -D WITH_MATLAB=OFF \
        -D WITH_TBB=OFF \
        -D WITH_CUDA=OFF \
        -D WITH_CUBLAS=0 \
        -D WITH_EIGEN=ON \
        -D WITH_1394=OFF \
        -D WITH_FFMPEG=OFF \
        -D WITH_GSTREAMER=OFF \
        -D WITH_AVFOUNDATION=OFF \
        -D WITH_TESSERACT=OFF \
        -D WITH_HDR=ON \
        -D WITH_GDAL=OFF \
        -D WITH_WIN32UI=OFF \
        -D WITH_QT=OFF \
        -D PYTHON3_EXECUTABLE=$(which python3) \
        -D PYTHON3_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -D PYTHON3_INCLUDE_DIR2=$(python3 -c "from os.path import dirname; from distutils.sysconfig import get_config_h_filename; print(dirname(get_config_h_filename()))") \
        -D PYTHON3_LIBRARY=$(python3 -c "from distutils.sysconfig import get_config_var;from os.path import dirname,join ; print(join(dirname(get_config_var('LIBPC')),get_config_var('LDLIBRARY')))") \
        -D PYTHON3_NUMPY_INCLUDE_DIRS=$(python3 -c "import numpy; print(numpy.get_include())") \
        -D PYTHON3_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
        -D CMAKE_C_FLAGS="${CMAKE_C_FLAGS} -I/opt/local/include -stdlib=libc++" \
        -D CMAKE_CXX_FLAGS="${CMAKE_CXX_FLAGS} -I/opt/local/include -stdlib=libc++" \
        -D CMAKE_SHARED_LINKER_FLAGS="${CMAKE_SHARED_LINKER_FLAGS} -L/opt/local/lib -lc++" \
        -D CMAKE_EXE_LINKER_FLAGS="${CMAKE_EXE_LINKER_FLAGS} -L/opt/local/lib -lc++" \
        -D ENABLE_FAST_MATH=1 \
        -D CUDA_FAST_MATH=1 \
        -D OPENCV_ENABLE_NONFREE=ON \
        -D OPENCV_EXTRA_MODULES_PATH=${WORKSPACE}/opencv_contrib/modules \
        ..
    make -j9
    sudo make install
    sudo update_dyld_shared_cache
fi

# Return to the workspace
cd ${WORKSPACE}
