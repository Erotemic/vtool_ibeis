#!/usr/bin/env python2.7
"""
FIXME:
    incoporate unix_build / mingw_build into this script
    ensure libsver.so installs correctly

CommandLine:
    python -c "import utool, vtool; utool.checkpath(vtool.__file__, verbose=True)"
    python -c "import utool, vtool; utool.checkpath(utool.unixjoin(utool.get_module_dir(vtool), 'libsver.so'), verbose=True)"
"""
from __future__ import absolute_import, division, print_function
from setuptools import setup
from utool import util_setup
import utool as ut
from os.path import dirname
import six

#import cyth

#cyth.translate('vtool/keypoint.py')
#cyth.translate('vtool/keypoint.py', 'vtool/spatial_verification.py')


INSTALL_REQUIRES = [
    'Cython >= 0.21.1',
    'numpy >= 1.9.0',
    'scipy >= .15.0',
    'scikit-learn >= 0.16.1',
    'statsmodels >= 0.6.1',
    #'cv2',  # no pipi index
]

CLUTTER_PATTERNS = [
    'libsver.*'
]

if six.PY2:
    INSTALL_REQUIRES += ['functools32 >= 3.2.3-1']

if __name__ == '__main__':
    kwargs = util_setup.setuptools_setup(
        setup_fpath=__file__,
        name='vtool',
        packages=util_setup.find_packages(),
        version=util_setup.parse_package_for_version('vtool'),
        license=util_setup.read_license('LICENSE'),
        long_description=util_setup.parse_readme('README.md'),
        ext_modules=util_setup.find_ext_modules(),
        cmdclass=util_setup.get_cmdclass(),
        description=('Vision tools - tools for computer vision'),
        url='https://github.com/Erotemic/vtool',
        author='Jon Crall',
        author_email='erotemic@gmail.com',
        keywords='',
        install_requires=INSTALL_REQUIRES,
        clutter_patterns=CLUTTER_PATTERNS,
        package_data={'build': ut.get_dynamic_lib_globstrs()},
        build_command=lambda: ut.std_build_command(dirname(__file__)),
        classifiers=[],
    )
    setup(**kwargs)

#from Cython.Build import cythonize
#from Cython.Distutils import build_ext

#python -c "import pyximport; pyximport.install(reload_support=True, setup_args={'script_args': ['--compiler=mingw32']})"

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
