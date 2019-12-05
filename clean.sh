#!/bin/bash


rm -rf _skbuild
rm -rf vtool_ibeis/lib
rm -rf vtool_ibeis/*.so
rm -rf dist
rm -rf build
rm -rf vtool_ibeis.egg-info

rm -rf mb_work
rm -rf wheelhouse

CLEAN_PYTHON='find . -regex ".*\(__pycache__\|\.py[co]\)" -delete || find . -iname *.pyc -delete || find . -iname *.pyo -delete'
bash -c "$CLEAN_PYTHON"
