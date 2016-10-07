#!/bin/bash

echo "[sver.unix_build] checking if build dir should be removed"
export FAILCMD='{ echo "FAILED VTOOL BUILD" ; exit 1; }'
python2.7 -c "import utool as ut; print('keeping build dir' if ut.get_argflag('--no-rmbuild') else ut.delete('build'))" $@

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

export PYEXE=$(which python2.7)
if [[ "$VIRTUAL_ENV" == ""  ]]; then
    export LOCAL_PREFIX=/usr/local
    export _SUDO="sudo"
else
    export LOCAL_PREFIX=$($PYEXE -c "import sys; print(sys.prefix)")/local
    export _SUDO=""
fi

echo 'Configuring with cmake'
if [[ '$OSTYPE' == 'darwin'* ]]; then
    export CONFIG="-DCMAKE_OSX_ARCHITECTURES=x86_64 -DCMAKE_C_COMPILER=clang2 -DCMAKE_CXX_COMPILER=clang2++ -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX -DOpenCV_DIR=$LOCAL_PREFIX/share/OpenCV"
    cmake $CONFIG -G 'Unix Makefiles' ..
elif [[ "$OSTYPE" == "msys"* ]]; then
    echo "USE MINGW BUILD INSTEAD" ; exit 1
    export INSTALL32="c:/Program Files (x86)"
    echo "INSTALL32=$INSTALL32"
    cmake -G "MSYS Makefiles" -DOpenCV_DIR="$INSTALL32/OpenCV" .. || $FAILCMD
else
    cmake -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX -DOpenCV_DIR=$LOCAL_PREFIX/share/OpenCV ..  ||  $FAILCMD
fi

if [[ "$OSTYPE" == "msys"* ]]; then
    make ||  $FAILCMD
else
    export NCPUS=$(grep -c ^processor /proc/cpuinfo)
    make -j$NCPUS ||  $FAILCMD
fi

cp -v libsver* ../vtool
cd ..
