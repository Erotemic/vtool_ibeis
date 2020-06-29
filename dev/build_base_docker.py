#!/usr/bin/env python
"""
Create a base docker image for building pyflann

References:
    https://github.com/skvark/opencv-python

    # Files skvark uses to make his base opencv docker image
    https://github.com/skvark/opencv-python/blob/master/docker/Dockerfile_i686
    https://github.com/skvark/opencv-python/blob/master/docker/Dockerfile_x86_64
"""
from __future__ import absolute_import, division, print_function
from os.path import basename
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
            'linux_jpeg_args': None,
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
        generator = 'Visual Studio 14' + (' Win64' if config['is_64bit'] else '')
    else:
        generator = 'Unix Makefiles'

    cmake_args = [
        '-G',
        '"{}"'.format(generator),
        # See opencv/CMakeLists.txt for options and defaults
        '-DBUILD_opencv_apps=OFF',
        '-DBUILD_SHARED_LIBS=OFF',
        '-DBUILD_TESTS=OFF',
        '-DBUILD_PERF_TESTS=OFF',
        '-DBUILD_DOCS=OFF',
    ]
    if config['python_args'] is not None:
        py_config = config['python_args']
        PY_MAJOR = py_config['py_ver'][0]
        cmake_args += [
            # skbuild inserts PYTHON_* vars. That doesn't satisfy opencv build scripts in case of Py3
            '-DPYTHON{}_EXECUTABLE={}'.format(PY_MAJOR, py_config['py_executable']),
            '-DBUILD_opencv_python{}=ON'.format(PY_MAJOR),
            # When off, adds __init__.py and a few more helper .py's. We use
            # our own helper files with a different structure.
            '-DOPENCV_SKIP_PYTHON_LOADER=ON',
            # Relative dir to install the built module to in the build tree.
            # The default is generated from sysconfig, we'd rather have a constant for simplicity
            '-DOPENCV_PYTHON{}_INSTALL_PATH=python'.format(PY_MAJOR),
            # Otherwise, opencv scripts would want to install `.pyd' right into site-packages,
            # and skbuild bails out on seeing that
            '-DINSTALL_CREATE_DISTRIB=ON',
        ]

    if config['build_contrib']:
        # TODO: need to know abspath
        root = '.'
        cmake_args += [
            '-DOPENCV_EXTRA_MODULES_PATH=' + join(root, 'opencv_contrib/modules')
        ]

    if config['build_headless']:
        # it seems that cocoa cannot be disabled so on macOS the package is not truly headless
        cmake_args.append('-DWITH_WIN32UI=OFF')
        cmake_args.append('-DWITH_QT=OFF')
    else:
        if DARWIN or LINUX:
            cmake_args.append('-DWITH_QT=4')

    if LINUX:
        cmake_args.append('-DWITH_V4L=ON')
        cmake_args.append('-DENABLE_PRECOMPILED_HEADERS=OFF')

        # tests fail with IPP compiled with
        # devtoolset-2 GCC 4.8.2 or vanilla GCC 4.9.4
        # see https://github.com/skvark/opencv-python/issues/138
        cmake_args.append('-DWITH_IPP=OFF')
        if not config['is_64bit']:
            cmake_args.append('-DCMAKE_CXX_FLAGS=-U__STRICT_ANSI__')

        if config['linux_jpeg_args'] is not None:
            jpeg_config = config['linux_jpeg_args']
            cmake_args += [
                '-DBUILD_JPEG=OFF',
                '-DJPEG_INCLUDE_DIR=' + jpeg_config['jpeg_include_dir'],
                '-DJPEG_LIBRARY=' + jpeg_config['jpeg_library'],
            ]

    # Fixes for macOS builds
    if DARWIN:
        # Some OSX LAPACK fns are incompatible, see
        # https://github.com/skvark/opencv-python/issues/21
        cmake_args.append('-DWITH_LAPACK=OFF')
        cmake_args.append('-DCMAKE_CXX_FLAGS=-stdlib=libc++')
        cmake_args.append('-DCMAKE_OSX_DEPLOYMENT_TARGET:STRING=10.7')

    return cmake_args


def main():
    QUAY_REPO = 'quay.io/erotemic/manylinux-for'

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

    default_dpath = ub.get_app_cache_dir('erotemic/manylinux-for/staging')
    DPATH = argval('--dpath', None, default=default_dpath)

    MAKE_CPUS = argval('--make_cpus', 'MAKE_CPUS', multiprocessing.cpu_count() + 1)

    PLAT = argval('--plat', 'PLAT', default='x86_64')

    OPENCV_VERSION = '4.1.0'

    DRY = ub.argflag('--dry')

    dpath = realpath(ub.expandpath(DPATH))
    dpath = ub.ensuredir(dpath)
    os.chdir(dpath)

    # BASE_REPO = 'quay.io/skvark'
    # BASE = 'manylinux1_{}'.format(PLAT)

    BASE_REPO = 'quay.io/pypa'
    BASE = 'manylinux2010_{}'.format(PLAT)

    if PLAT in ['aarch64', 's390x', 'ppc64le']:
        BASE = 'manylinux2014_{}'.format(PLAT)

    # do we need the unicode width in this tag?
    DOCKER_TAG = '{}-opencv{}-v4'.format(PLAT, OPENCV_VERSION)
    DOCKER_URI = '{QUAY_REPO}:{DOCKER_TAG}'.format(**locals())

    if not exists(join(dpath, 'opencv-' + OPENCV_VERSION)):
        # FIXME: make robust in the case this fails
        print('downloading opencv')
        fpath = ub.grabdata(
            'https://github.com/opencv/opencv/archive/{}.zip'.format(OPENCV_VERSION),
            dpath=dpath,
            hash_prefix='1a00f2cdf2b1bd62e5a700a6f15026b2f2de9b1',
            hasher='sha512',
            verbose=3,
        )
        ub.cmd('ln -s {} .'.format(fpath), cwd=dpath, verbose=0)
        ub.cmd('unzip {}'.format(fpath), cwd=dpath, verbose=0)

    dockerfile_fpath = join(dpath, 'Dockerfile_' + DOCKER_TAG)

    PARENT_IMAGE = f'{BASE_REPO}/{BASE}'

    docker_header = ub.codeblock(
        f"""
        FROM {PARENT_IMAGE}

        RUN yum install lz4-devel zlib-devel -y

        RUN mkdir -p /root/code
        COPY opencv-{OPENCV_VERSION} /root/code/opencv

        ENV _MY_DOCKER_TAG={DOCKER_TAG}
        ENV HOME=/root
        ENV PLAT={PLAT}
        """
    )

    MB_PYTHON_TAGS = [
        'cp38-cp38',
        'cp37-cp37m',
        'cp36-cp36m',
        'cp35-cp35m',
        'cp27-cp27mu',
    ]

    parts = [docker_header]

    # if PLAT != 'x86_64':
    if True:
        # For architectures other than x86_64 we have to build cmake ourselves
        fpath = ub.grabdata(
            'https://github.com/Kitware/CMake/releases/download/v3.15.6/cmake-3.15.6.tar.gz',
            dpath=dpath,
            hash_prefix='3210cbf4644a7cb8d08ad752a0b550d864666b0',
            hasher='sha512',
            verbose=3,
        )
        cmake_tar_fname = basename(fpath)

        # manylinux1 provides curl-devel equivalent and libcurl statically linked
        # against the same newer OpenSSL as other source-built tools
        # (1.0.2s as of this writing)

        # Alternate way to grab data and check the sha512sum
        # curl -O -L https://github.com/Kitware/CMake/releases/download/v3.15.6/cmake-3.15.6.tar.gz
        # sha512sum cmake-3.15.6.tar.gz | grep '^3210cbf4644a7cb8d08ad752'

        parts.append(
            ub.codeblock(
                fr"""

            RUN yum install curl-devel -y

            COPY {cmake_tar_fname} /root/code/

            RUN \
                mkdir -p /root/code/ && \
                cd /root/code/ && \
                tar -xf cmake-3.15.6.tar.gz && \
                cd cmake-3.15.6 && \
                export MAKEFLAGS=-j$(getconf _NPROCESSORS_ONLN) && \
                ./configure --system-curl && \
                make && \
                make install && \
                cd .. && \
                rm -rf cmake-*
            """
            )
        )

    # note: perl build scripts does a lot of redundant work
    # if running "make install" separately
    parts.append(
        ub.codeblock(
            r"""
        RUN yum install freetype-devel bzip2-devel zlib-devel -y && \
            mkdir -p ~/ffmpeg_sources

        # Newer openssl configure requires newer perl
        RUN cd ~/ffmpeg_sources && \
            curl -O -L https://www.cpan.org/src/5.0/perl-5.20.1.tar.gz && \
            tar -xf perl-5.20.1.tar.gz && \
            cd ~/ffmpeg_sources/perl-5.20.1 && \
            ./Configure -des -Dprefix="$HOME/openssl_build" && \
            make install -j$(getconf _NPROCESSORS_ONLN) && \
            cd ~/ffmpeg_sources && \
            rm -rf perl-5.20.1*
        """
        )
    )

    if PLAT == 'i686':
        parts.append(
            ub.codeblock(
                r"""
            RUN cd ~/ffmpeg_sources && \
                curl -O -L https://github.com/openssl/openssl/archive/OpenSSL_1_1_1c.tar.gz && \
                tar -xf OpenSSL_1_1_1c.tar.gz && \
                cd ~/ffmpeg_sources/openssl-OpenSSL_1_1_1c && \
                #in i686, ./config detects x64 in i686 container without linux32
                # when run from "docker build"
                PERL="$HOME/openssl_build/bin/perl" linux32 ./config --prefix="$HOME/ffmpeg_build" --openssldir="$HOME/ffmpeg_build" shared zlib && \
                make -j$(getconf _NPROCESSORS_ONLN) && \
                make install_sw && \
                rm -rf ~/openssl_build
            """
            )
        )
    else:
        parts.append(
            ub.codeblock(
                r"""
            RUN cd ~/ffmpeg_sources && \
                curl -O -L https://github.com/openssl/openssl/archive/OpenSSL_1_1_1c.tar.gz && \
                tar -xf OpenSSL_1_1_1c.tar.gz && \
                cd ~/ffmpeg_sources/openssl-OpenSSL_1_1_1c && \
                PERL="$HOME/openssl_build/bin/perl" ./config --prefix="$HOME/ffmpeg_build" --openssldir="$HOME/ffmpeg_build" shared zlib && \
                make -j$(getconf _NPROCESSORS_ONLN) && \
                make install_sw && \
                rm -rf ~/openssl_build
            """
            )
        )

    parts.append(
        ub.codeblock(
            r"""
        RUN cd ~/ffmpeg_sources && \
            curl -O -L http://www.nasm.us/pub/nasm/releasebuilds/2.14.01/nasm-2.14.01.tar.bz2 && \
            tar -xf nasm-2.14.01.tar.bz2 && cd nasm-2.14.01 && ./autogen.sh && \
            ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" && \
            make -j$(getconf _NPROCESSORS_ONLN) && \
            make install

        RUN cd ~/ffmpeg_sources && \
            curl -O -L http://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz && \
            tar -xf yasm-1.3.0.tar.gz && \
            cd yasm-1.3.0 && \
            ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" && \
            make -j$(getconf _NPROCESSORS_ONLN) && \
            make install

        RUN cd ~/ffmpeg_sources && \
            git clone --depth 1 https://chromium.googlesource.com/webm/libvpx.git && \
            cd libvpx && \
            ./configure --prefix="$HOME/ffmpeg_build" --disable-examples --disable-unit-tests --enable-vp9-highbitdepth --as=yasm --enable-pic --enable-shared && \
            make -j$(getconf _NPROCESSORS_ONLN) && \
            make install

        RUN cd ~/ffmpeg_sources && \
            curl -O -L https://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2 && \
            tar -xf ffmpeg-snapshot.tar.bz2 && \
            cd ffmpeg && \
            PATH=~/bin:$PATH && \
            PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure --prefix="$HOME/ffmpeg_build" --extra-cflags="-I$HOME/ffmpeg_build/include" --extra-ldflags="-L$HOME/ffmpeg_build/lib" --enable-openssl --enable-libvpx --enable-shared --enable-pic --bindir="$HOME/bin" && \
            make -j$(getconf _NPROCESSORS_ONLN) && \
            make install && \
            echo "/root/ffmpeg_build/lib/" >> /etc/ld.so.conf && \
            ldconfig && \
            rm -rf ~/ffmpeg_sources

        ENV PKG_CONFIG_PATH /usr/local/lib/pkgconfig:/root/ffmpeg_build/lib/pkgconfig
        ENV LDFLAGS -L/root/ffmpeg_build/lib

        RUN curl -O https://raw.githubusercontent.com/torvalds/linux/v4.14/include/uapi/linux/videodev2.h && \
            curl -O https://raw.githubusercontent.com/torvalds/linux/v4.14/include/uapi/linux/v4l2-common.h && \
            curl -O https://raw.githubusercontent.com/torvalds/linux/v4.14/include/uapi/linux/v4l2-controls.h && \
            curl -O https://raw.githubusercontent.com/torvalds/linux/v4.14/include/linux/compiler.h && \
            mv videodev2.h v4l2-common.h v4l2-controls.h compiler.h /usr/include/linux
        """
        )
    )

    if PLAT == 'i686':
        parts.append(
            ub.codeblock(
                r"""
            #in i686, yum metadata ends up with slightly wrong timestamps
            #which inhibits its update
            #https://github.com/skvark/opencv-python/issues/148
            RUN yum clean all
            """
            )
        )

    parts.append(
        ub.codeblock(
            r"""
        ENV PATH "$HOME/bin:$PATH"
        """
        )
    )

    # Create a virtual environment for each supported python version
    for MB_PYTHON_TAG in MB_PYTHON_TAGS:
        if PLAT == 'x86_64':
            pip_pkgs = 'cmake ubelt numpy wheel'
        else:
            pip_pkgs = 'ubelt numpy wheel'
        parts.append(
            ub.codeblock(
                fr"""
            RUN /opt/python/{MB_PYTHON_TAG}/bin/python -m pip -q --no-cache-dir install pip -U && \
                /opt/python/{MB_PYTHON_TAG}/bin/python -m pip -q --no-cache-dir install setuptools pip virtualenv && \
                /opt/python/{MB_PYTHON_TAG}/bin/python -m virtualenv /root/venv-{MB_PYTHON_TAG} && \
                source /root/venv-{MB_PYTHON_TAG}/bin/activate && \
                python -m pip -q --no-cache-dir install scikit-build ninja && \
                python -m pip -q --no-cache-dir install {pip_pkgs}
            """
            )
        )

    # we don't need opencv to build with python so only do this once
    MB_PYTHON_TAGS = MB_PYTHON_TAGS[0:1]
    for MB_PYTHON_TAG in MB_PYTHON_TAGS:
        major, minor = MB_PYTHON_TAG.replace('cp', '')[0:2]
        PY_VER = '{}.{}'.format(major, minor)

        config = {
            'is_64bit': PLAT in {'x86_64'},
            'build_contrib': False,
            'build_headless': True,
            'python_args': None,
            # We actually dont need python
            # 'python_args': {
            #     'py_ver': PY_VER,
            #     'py_executable': PY_VER,
            # },
            'linux_jpeg_args': {
                'jpeg_include_dir': '${JPEG_INCLUDE_DIR}',
                'jpeg_library': '${JPEG_LIBRARY}',
            },
        }
        sepstr = ' \\\n                '
        CMAKE_ARGS = sepstr.join(build_opencv_cmake_args(config))

        # Note we activate a python venv so we get the pip version of cmake.
        parts.append(
            ub.codeblock(
                fr"""
            RUN source /root/venv-{MB_PYTHON_TAG}/bin/activate && \
                mkdir -p /root/code/opencv/build && \
                cd /root/code/opencv/build && \
                cmake --version && \
                cmake {CMAKE_ARGS} /root/code/opencv && \
                cd /root/code/opencv/build && \
                make -j{MAKE_CPUS} && \
                make install && \
                rm -rf /root/code/opencv/build
            """
            )
        )

    docker_code = '\n\n'.join(parts)

    try:
        print(ub.color_text('\n--- DOCKER CODE ---', 'white'))
        print(ub.highlight_code(docker_code, 'docker'))
        print(ub.color_text('--- END DOCKER CODE ---\n', 'white'))
    except Exception:
        pass
    with open(dockerfile_fpath, 'w') as file:
        file.write(docker_code)

    docker_build_cli = ' '.join(
        [
            'docker',
            'build',
            '--tag {}'.format(DOCKER_TAG),
            '-f {}'.format(dockerfile_fpath),
            '.',
        ]
    )
    print('docker_build_cli = {!r}'.format(docker_build_cli))

    if DRY:
        print('DRY RUN: Would run')
        print(f'docker pull {PARENT_IMAGE}')
        print(docker_build_cli)
    else:
        ub.cmd(f'docker pull {PARENT_IMAGE}')
        info = ub.cmd(docker_build_cli, verbose=3, shell=True)

        if info['ret'] != 0:
            print(ub.color_text('\n--- FAILURE ---', 'red'))
            print('Failed command:')
            print(info['command'])
            print(info['err'])
            raise Exception(
                'Building docker failed with exit code {}'.format(info['ret'])
            )
        else:
            print(ub.color_text('\n--- SUCCESS ---', 'green'))

        print(
            ub.highlight_code(
                ub.codeblock(
                    f"""
            # Finished creating the docker image.
            # To test / export / publish you can do something like this:


            # Test that we can get a bash terminal
            docker run -it {DOCKER_TAG} bash

            docker save -o {DOCKER_TAG}.docker.tar {DOCKER_TAG}

            # To publish to quay

            source $(secret_loader.sh)
            echo "QUAY_USERNAME = $QUAY_USERNAME"
            docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io

            docker tag {DOCKER_TAG} {DOCKER_URI}
            docker push {DOCKER_URI}

            """
                ),
                'bash',
            )
        )

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

        docker run --rm -it quay.io/pypa/manylinux2010_x86_64 /bin/bash

        # Pull the standard manylinux base images
        docker pull quay.io/pypa/manylinux2010_i686
        docker pull quay.io/pypa/manylinux2010_x86_64
        docker pull quay.io/pypa/manylinux2014_i686
        docker pull quay.io/pypa/manylinux2014_x86_64
        docker pull quay.io/pypa/manylinux2014_aarch64


        python ~/code/vtool/dev/build_base_docker.py --dry
        python ~/code/vtool/dev/build_base_docker.py --plat=x86_64
        python ~/code/vtool/dev/build_base_docker.py --plat=i686
        python ~/code/vtool/dev/build_base_docker.py --plat=aarch64 --dry
    """
    main()
