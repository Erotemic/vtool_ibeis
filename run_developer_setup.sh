#!/bin/bash
# Install dependency packages

#if [[ "$(which docker)" != "" ]]; then
#    echo "building with docker"
#    BDIST_FPATH=$(./run_multibuild.sh)
#    pip install $BDIST_FPATH
#else

pip install -r requirements.txt
# new pep makes this not always work
# pip install -e .

./clean.sh

python setup.py clean
python setup.py build_ext --inplace
python setup.py develop
pip install -e .

# Point to custom opencv
# python setup.py build_ext --inplace -- -DOpenCV_DIR=$HOME/code/opencv/build
# python setup.py develop -- -DOpenCV_DIR=$HOME/code/opencv/build
