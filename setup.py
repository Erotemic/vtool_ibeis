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
    import vtool
    setuptools_setup(
        setup_fpath=__file__,
        module=vtool,
        description=('Vision tools - tools for computer vision'),
        url='https://github.com/Erotemic/vtool',
        author='Jon Crall',
        author_email='erotemic@gmail.com',
        keywords='',
        package_data={},
        classifiers=[],
    )
