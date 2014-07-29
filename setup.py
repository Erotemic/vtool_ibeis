#!/usr/bin/env python2.7
from __future__ import absolute_import, division, print_function
#from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import setup
import utool

#extensions = [Extension('vtool/linalg_cython.pyx')]
#extensions = cythonize('vtool/*.pyx')
#[
#    Extension('vtool.linalg_cython', ['vtool/linalg_cython.pyx'],
#              include_dirs=[np.get_include()])
#]
r'''
set PATH=%HOME%\code\utool\utool\util_scripts;%PATH%
cyth.py vtool\linalg_cython.pyx
cd %HOME%\code\vtool
python %HOME%/code/vtool/vtool/tests/test_linalg.py
ls vtool/*_cython*
python setup.py build_ext --inplace && python vtool/tests/test_linalg.py
python
python -c "import utool; utool.checkpath('vtool/linalg_cython.pyd', verbose=True)"
cyth.py %HOME%/code/vtool/vtool/linalg_cython.pyx
'''
#ext_modules = cythonize("vtool/linalg_cython.pyx")

ext_modules = utool.find_ext_modules()


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

import six


INSTALL_REQUIRES = [
    'Cython >= 0.20.2',
    'numpy >= 1.8.0',
    #'cv2',  # no pipi index
]

if six.PY2:
    INSTALL_REQUIRES += ['functools32 >= 3.2.3-1']

if __name__ == '__main__':
    from utool.util_setup import setuptools_setup

    #python -c "import pyximport; pyximport.install(reload_support=True, setup_args={'script_args': ['--compiler=mingw32']})"

    kwargs = setuptools_setup(
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
    setup(**kwargs)
