#!/usr/bin/env python
#!/usr/bin/env python
"""
Create a base docker image for building pyflann_ibeis

References:
    https://github.com/skvark/opencv-python
"""
from __future__ import absolute_import, division, print_function
from os.path import exists
from os.path import join
from os.path import realpath
import ubelt as ub
import sys
import os


def build_opencv_cmake_args(config):
    """
    Create cmake configuration args for opencv depending on the target platform

    References:
        https://github.com/skvark/opencv-python/blob/master/setup.py

    Ignore:
        config = {
            'build_contrib': True,
            'python_args': {
                'py_executable': '${PYTHON_EXE}',
                'py_ver': '3.6',
            },
            'linux_jpeg_args': {
                'jpeg_include_dir': '${JPEG_INCLUDE_DIR}',
                'jpeg_library': '${JPEG_LIBRARY}',
            }
        }
        build_opencv_cmake_args(config)
    """
    DEFAULT_CONFIG = True
    if DEFAULT_CONFIG:
        default_config = {
            'is_64bit': sys.maxsize > 2 ** 32,
            'sys_plat': sys.platform,
            'build_contrib': False,
            'build_headless': True,
            'python_args': {
                'py_ver': '{}.{}'.format(sys.version_info[0], sys.version_info[1]),
                'py_executable': sys.executable,
            },
            'linux_jpeg_args': None
        }
        if all(v in os.environ for v in ('JPEG_INCLUDE_DIR', 'JPEG_LIBRARY')):
            default_config['linux_jpeg_args'] = {
                'jpeg_include_dir': os.environ['JPEG_INCLUDE_DIR'],
                'jpeg_library': os.environ['JPEG_LIBRARY'],
            }
        unknown_ops = set(config) - set(default_config)
        assert not unknown_ops
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

    WIN32 = config['sys_plat'] == 'win32'
    DARWIN = config['sys_plat'] == 'darwin'
    LINUX = config['sys_plat'].startswith('linux')

    if WIN32:
        generator = "Visual Studio 14" + (" Win64" if config['is_64bit'] else '')
    else:
        generator = 'Unix Makefiles'

    cmake_args = [
        '-G', '"{}"'.format(generator),
        # See opencv/CMakeLists.txt for options and defaults
        "-DBUILD_opencv_apps=OFF",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TESTS=OFF",
        "-DBUILD_PERF_TESTS=OFF",
        "-DBUILD_DOCS=OFF"
    ]
    if config['python_args'] is not None:
        py_config = config['python_args']
        PY_MAJOR = py_config['py_ver'][0]
        cmake_args += [
            # skbuild inserts PYTHON_* vars. That doesn't satisfy opencv build scripts in case of Py3
            "-DPYTHON{}_EXECUTABLE={}".format(PY_MAJOR, py_config['py_executable']),
            "-DBUILD_opencv_python{}=ON".format(PY_MAJOR),

            # When off, adds __init__.py and a few more helper .py's. We use
            # our own helper files with a different structure.
            "-DOPENCV_SKIP_PYTHON_LOADER=ON",
            # Relative dir to install the built module to in the build tree.
            # The default is generated from sysconfig, we'd rather have a constant for simplicity
            "-DOPENCV_PYTHON{}_INSTALL_PATH=python".format(PY_MAJOR),
            # Otherwise, opencv scripts would want to install `.pyd' right into site-packages,
            # and skbuild bails out on seeing that
            "-DINSTALL_CREATE_DISTRIB=ON",
        ]

    if config['build_contrib']:
        # TODO: need to know abspath
        root = '.'
        cmake_args += [
            "-DOPENCV_EXTRA_MODULES_PATH=" + join(root, "opencv_contrib/modules")
        ]

    if config['build_headless']:
        # it seems that cocoa cannot be disabled so on macOS the package is not truly headless
        cmake_args.append("-DWITH_WIN32UI=OFF")
        cmake_args.append("-DWITH_QT=OFF")
    else:
        if DARWIN or LINUX:
            cmake_args.append("-DWITH_QT=4")

    if LINUX:
        cmake_args.append("-DWITH_V4L=ON")
        cmake_args.append("-DENABLE_PRECOMPILED_HEADERS=OFF")

        # tests fail with IPP compiled with
        # devtoolset-2 GCC 4.8.2 or vanilla GCC 4.9.4
        # see https://github.com/skvark/opencv-python/issues/138
        cmake_args.append("-DWITH_IPP=OFF")
        if not config['is_64bit']:
            cmake_args.append("-DCMAKE_CXX_FLAGS=-U__STRICT_ANSI__")

        if config['linux_jpeg_args'] is not None:
            jpeg_config = config['linux_jpeg_args']
            cmake_args += [
                "-DBUILD_JPEG=OFF",
                "-DJPEG_INCLUDE_DIR=" + jpeg_config['jpeg_include_dir'],
                "-DJPEG_LIBRARY=" + jpeg_config['jpeg_library'],
            ]

    # Fixes for macOS builds
    if DARWIN:
        # Some OSX LAPACK fns are incompatible, see
        # https://github.com/skvark/opencv-python/issues/21
        cmake_args.append("-DWITH_LAPACK=OFF")
        cmake_args.append("-DCMAKE_CXX_FLAGS=-stdlib=libc++")
        cmake_args.append("-DCMAKE_OSX_DEPLOYMENT_TARGET:STRING=10.7")

    return cmake_args


# def main():
#     """
#     Usage:
#         cd ~/code/hesaff/factory
#         python ~/code/hesaff/factory/build_opencv_docker.py --publish --no-exec
#         python ~/code/hesaff/factory/build_opencv_docker.py --publish
#     """
#     import multiprocessing

#     def argval(clikey, envkey=None, default=ub.NoParam):
#         if envkey is not None:
#             envval = os.environ.get(envkey)
#             if envval:
#                 default = envval
#         return ub.argval(clikey, default=default)

#     DEFAULT_PY_VER = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
#     DPATH = argval('--dpath', None, default=os.getcwd())
#     MAKE_CPUS = argval('--make_cpus', 'MAKE_CPUS', multiprocessing.cpu_count() + 1)
#     UNICODE_WIDTH = argval('--unicode_width', 'UNICODE_WIDTH', '32')
#     EXEC = not ub.argflag('--no-exec')

#     if ub.argflag('--publish'):
#         fpaths = []
#         plat = ['i686', 'x86_64']
#         pyver = ['2.7', '3.4', '3.5', '3.6', '3.7']
#         for PLAT in plat:
#             for PY_VER in pyver:
#                 fpaths += [build(DPATH, MAKE_CPUS, UNICODE_WIDTH, PLAT, PY_VER, EXEC=EXEC)]

#         print("WROTE TO: ")
#         print('\n'.join(fpaths))
#     else:
#         PY_VER = argval('--pyver', 'MB_PYTHON_VERSION', default=DEFAULT_PY_VER)
#         PLAT = argval('--plat', 'PLAT', default='x86_64')
#         build(DPATH, MAKE_CPUS, UNICODE_WIDTH, PLAT, PY_VER, EXEC=EXEC)


def main():
    ROOT = join(os.getcwd())
    # ROOT = '.'
    os.chdir(ROOT)

    # NAME = 'vtool'
    # VERSION = '0.1.0'
    # DOCKER_TAG = '{}-{}'.format(NAME, VERSION )

    QUAY_REPO = 'quay.io/erotemic/manylinux-for'

    # dockerfile_fpath = join(ROOT, 'Dockerfile')
    # This docker code is very specific for building linux binaries.
    # We will need to do a bit of refactoring to handle OSX and windows.
    # But the goal is to get at least one OS working end-to-end.

    import multiprocessing

    def argval(clikey, envkey=None, default=ub.NoParam):
        if envkey is not None:
            envval = os.environ.get(envkey)
            if envval:
                default = envval
        return ub.argval(clikey, default=default)

    # DPATH = argval('--dpath', None, default=os.getcwd())
    DPATH = argval('--dpath', None, default=ub.expandpath('~/code/vtool/dev/docker'))

    # DEFAULT_MB_PYTHON_TAG = '{}{}'.format(sys.version_info.major, sys.version_info.minor)
    # DEFAULT_MB_PYTHON_TAG = ub.import_module_from_path(ub.expandpath('~/code/vtool/setup.py'), 0).MB_PYTHON_TAG
    # DEFAULT_MB_PYTHON_TAG = None
    # MB_PYTHON_TAG = argval('--mb_python_tag', 'MB_PYTHON_TAG', default=DEFAULT_MB_PYTHON_TAG)

    MAKE_CPUS = argval('--make_cpus', 'MAKE_CPUS', multiprocessing.cpu_count() + 1)
    UNICODE_WIDTH = argval('--unicode_width', 'UNICODE_WIDTH', '32')
    PLAT = argval('--plat', 'PLAT', default='x86_64')

    OPENCV_VERSION = '4.1.0'

    dpath = realpath(ub.expandpath(DPATH))
    dpath = ub.ensuredir(dpath)
    os.chdir(dpath)

    BASE = 'manylinux1_{}'.format(PLAT)
    BASE_REPO = 'quay.io/skvark'

    # do we need the unicode width in this tag?
    DOCKER_TAG = '{}-opencv{}-v2'.format(PLAT, OPENCV_VERSION)
    DOCKER_URI = '{QUAY_REPO}:{DOCKER_TAG}'.format(**locals())

    if not exists(join(dpath, 'opencv-' + OPENCV_VERSION)):
        # FIXME: make robust in the case this fails
        print('downloading opencv')
        fpath = ub.grabdata(
            'https://github.com/opencv/opencv/archive/{}.zip'.format(OPENCV_VERSION),
            dpath=dpath, hash_prefix='1a00f2cdf2b1bd62e5a700a6f15026b2f2de9b1',
            hasher='sha512', verbose=3
        )
        ub.cmd('ln -s {} .'.format(fpath), cwd=dpath, verbose=0)
        ub.cmd('unzip {}'.format(fpath), cwd=dpath, verbose=0)

    dockerfile_fpath = join(dpath, 'Dockerfile_' + DOCKER_TAG)

    """
    Notes:
        docker run --rm -it quay.io/pypa/manylinux2010_x86_64 /bin/bash
        docker run -v $HOME/code/vtool/dev/docker:/root/vmnt --rm -it quay.io/skvark/manylinux1_x86_64 /bin/bash
    """
    docker_header = ub.codeblock(
        f'''
        FROM {BASE_REPO}/{BASE}
        # FROM quay.io/pypa/manylinux2010_x86_64
        # FROM quay.io/skvark/manylinux1_x86_64
        # RUN yum install lz4-devel -y

        RUN mkdir -p /root/code
        COPY opencv-{OPENCV_VERSION} /root/code/opencv

        ENV _MY_DOCKER_TAG={DOCKER_TAG}
        ENV HOME=/root
        ENV PLAT={PLAT}
        ENV UNICODE_WIDTH={UNICODE_WIDTH}
        ''')

    MB_PYTHON_TAGS = [
        'cp37-cp37m',
        'cp36-cp36m',
        'cp35-cp35m',
        'cp27-cp27mu',
    ]

    parts = [docker_header]

    for MB_PYTHON_TAG in MB_PYTHON_TAGS:
        parts.append(ub.codeblock(
            f'''
            RUN MB_PYTHON_TAG={MB_PYTHON_TAG} && \
                /opt/python/$MB_PYTHON_TAG/bin/python -m pip -q --no-cache-dir install setuptools pip virtualenv scikit-build cmake ninja ubelt numpy wheel -U && \
                /opt/python/$MB_PYTHON_TAG/bin/python -m virtualenv /root/venv-$MB_PYTHON_TAG
            '''))

    # only do this once
    MB_PYTHON_TAGS = MB_PYTHON_TAGS[0:1]
    for MB_PYTHON_TAG in MB_PYTHON_TAGS:
        major, minor = MB_PYTHON_TAG.replace('cp', '')[0:2]
        PY_VER = '{}.{}'.format(major, minor)

        config = {
            'is_64bit': PLAT in {'x86_64'},
            'build_contrib': False,
            'build_headless': True,
            'python_args': None,
            # 'python_args': {
            #     'py_ver': PY_VER,
            #     'py_executable': PY_VER,
            # },
            'linux_jpeg_args': {
                'jpeg_include_dir': '${JPEG_INCLUDE_DIR}',
                'jpeg_library': '${JPEG_LIBRARY}',
            }
        }
        CMAKE_ARGS = ' \\\n                '.join(build_opencv_cmake_args(config))

        parts.append(ub.codeblock(
            f'''
            RUN MB_PYTHON_TAG={MB_PYTHON_TAG} && \
                PYTHON_ROOT=/opt/python/{MB_PYTHON_TAG}/ \
                PYTHONPATH=/opt/python/{MB_PYTHON_TAG}/lib/python{PY_VER}/site-packages/ \
                PATH=/opt/python/{MB_PYTHON_TAG}/bin:$PATH \
                PYTHON_EXE=/opt/python/{MB_PYTHON_TAG}/bin/python \
                source /root/venv-$MB_PYTHON_TAG/bin/activate && \
                mkdir -p /root/code/opencv/build_{MB_PYTHON_TAG} && \
                cd /root/code/opencv/build_{MB_PYTHON_TAG} && \
                cmake {CMAKE_ARGS} /root/code/opencv && \
                cd /root/code/opencv/build_{MB_PYTHON_TAG} && \
                make -j{MAKE_CPUS} && \
                make install && \
                rm -rf /root/code/opencv/build_{MB_PYTHON_TAG}
            '''))

    # cmake {CMAKE_ARGS} -DCMAKE_INSTALL_PREFIX=/root/venv-$MB_PYTHON_TAG /root/code/opencv && \
    docker_code = '\n\n'.join(parts)

    try:
        print(ub.color_text('\n--- DOCKER CODE ---', 'white'))
        print(ub.highlight_code(docker_code, 'docker'))
        print(ub.color_text('--- END DOCKER CODE ---\n', 'white'))
    except Exception:
        pass
    with open(dockerfile_fpath, 'w') as file:
        file.write(docker_code)

    docker_build_cli = ' '.join([
        'docker', 'build',
        '--tag {}'.format(DOCKER_TAG),
        '-f {}'.format(dockerfile_fpath),
        '.'
    ])
    print('docker_build_cli = {!r}'.format(docker_build_cli))

    if 1:
        info = ub.cmd(docker_build_cli, verbose=3, shell=True)

        if info['ret'] != 0:
            print(ub.color_text('\n--- FAILURE ---', 'red'))
            print('Failed command:')
            print(info['command'])
            print(info['err'])
            print('NOTE: sometimes reruning the command manually works')
            raise Exception('Building docker failed with exit code {}'.format(info['ret']))
        else:
            print(ub.color_text('\n--- SUCCESS ---', 'green'))

        print(ub.highlight_code(ub.codeblock(
            f'''
            # Finished creating the docker image.
            # To test / export / publish you can do something like this:


            # Test that we can get a bash terminal
            docker run -it {DOCKER_TAG} bash

            docker save -o ${ROOT}/{DOCKER_TAG}.docker.tar {DOCKER_TAG}

            # To publish to quay

            source $(secret_loader.sh)
            echo "QUAY_USERNAME = $QUAY_USERNAME"
            docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io

            docker tag {DOCKER_TAG} {DOCKER_URI}
            docker push {DOCKER_URI}

            '''), 'bash'))
        # push_cmd = 'docker push quay.io/erotemic/manylinux-opencv:manylinux1_x86_64-opencv4.1.0-py3.6'
        # print('push_cmd = {!r}'.format(push_cmd))
        # print(push_cmd)

    PUBLISH = 0
    if PUBLISH:
        cmd1 = 'docker tag {DOCKER_TAG} {DOCKER_URI}'.format(**locals())
        cmd2 = 'docker push {DOCKER_URI}'.format(**locals())
        print('-- <push cmds> ---')
        print(cmd1)
        print(cmd2)
        print('-- </push cmds> ---')


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/vtool/dev/build_base_docker.py
    """
    main()
