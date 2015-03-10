#!/bin/bash
#cd ~/code/vtool
echo "[sver.unix_build] checking if build dir should be removed"

python -c "import utool as ut; print('keeping build dir' if ut.get_argflag('--no-rmbuild') else ut.delete('build'))" $@

mkdir build
cd build

echo "$OSTYPE"

if [[ "$OSTYPE" == "darwin"* ]]; then
    cmake -DCMAKE_OSX_ARCHITECTURES=x86_64 -G "Unix Makefiles" ..  || { echo "FAILED CMAKE CONFIGURE" ; exit 1; }
elif [[ "$OSTYPE" == "msys"* ]]; then
    echo "USE MINGW BUILD INSTEAD" ; exit 1
    export INSTALL32="c:/Program Files (x86)"
    echo "INSTALL32=$INSTALL32"
    cmake -G "MSYS Makefiles" -DOpenCV_DIR="$INSTALL32/OpenCV" .. || { echo "FAILED CMAKE CONFIGURE" ; exit 1; }
else
    cmake -G "Unix Makefiles" ..  || { echo "FAILED CMAKE CONFIGURE" ; exit 1; }
fi

if [[ "$OSTYPE" == "msys"* ]]; then
    make || { echo "FAILED MAKE" ; exit 1; }
else
    export NCPUS=$(grep -c ^processor /proc/cpuinfo)
    make -j$NCPUS || { echo "FAILED MAKE" ; exit 1; }
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
	cp libsver* ../vtool
else
	cp libsver* ../vtool --verbose
fi
cd ..

