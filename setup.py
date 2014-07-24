#!/usr/bin/env python2.7
from __future__ import absolute_import, division, print_function
from Cython.Build import cythonize
from setuptools import Extension
from Cython.Distutils import build_ext
import numpy as np

#extensions = [Extension('vtool/linalg_cython.pyx')]
#extensions = cythonize('vtool/*.pyx')

ext_modules = [
    Extension('linalg_cython', ['vtool/linalg_cython.pyx'],
              include_dirs=[np.get_include()])
]

#ext_modules = cythonize("vtool/linalg_cython.pyx")

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


INSTALL_REQUIRES = [
    'numpy >= 1.8.0',
    'functools32 >= 3.2.3-1',
    #'cv2',  # no pipi index
]

if __name__ == '__main__':
    from utool.util_setup import setuptools_setup
    setuptools_setup(
        setup_fpath=__file__,
        name='vtool',
        ext_modules=ext_modules,
        cmdclass={'build_ext': build_ext},
        description=('Vision tools - tools for computer vision'),
        url='https://github.com/Erotemic/vtool',
        author='Jon Crall',
        author_email='erotemic@gmail.com',
        keywords='',
        install_requires=INSTALL_REQUIRES,
        package_data={},
        classifiers=[],
    )
