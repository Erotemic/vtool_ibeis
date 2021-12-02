#!/bin/bash

set -ex

pip install -r requirements/build.txt

brew update

brew install \
    pkg-config \
    eigen \
    opencv \
    libomp
