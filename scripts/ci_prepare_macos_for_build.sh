#!/bin/bash

set -ex

# See https://stackoverflow.com/a/246128/176882
export CUR_LOC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Install Python package dependencies
python -m pip install -r requirements/build.txt

$CUR_LOC/_install_opencv_build_dependencies_macports_on_macos.sh

$CUR_LOC/_install_opencv_build_software_on_macos.sh
