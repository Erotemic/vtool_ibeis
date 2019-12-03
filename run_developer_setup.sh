#!/bin/bash
# Install dependency packages
pip install -r requirements.txt
# new pep makes this not always work
# pip install -e .
python setup.py build_ext --inplace
python setup.py develop
