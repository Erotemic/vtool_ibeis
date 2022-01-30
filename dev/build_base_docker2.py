import ubelt as ub
import os


def argval(clikey, envkey=None, default=ub.NoParam):
    if envkey is not None:
        envval = os.environ.get(envkey)
        if envval:
            default = envval
    return ub.argval(clikey, default=default)


def main():
    fletch_version = 'v1.5.0'
    ARCH = argval('--arch', 'ARCH', default='x86_64')
    PARENT_IMAGE_PREFIX = argval('--parent_image_prefix', 'PARENT_IMAGE_PREFIX', default='manylinux2014')
    # PARENT_IMAGE_PREFIX = 'manylinux_2_24'
    # PARENT_IMAGE_PREFIX = 'manylinux2014'

    PARENT_IMAGE_BASE = f'{PARENT_IMAGE_PREFIX}_{ARCH}'
    PARENT_IMAGE_TAG = 'latest'
    PARENT_IMAGE_NAME = f'{PARENT_IMAGE_BASE}:{PARENT_IMAGE_TAG}'

    PARENT_QUAY_USER = 'quay.io/pypa'
    PARENT_IMAGE_URI = f'{PARENT_QUAY_USER}/{PARENT_IMAGE_NAME}'

    OUR_QUAY_USER = 'quay.io/erotemic'
    OUR_IMAGE_BASE = f'{PARENT_IMAGE_BASE}_for'
    OUR_IMAGE_TAG = f'fletch{fletch_version}-opencv'
    OUR_IMAGE_NAME = f'{OUR_IMAGE_BASE}:{OUR_IMAGE_TAG}'

    OUR_DOCKER_URI = f'{OUR_QUAY_USER}/{OUR_IMAGE_NAME}'
    DRY = ub.argflag('--dry')

    dpath = ub.Path(ub.get_app_cache_dir('erotemic/manylinux-for/workspace2')).ensuredir()

    dockerfile_fpath = dpath / f'{OUR_IMAGE_BASE}.{OUR_IMAGE_TAG}.Dockerfile'

    if PARENT_IMAGE_PREFIX == 'manylinux2014':
        distribution = 'centos'
    elif PARENT_IMAGE_PREFIX == 'manylinux_2_24':
        distribution = 'debian'
    elif PARENT_IMAGE_PREFIX == 'musllinux_1_1':
        distribution = 'alpine'
    else:
        raise KeyError(PARENT_IMAGE_PREFIX)

    USE_STAGING_STRATEGY = False

    if USE_STAGING_STRATEGY:
        staging_dpath = (dpath / 'staging').ensuredir()
        fletch_dpath = staging_dpath / 'fletch'
        if not fletch_dpath.exists():
            # TODO: setup a dummy build on the host machine that
            # pre-downloads all the requirements so we can stage them
            ub.cmd('git clone -b @v1.5.0 https://github.com/Kitware/fletch.git', cwd=staging_dpath)
        ub.cmd(f'git checkout {fletch_version}', cwd=fletch_dpath)

    parts = []
    parts.append(ub.codeblock(
        f'''
        FROM {PARENT_IMAGE_URI}
        SHELL ["/bin/bash", "-c"]
        ENV HOME=/root
        RUN mkdir -p /root/code
        '''))
    # ENV ARCH={ARCH}

    fletch_init_commands = []
    if USE_STAGING_STRATEGY:
        parts.append(ub.codeblock(
            '''
            COPY ./staging/fletch /root/code/fletch
            '''))
        fletch_init_commands.extend([
            'mkdir -p /root/code/fletch/build',
            'cd /root/code/fletch/build',
        ])
    else:
        # Clone specific branch with no tag history
        fletch_init_commands.extend([
            'cd /root/code',
            'git clone -b v1.5.0 --depth 1 https://github.com/Kitware/fletch.git fletch',
            'mkdir -p /root/code/fletch/build',
            'cd /root/code/fletch/build',
        ])
    fletch_init_commands.append(ub.codeblock(
        r'''
        cmake \
            -Dfletch_ENABLE_OpenCV=True \
            -DCMAKE_BUILD_TYPE=Release \
            -DOpenCV_SELECT_VERSION=4.2.0 ..
        '''))
    fletch_init_commands.extend([
        'make -j$(getconf _NPROCESSORS_ONLN)',
        'make install',
        'rm -rf /root/code/fletch',
    ])
    BS = '\\'
    NL = '\n'
    CMD_SEP = f' && {BS}{NL}'
    fletch_init_run_command = ub.indent(CMD_SEP.join(fletch_init_commands)).lstrip()
    parts.append(f'RUN {fletch_init_run_command}')

    parts.append(f'RUN {fletch_init_run_command}')

    if distribution == 'centos':
        yum_libs = [
            'lz4-devel',
        ]
        yum_libs_str = ' '.join(yum_libs)
        yum_parts = [
            'yum update -y',
            f'yum install {yum_libs_str} -y',
            'yum clean all',
        ]
        yum_install_cmd = ub.indent(CMD_SEP.join(yum_parts)).lstrip()
        parts.append(f'RUN {yum_install_cmd}')
    elif distribution == 'debian':
        apt_libs = [
            'liblz4-dev',
        ]
        apt_libs_str = ' '.join(apt_libs)
        apt_parts = [
            'apt-get update',
            'apt-get install',
            f'apt-get install {apt_libs_str} -y',
            'rm -rf /var/lib/apt/lists/*',
        ]
        apt_install_cmd = ub.indent(CMD_SEP.join(apt_parts)).lstrip()
        parts.append(f'RUN {apt_install_cmd}')
    elif distribution == 'alpine':
        apt_libs = [
            'lz4-dev',
        ]
        apt_libs_str = ' '.join(apt_libs)
        apt_parts = [
            f'apk add --update-cache {apt_libs_str}',
            'rm -rf /var/cache/apk/*',
        ]
        apk_install_cmd = ub.indent(CMD_SEP.join(apt_parts)).lstrip()
        parts.append(f'RUN {apk_install_cmd}')

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
        '--tag {}'.format(OUR_IMAGE_NAME),
        '-f {}'.format(dockerfile_fpath),
        '.'
    ])
    print('docker_build_cli = {!r}'.format(docker_build_cli))

    if DRY:
        print('DRY RUN: Would run')
        print(f'docker pull {PARENT_IMAGE_URI}')
        print(f'cd {dpath}')
        print(docker_build_cli)
    else:
        ub.cmd(f'docker pull {PARENT_IMAGE_URI}', verbose=3)
        info = ub.cmd(docker_build_cli, cwd=dpath, verbose=3, shell=True, check=True)

        if info['ret'] != 0:
            print(ub.color_text('\n--- FAILURE ---', 'red'))
            print('Failed command:')
            print(info['command'])
            print(info['err'])
            raise Exception('Building docker failed with exit code {}'.format(info['ret']))
        else:
            print(ub.color_text('\n--- SUCCESS ---', 'green'))

        print(ub.highlight_code(ub.codeblock(
            f'''
            # Finished creating the docker image.
            # To test / export / publish you can do something like this:

            # Test that we can get a bash terminal
            docker run -it {OUR_IMAGE_NAME} bash

            docker save -o {OUR_IMAGE_NAME}.docker.tar {OUR_IMAGE_NAME}

            # To publish to quay

            source $(secret_loader.sh)
            echo "QUAY_USERNAME = $QUAY_USERNAME"
            docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io

            docker tag {OUR_IMAGE_NAME} {OUR_DOCKER_URI}
            docker push {OUR_DOCKER_URI}
            '''), 'bash'))


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --dry

        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux_2_24
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux_2_24
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=manylinux2014
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=manylinux2014

        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=x86_64 --parent_image_prefix=musllinux_1_1 --lz4
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=i686 --parent_image_prefix=musllinux_1_1 --lz4

        python ~/code/vtool_ibeis/dev/build_base_docker2.py --arch=aarch64 --dry

        # Then to build with CIBW
        pip install cibuildwheel
        CIBW_BUILD='cp*-manylinux_x86_64' CIBW_MANYLINUX_X86_64_IMAGE=quay.io/erotemic/manylinux-for:x86_64-fletch1.5.0-opencv cibuildwheel --platform linux --archs x86_64


    """
    main()
