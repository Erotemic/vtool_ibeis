#!/bin/bash
__heredoc__="""


notes:

    # TODO: use dind as the base image,
    # Then run the multibuild in docker followed by a test in a different
    # docker container

    # BETTER TODO: 
    # Use a build stage to build in the multilinux environment and then
    # use a test stage with a different image to test and deploy the wheel
    docker run --rm -it --entrypoint="" docker:dind sh
    docker run --rm -it --entrypoint="" docker:latest sh
    docker run --rm -v $PWD:/io -it --entrypoint="" docker:latest sh

    docker run --rm -v $PWD:/io -it python:2.7 bash
     
        cd /io
        pip install -r requirements.txt
        pip install pygments
        pip install wheelhouse/pyflann_ibeis-0.5.0-cp27-cp27mu-manylinux1_x86_64.whl

        cd /
        xdoctest pyflann_ibeis
        pytest io/tests

        cd /io
        python run_tests.py


MB_PYTHON_TAG=cp37-cp37m ./run_multibuild.sh
MB_PYTHON_TAG=cp36-cp36m ./run_multibuild.sh
MB_PYTHON_TAG=cp35-cp35m ./run_multibuild.sh
MB_PYTHON_TAG=cp27-cp27m ./run_multibuild.sh

# MB_PYTHON_TAG=cp27-cp27mu ./run_nmultibuild.sh

docker pull quay.io/erotemic/manylinux-opencv:manylinux1_i686-opencv4.1.0-py3.6

"""


get_native_mb_python_tag(){
    __heredoc__='''
    Get the MB tag for the current version of python running
    
    https://stackoverflow.com/questions/53409511/what-is-the-difference-between-cpython-27m-and-27mu?noredirect=1&lq=1
    '''
    python -c "
import sys
import platform
major = sys.version_info[0]
minor = sys.version_info[1]
ver = '{}{}'.format(major, minor)
if platform.python_implementation() == 'CPython':
    impl = 'cp'
    abi = 'm'
else:
    raise NotImplementedError(impl)
mb_tag = '{impl}{ver}-{impl}{ver}{abi}'.format(**locals())
print(mb_tag)
"
}


DOCKER_IMAGE=${DOCKER_IMAGE:="quay.io/erotemic/manylinux-for:x86_64-opencv4.1.0-v2"}
# Valid multibuild python versions are:
# cp27-cp27m  cp27-cp27mu  cp34-cp34m  cp35-cp35m  cp36-cp36m  cp37-cp37m
MB_PYTHON_TAG=${MB_PYTHON_TAG:=$(python -c "import setup; print(setup.MB_PYTHON_TAG)")}
NAME=${NAME:=$(python -c "import setup; print(setup.NAME)")}
VERSION=${VERSION:=$(python -c "import setup; print(setup.VERSION)")}
echo "
MB_PYTHON_TAG = $MB_PYTHON_TAG
DOCKER_IMAGE = $DOCKER_IMAGE
VERSION = $VERSION
NAME = $NAME
"

if [ "$_INSIDE_DOCKER" != "YES" ]; then

    set -e
    docker run --rm \
        -v $PWD:/io \
        -e _INSIDE_DOCKER="YES" \
        -e MB_PYTHON_TAG="$MB_PYTHON_TAG" \
        -e NAME="$NAME" \
        -e VERSION="$VERSION" \
        $DOCKER_IMAGE bash -c 'cd /io && ./run_multibuild.sh'

    __interactive__='''
    docker run --rm \
        -v $PWD:/io \
        -e _INSIDE_DOCKER="YES" \
        -e MB_PYTHON_TAG="$MB_PYTHON_TAG" \
        -e NAME="$NAME" \
        -e VERSION="$VERSION" \
        -it $DOCKER_IMAGE bash

    set +e
    set +x
    '''

    BDIST_WHEEL_PATH=$(ls wheelhouse/$NAME-$VERSION-$MB_PYTHON_TAG*.whl)
    echo "BDIST_WHEEL_PATH = $BDIST_WHEEL_PATH"
else
    set -x
    set -e

    VENV_DIR=$HOME/venv-$MB_PYTHON_TAG
    #PY_VER=$(python -c "print('$MB_PYTHON_TAG'[2:4])")
    #PYTHON_ROOT=/opt/python/$MB_PYTHON_TAG
    #PYTHONPATH=/opt/python/$MB_PYTHON_TAG/lib/python{PY_VER}/site-packages
    #PATH=/opt/python/$MB_PYTHON_TAG/bin:$PATH 
    #PYTHON_EXE=/opt/python/$MB_PYTHON_TAG/bin/python 

    source $VENV_DIR/bin/activate 
    pip install scikit-build cmake ninja
    pip install auditwheel 

    cd /io
    python setup.py bdist_wheel

    chmod -R o+rw _skbuild
    chmod -R o+rw dist

    auditwheel repair dist/$NAME-$VERSION-$MB_PYTHON_TAG*.whl
    chmod -R o+rw wheelhouse
    chmod -R o+rw $NAME.egg-info
fi
