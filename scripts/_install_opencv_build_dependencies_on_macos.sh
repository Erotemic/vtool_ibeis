#!/bin/bash
################################
# Install OpenCV dependencies

set -ex

brew install pkg-config
brew install jpeg libpng libtiff openexr
brew install eigen tbb
#: to acquire the source
brew install git
#: needed for python3 bindings
python -m pip install numpy
