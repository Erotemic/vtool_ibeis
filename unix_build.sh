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
if [[ "$VIRTUAL_ENV" == ""  ]] && [[ "$CONDA_PREFIX" == ""  ]] ; then
    export LOCAL_PREFIX=/usr/local
    export _SUDO="sudo"
else
    if [[ "$CONDA_PREFIX" == ""  ]] ; then
        export LOCAL_PREFIX=$($PYEXE -c "import sys; print(sys.prefix)")/local
    else
        export LOCAL_PREFIX=$($PYEXE -c "import sys; print(sys.prefix)")
    fi
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

if [ -d "$LOCAL_PREFIX/share/OpenCV" ]; then
    OPENCV_ARGS="-DOpenCV_DIR=$LOCAL_PREFIX/share/OpenCV"
else
    OPENCV_ARGS=""
fi

#if [[ "$OSTYPE" != "darwin"* ]]; then
#    if [[ ! -d $OPENCV_DIR ]]; then
#        echo $OPENCV_DIR
#        { echo "FAILED OPENCV DIR DOES NOT EXIST" ; exit 1; }
#    fi
#fi

echo 'Configuring with cmake'
if [[ '$OSTYPE' == 'darwin'* ]]; then
    cmake -G 'Unix Makefiles' \
        -DCMAKE_OSX_ARCHITECTURES=x86_64 \
        -DCMAKE_C_COMPILER=clang2 \
        -DCMAKE_CXX_COMPILER=clang2++ \
        -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
        $OPENCV_ARGS \
        ..
elif [[ "$OSTYPE" == "msys"* ]]; then
    echo "USE MINGW BUILD INSTEAD" ; exit 1
    cmake -G "MSYS Makefiles" \
        -DCMAKE_INSTALL_PREFIX="$INSTALL32/Hesaff" \
        $OPENCV_ARGS \
        ..
else
    cmake -G "Unix Makefiles" \
        -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
        -DCMAKE_C_FLAGS="${CMAKE_C_FLAGS}" \
        -DCMAKE_CXX_FLAGS="${CMAKE_CXX_FLAGS}" \
        -DCMAKE_SHARED_LINKER_FLAGS="${CMAKE_SHARED_LINKER_FLAGS}" \
        -DCMAKE_EXE_LINKER_FLAGS="${CMAKE_EXE_LINKER_FLAGS}" \
        $OPENCV_ARGS \
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
