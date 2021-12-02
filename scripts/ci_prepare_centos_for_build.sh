#!/bin/bash

set -ex

# Install Python package dependencies
python -m pip install -r requirements/build.txt

yum update

yum install -y eigen3 opencv opencv-devel opencv-python libgomp-devel pkgconfig
