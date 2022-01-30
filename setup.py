#!/usr/bin/env python
"""
pip install cibuildwheel
CIBW_SKIP='pp*' cibuildwheel --config-file pyproject.toml --platform linux --arch x86_64
"""
from __future__ import absolute_import, division, print_function
from os.path import dirname
from os.path import join
from os.path import sys
from os.path import exists
from setuptools import find_packages


def parse_version(fpath):
    """
    Statically parse the version number from a python file
    """
    import ast
    if not exists(fpath):
        try2 = join(dirname(__file__), fpath)
        if exists(try2):
            fpath = try2
        else:
            raise ValueError('fpath={!r} does not exist'.format(fpath))
    with open(fpath, 'r') as file_:
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


def native_mb_python_tag(plat_impl=None, version_info=None):
    """
    Example:
        >>> print(native_mb_python_tag())
        >>> print(native_mb_python_tag('PyPy', (2, 7)))
        >>> print(native_mb_python_tag('CPython', (3, 8)))
    """
    if plat_impl is None:
        import platform
        plat_impl = platform.python_implementation()

    if version_info is None:
        import sys
        version_info = sys.version_info

    major, minor = version_info[0:2]
    ver = '{}{}'.format(major, minor)

    if plat_impl == 'CPython':
        # TODO: get if cp27m or cp27mu
        impl = 'cp'
        if ver == '27':
            IS_27_BUILT_WITH_UNICODE = True  # how to determine this?
            if IS_27_BUILT_WITH_UNICODE:
                abi = 'mu'
            else:
                abi = 'm'
        else:
            if ver == '38':
                # no abi in 38?
                abi = ''
            else:
                abi = 'm'
        mb_tag = '{impl}{ver}-{impl}{ver}{abi}'.format(**locals())
    elif plat_impl == 'PyPy':
        abi = ''
        impl = 'pypy'
        ver = '{}{}'.format(major, minor)
        mb_tag = '{impl}-{ver}'.format(**locals())
    else:
        raise NotImplementedError(plat_impl)
    return mb_tag


def parse_description():
    """
    Parse the description in the README file

    CommandLine:
        pandoc --from=markdown --to=rst --output=README.rst README.md
        python -c "import setup; print(setup.parse_description())"
    """
    from os.path import dirname, join, exists
    readme_fpath = join(dirname(__file__), 'README.rst')
    # This breaks on pip install, so check that it exists.
    if exists(readme_fpath):
        with open(readme_fpath, 'r') as f:
            text = f.read()
        return text
    return ''


def parse_requirements(fname='requirements.txt', with_version=False):
    """
    Parse the package dependencies listed in a requirements file but strips
    specific versioning information.

    Args:
        fname (str): path to requirements file
        with_version (bool, default=False): if true include version specs

    Returns:
        List[str]: list of requirements items

    CommandLine:
        python -c "import setup; print(setup.parse_requirements())"
        python -c "import setup; print(chr(10).join(setup.parse_requirements(with_version=True)))"
    """
    from os.path import exists
    import re
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
        else:
            info = {'line': line}
            if line.startswith('-e '):
                info['package'] = line.split('#egg=')[1]
            else:
                # Remove versioning from the package
                pat = '(' + '|'.join(['>=', '==', '>']) + ')'
                parts = re.split(pat, line, maxsplit=1)
                parts = [p.strip() for p in parts]

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

    def gen_packages_items():
        if exists(require_fpath):
            for info in parse_require_file(require_fpath):
                parts = [info['package']]
                if with_version and 'version' in info:
                    parts.extend(info['version'])
                if not sys.version.startswith('3.4'):
                    # apparently package_deps are broken in 3.4
                    platform_deps = info.get('platform_deps')
                    if platform_deps is not None:
                        parts.append(';' + platform_deps)
                item = ''.join(parts)
                yield item

    packages = list(gen_packages_items())
    return packages

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


NAME = 'vtool_ibeis'
MB_PYTHON_TAG = native_mb_python_tag()  # NOQA
VERSION = parse_version('vtool_ibeis/__init__.py')

KWARGS = dict(
    name='vtool_ibeis',
    version=VERSION,
    author=', '.join(AUTHORS),
    description='vision tools',
    long_description=parse_description(),
    long_description_content_type='text/x-rst',
    author_email='erotemic@gmail.com',
    url='https://github.com/Erotemic/vtool_ibeis',
    license='Apache 2',
    # List of classifiers available at:
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',  # Interpret as Apache License v2.0
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
        # Really annoying that this is the best we can do
        # The user *must* choose either headless or graphics
        # to get a complete working install.
        'headless': parse_requirements('requirements/headless.txt'),
        'graphics': parse_requirements('requirements/graphics.txt'),
    },
    packages=find_packages(),
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
    import sysconfig
    import os
    try:
        soconfig = sysconfig.get_config_var('EXT_SUFFIX')
    except Exception:
        soconfig = sysconfig.get_config_var('SO')

    def get_lib_ext():
        if sys.platform.startswith('win32'):
            ext = '.dll'
        elif sys.platform.startswith('darwin'):
            ext = '.dylib'
        elif sys.platform.startswith('linux'):
            ext = '.so'
        else:
            raise Exception('Unknown operating system: %s' % sys.platform)
        return ext

    libext = get_lib_ext()
    _pyver = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
    hack_libconfig = '-{}{}'.format(_pyver, libext)

    PACKAGE_DATA = (
            ['*%s' % soconfig] +
            ['*%s' % hack_libconfig] +
            ['*%s' % libext] +
            (['*.dll'] if os.name == 'nt' else []) +
            (['Release\\*.dll'] if os.name == 'nt' else [])
            # ["LICENSE.txt", "LICENSE-3RD-PARTY.txt", "LICENSE.SIFT"]
    )
    KWARGS.update(dict(
        ext_modules=EmptyListWithLength(),  # hack for including ctypes bins
        include_package_data=True,
        package_data={
            KWARGS['name']: PACKAGE_DATA,
        },
    ))

    if '--universal' in sys.argv:
        if 'develop' in sys.argv:
            sys.argv.remove('--universal')
        from setuptools import setup
        setup(**KWARGS)
    else:
        from skbuild import setup
        setup(**KWARGS)
