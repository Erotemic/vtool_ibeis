#!/usr/bin/env python
from __future__ import absolute_import, division, print_function


CYTHON_FILES = [
    'vtool/chip.py',
    'vtool/image.py',
    'vtool/exif.py',
    'vtool/histogram.py',
    'vtool/ellipse.py',
    'vtool/keypoint.py',
    'vtool/linalg.py',
    'vtool/math.py',
    'vtool/patch.py',
    'vtool/segmentation.py',
    'vtool/spatial_verification.py',
]

if __name__ == '__main__':
    from utool.util_setup import setuptools_setup
    setuptools_setup(
        setup_fpath=__file__,
        package_name='vtool',
        version='1.0.0.dev1',
        description=('Vision tools - tools for computer vision'),
        url='https://github.com/Erotemic/vtool',
        author='Jon Crall',
        author_email='erotemic@gmail.com',
        keywords='',
        package_data={},
        classifiers=[],
    )
