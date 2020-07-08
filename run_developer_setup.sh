#!/bin/bash

./clean.sh
python setup.py clean

pip install -r requirements.txt

python setup.py build_ext --inplace
python setup.py develop

pip install -e .

# Point to custom opencv
# python setup.py build_ext --inplace -- -DOpenCV_DIR=$HOME/code/opencv/build
# python setup.py develop -- -DOpenCV_DIR=$HOME/code/opencv/build
