#!/bin/bash
# Install dependency packages
pip install -r requirements.txt
# new pep makes this not always work
# pip install -e .

python setup.py build_ext --inplace -- -DOpenCV_DIR=$HOME/code/opencv/build
python setup.py develop -- -DOpenCV_DIR=$HOME/code/opencv/build

# Point to custom opencv
_note="""
python setup.py build_ext --inplace -- -DOpenCV_DIR=$HOME/code/opencv/build
python setup.py develop -- -DOpenCV_DIR=$HOME/code/opencv/build
"""
