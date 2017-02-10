#!/bin/bash

echo "[sver.unix_build] checking if build dir should be removed"
export FAILCMD='{ echo "FAILED VTOOL BUILD" ; exit 1; }'
python -c "import utool as ut; print('keeping build dir' if ut.get_argflag('--no-rmbuild') else ut.delete('build'))" $@

#################################
echo 'Removing old build'
rm -rf build
rm -rf CMakeFiles
rm -rf CMakeCache.txt
rm -rf cmake_install.cmake
#################################
echo 'Creating new build'
mkdir build
cd build
#################################

export PYEXE=$(which python)
if [[ "$VIRTUAL_ENV" == ""  ]]; then
    export LOCAL_PREFIX=/usr/local
    export _SUDO="sudo"
else
    export LOCAL_PREFIX=$($PYEXE -c "import sys; print(sys.prefix)")/local
    export _SUDO=""
fi


if [[ "$OSTYPE" == "msys"* ]]; then
    echo "INSTALL32=$INSTALL32"
    echo "HESAFF_INSTALL=$HESAFF_INSTALL"
    export INSTALL32="c:/Program Files (x86)"
    export OPENCV_DIR=$INSTALL32/OpenCV
else
    export OPENCV_DIR=$LOCAL_PREFIX/share/OpenCV
fi

if [[ ! -d $OPENCV_DIR ]]; then
    { echo "FAILED OPENCV DIR DOES NOT EXIST" ; exit 1; }
fi


echo 'Configuring with cmake'
if [[ '$OSTYPE' == 'darwin'* ]]; then
    cmake -G 'Unix Makefiles' \
        -DCMAKE_OSX_ARCHITECTURES=x86_64 \
        -DCMAKE_C_COMPILER=clang2 \
        -DCMAKE_CXX_COMPILER=clang2++ \
        -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
        -DOpenCV_DIR=$OPENCV_DIR \
        ..
elif [[ "$OSTYPE" == "msys"* ]]; then
    echo "USE MINGW BUILD INSTEAD" ; exit 1
    cmake -G "MSYS Makefiles" \
        -DCMAKE_INSTALL_PREFIX="$INSTALL32/Hesaff" \
        -DOpenCV_DIR=$OPENCV_DIR \
        ..
else
    cmake -G "Unix Makefiles" \
        -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
        -DOpenCV_DIR=$OPENCV_DIR \
        ..
fi

export CMAKE_EXITCODE=$?
if [[ $CMAKE_EXITCODE != 0 ]]; then
    { echo "FAILED VTOOL BUILD - CMake Step" ; exit 1; }
fi

if [[ "$OSTYPE" == "msys"* ]]; then
    make ||  $FAILCMD
else
    export NCPUS=$(grep -c ^processor /proc/cpuinfo)
    make -j$NCPUS ||  $FAILCMD
fi

cp -v libsver* ../vtool
cd ..
