#!/usr/bin/env python
"""
An Ode to Python Packaging:

Oh Python Packaging, when will you get better?
You've already improved so much...
but, lets say, there's still a lot of room for improvement.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import skbuild as skb
from os.path import dirname  # NOQA


def parse_version(package):
    """
    Statically parse the version number from __init__.py

    CommandLine:
        python -c "import setup; print(setup.parse_version('vtool'))"
    """
    from os.path import join, exists
    import ast

    # Check if the package is a single-file or multi-file package
    _candiates = [
        join(dirname(__file__), package + '.py'),
        join(dirname(__file__), package, '__init__.py'),
    ]
    _found = [init_fpath for init_fpath in _candiates if exists(init_fpath)]
    if len(_found) > 0:
        init_fpath = _found[0]
    elif len(_found) > 1:
        raise Exception('parse_version found multiple init files')
    elif len(_found) == 0:
        raise Exception('Cannot find package init file')

    with open(init_fpath) as file_:
        sourcecode = file_.read()
    pt = ast.parse(sourcecode)
    class VersionVisitor(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if getattr(target, 'id', None) == '__version__':
                    self.version = node.value.s
    visitor = VersionVisitor()
    visitor.visit(pt)
    return visitor.version


def native_mb_python_tag():
    import sys
    import platform
    major = sys.version_info[0]
    minor = sys.version_info[1]
    ver = '{}{}'.format(major, minor)
    if platform.python_implementation() == 'CPython':
        # TODO: get if cp27m or cp27mu
        impl = 'cp'
        if ver == '27':
            IS_27_BUILT_WITH_UNICODE = True  # how to determine this?
            if IS_27_BUILT_WITH_UNICODE:
                abi = 'mu'
            else:
                abi = 'm'
        else:
            abi = 'm'
    else:
        raise NotImplementedError(impl)
    mb_tag = '{impl}{ver}-{impl}{ver}{abi}'.format(**locals())
    return mb_tag


def parse_requirements(fname='requirements.txt'):
    """
    Parse the package dependencies listed in a requirements file but
    strips specific versioning information.

    TODO:
        perhaps use https://github.com/davidfischer/requirements-parser instead

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
    """
    from os.path import exists
    import re
    import sys
    require_fpath = fname

    def parse_line(line):
        """
        Parse information from a line in a requirements text file
        """
        if line.startswith('-r '):
            # Allow specifying requirements in other files
            target = line.split(' ')[1]
            for info in parse_require_file(target):
                yield info
        elif line.startswith('-e '):
            info = {}
            info['package'] = line.split('#egg=')[1]
            yield info
        else:
            # Remove versioning from the package
            pat = '(' + '|'.join(['>=', '==', '>']) + ')'
            parts = re.split(pat, line, maxsplit=1)
            parts = [p.strip() for p in parts]

            info = {}
            info['package'] = parts[0]
            if len(parts) > 1:
                op, rest = parts[1:]
                if ';' in rest:
                    # Handle platform specific dependencies
                    # http://setuptools.readthedocs.io/en/latest/setuptools.html#declaring-platform-specific-dependencies
                    version, platform_deps = map(str.strip, rest.split(';'))
                    info['platform_deps'] = platform_deps
                else:
                    version = rest  # NOQA
                info['version'] = (op, version)
            yield info

    def parse_require_file(fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    for info in parse_line(line):
                        yield info

    # This breaks on pip install, so check that it exists.
    packages = []
    if exists(require_fpath):
        for info in parse_require_file(require_fpath):
            package = info['package']
            if not sys.version.startswith('3.4'):
                # apparently package_deps are broken in 3.4
                platform_deps = info.get('platform_deps')
                if platform_deps is not None:
                    package += ';' + platform_deps
            packages.append(package)
    return packages

# TODO: Push for merger of PR adding templatable utilities to skb.utils
from setuptools import find_packages
skb.utils.find_packages = find_packages
skb.utils.parse_version = parse_version
skb.utils.parse_requirements = parse_requirements
_ = skb.utils.CLASSIFIER_STATUS_OPTIONS = {
    '1': 'Development Status :: 1 - Planning',
    '2': 'Development Status :: 2 - Pre-Alpha',
    '3': 'Development Status :: 3 - Alpha',
    '4': 'Development Status :: 4 - Beta',
    '5': 'Development Status :: 5 - Production/Stable',
    '6': 'Development Status :: 6 - Mature',
    '7': 'Development Status :: 7 - Inactive',
}
_.update({
    'planning': _['1'],
    'pre-alpha': _['2'],
    'alpha': _['3'],
    'beta': _['4'],
    'stable': _['5'],
    'mature': _['6'],
    'inactive': _['7'],
})

_ = skb.utils.CLASSIFIER_LICENSE_OPTIONS = {
    'apache': 'License :: OSI Approved :: Apache Software License',
}
del _


VERSION = parse_version('vtool')

"""
TODO: automate with some modified version of: git shortlog -s | cut -c8-
TODO: maintain contributors file
"""
AUTHORS = [
    'Avi Weinstock',
    'Chuck Stewart',
    'Hendrik Weideman'
    'Jason Parham'
    'Jon Crall'
    'Zackary Rutfield'
]


NAME = 'vtool'
MB_PYTHON_TAG = native_mb_python_tag()  # NOQA
# VERSION = parse_version()

KWARGS = dict(
    name='vtool',
    version=VERSION,
    author=', '.join(AUTHORS),
    description='vision tools',
    # long_description=parse_description(),
    long_description_content_type='text/x-rst',
    author_email='erotemic@gmail.com',
    url='https://github.com/Erotemic/vtool',
    license='Apache 2',
    # List of classifiers available at:
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        skb.utils.CLASSIFIER_STATUS_OPTIONS['beta'],
        skb.utils.CLASSIFIER_LICENSE_OPTIONS['apache'],  # Interpret as Apache License v2.0
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=parse_requirements('requirements/runtime.txt'),
    extras_require={
        'all': parse_requirements('requirements.txt'),
        'tests': parse_requirements('requirements/tests.txt'),
        'build': parse_requirements('requirements/build.txt'),
        'runtime': parse_requirements('requirements/runtime.txt'),
    },
    packages=skb.utils.find_packages(),
)


try:
    class EmptyListWithLength(list):
        def __len__(self):
            return 1
except Exception:
    raise RuntimeError('FAILED TO ADD BUILD CONSTRUCTS')


if __name__ == '__main__':
    """
    CommandLine:
        xdoctest -m setup
    """
    skb.setup(**KWARGS)


# DEV_REQUIREMENTS = [
#     'atlas',
# ]

# TEST_APT_REQUIRES = [
#     #sudo apt-get install libjpeg-turbo8-dev
#     'lcms2-dev'  # sudo apt-get install liblcms2-dev
# ]

# TEST_PIP_REQUIRES = [
#     'smc.freeimage',  # sudo pip install smc.freeimage
# ]

# CLUTTER_PATTERNS = [
#     'libsver.*'
# ]

# if six.PY2:
#     INSTALL_REQUIRES += ['functools32 >= 3.2.3-1']

# kwargs = util_setup.setuptools_setup(
#     setup_fpath=__file__,
#     name='vtool',
#     packages=util_setup.find_packages(),
#     version=parse_version(),
#     license=util_setup.read_license('LICENSE'),
#     long_description=util_setup.parse_readme('README.md'),
#     ext_modules=util_setup.find_ext_modules(),
#     cmdclass=util_setup.get_cmdclass(),
#     description=('Vision tools - tools for computer vision'),
#     url='https://github.com/Erotemic/vtool',
#     author='Jon Crall',
#     author_email='erotemic@gmail.com',
#     keywords='',
#     install_requires=INSTALL_REQUIRES,
#     clutter_patterns=CLUTTER_PATTERNS,
#     # package_data={'build': ut.get_dynamic_lib_globstrs()},
#     # build_command=lambda: ut.Repo(dirname(__file__)),
#     build_command=lambda: ut.std_build_command(),
#     classifiers=[],
# )
# setup(**kwargs)
