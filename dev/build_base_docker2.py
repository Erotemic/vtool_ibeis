import ubelt as ub
import os
QUAY_REPO = 'quay.io/erotemic/manylinux-for'


def argval(clikey, envkey=None, default=ub.NoParam):
    if envkey is not None:
        envval = os.environ.get(envkey)
        if envval:
            default = envval
    return ub.argval(clikey, default=default)


def main():
    dpath = ub.Path(ub.get_app_cache_dir('erotemic/manylinux-for/workspace2'))
    staging_dpath = (dpath / 'staging').ensuredir()
    fletch_dpath = staging_dpath / 'fletch'
    if not fletch_dpath.exists():
        # TODO: setup a dummy build on the host machine that
        # pre-downloads all the requirements so we can stage them
        ub.cmd('git clone https://github.com/Kitware/fletch.git', cwd=staging_dpath)
    ub.cmd('git checkout v1.5.0', cwd=fletch_dpath)

    ARCH = argval('--arch', 'ARCH', default='x86_64')
    manylinux_base = 'manylinux_2_24'
    BASE = f'{manylinux_base}_{ARCH}'
    DOCKER_TAG = '{}-fletch1.5.0-opencv'.format(ARCH)
    DOCKER_URI = f'{QUAY_REPO}:{DOCKER_TAG}'
    DRY = ub.argflag('--dry')

    dockerfile_fpath = dpath / ('Dockerfile_' + DOCKER_TAG)
    BASE_REPO = 'quay.io/pypa'
    PARENT_IMAGE = f'{BASE_REPO}/{BASE}'

    parts = []

    parts.append(ub.codeblock(
        f'''
        FROM {PARENT_IMAGE}
        SHELL ["/bin/bash", "-c"]
        ENV HOME=/root
        ENV ARCH={ARCH}
        '''))

    parts.append(ub.codeblock(
        '''
        RUN mkdir -p /staging

        COPY ./staging/fletch /staging/fletch
        RUN mkdir -p /root/code
        RUN cp -r /staging/fletch /root/code/fletch
        '''))

    parts.append(ub.codeblock(
        r'''
        RUN mkdir -p /root/code/fletch/build
        RUN cd /root/code/fletch/build && \
            cmake -Dfletch_ENABLE_OpenCV=True -DOpenCV_SELECT_VERSION=4.2.0 .. && \
            make -j$(getconf _NPROCESSORS_ONLN) && \
            make install
        '''))

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

    if DRY:
        print('DRY RUN: Would run')
        print(f'docker pull {PARENT_IMAGE}')
        print(f'cd {dpath}')
        print(docker_build_cli)
    else:
        ub.cmd(f'docker pull {PARENT_IMAGE}')
        info = ub.cmd(docker_build_cli, cwd=dpath, verbose=3, shell=True)

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
            docker run -it {DOCKER_TAG} bash

            docker save -o {DOCKER_TAG}.docker.tar {DOCKER_TAG}

            # To publish to quay

            source $(secret_loader.sh)
            echo "QUAY_USERNAME = $QUAY_USERNAME"
            docker login -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io

            docker tag {DOCKER_TAG} {DOCKER_URI}
            docker push {DOCKER_URI}
            '''), 'bash'))


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/vtool_ibeis/dev/build_base_docker2.py --dry

        # Then to build with CIBW
        pip install cibuildwheel
        CIBW_MANYLINUX_X86_64_IMAGE=quay.io/erotemic/manylinux-for:x86_64-fletch1.5.0-opencv cibuildwheel --platform linux

    """
    main()
