#!/bin/bash

set -ex

export CUR_LOC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

pip install -r requirements/build.txt

brew install \
    pkg-config \
    eigen \
    opencv \
    libomp

python setup.py build_ext --inplace
