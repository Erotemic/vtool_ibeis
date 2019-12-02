ubuntu_docker_requires()
{
    __heredoc__="""
    Ensure proper groups and base dependencies exist
    """
    # Ensure the docker group exists
    if [ "$(groups | grep docker)" = "" ]; then
        sudo groupadd docker
    fi
    # Add current $USER to docker group if not in it already
    if [ "$(groups $USER | grep docker)" = "" ]; then
        sudo usermod -aG docker $USER
        # NEED TO LOGOUT / LOGIN to revaluate groups
        su - $USER  # or we can do this
    fi
    # Install base dependencies
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
}


ubuntu_install_docker(){
    __heredoc__="""
    References:
        https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#set-up-the-repository
        https://github.com/NVIDIA/nvidia-docker
        https://docs.docker.com/install/linux/docker-ce/ubuntu/

    Notes:
        sudo ln -s /media/joncrall/4bf557b1-cbf7-414c-abde-a09a25e351a6/ /data
        mkdir -p /data/docker

    """
    # Add GPG keys for docker and nvidia
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -

    # Verify GPG keys
    sudo apt-key fingerprint 0EBFCD88 
    sudo apt-key fingerprint F796ECB0

    # Setup stable docker repository
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" 
    # Setup apt sources for nvidia-docker
    curl -s -L https://nvidia.github.io/nvidia-docker/ubuntu16.04/amd64/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    # Install nvidia-docker2 and reload the Docker daemon configuration
    sudo apt update -y

    # Install docker
    sudo apt install -y docker-ce docker-ce-cli containerd.io

    # Install nvidia-docker runtime
    sudo apt install -y nvidia-docker2
}


ubuntu_configure_docker(){
    __heredoc__="""
    Configure docker to use a different data directory
    """
    sudo pkill -SIGHUP dockerd

    # https://github.com/moby/moby/issues/3127
    # ENSURE ALL DOCKER PROCS ARE CLOSED
    docker ps -q | xargs docker kill

    sudo service docker stop

    # <DOCKER_CONFIG>
    # MOVE DOCKER DATA DIRECTORY TO EXTERNAL DRIVE
    DOCKER_DIR="/data/docker"
    #Ubuntu/Debian: edit your /etc/default/docker file with the -g option: 
    sudo sed -ie "s|^#* *DOCKER_OPTS.*|DOCKER_OPTS=\"-g ${DOCKER_DIR}\"|g" /etc/default/docker
    sudo sed -ie "s|^#* *export DOCKER_TMPDIR.*|export DOCKER_TMPDIR=${DOCKER_DIR}-tmp|g" /etc/default/docker
    # We need to point the systemctl docker serivce to this file
    # the proper way to edit systemd service file is to create a file in
    # /etc/systemd/system/docker.service.d/<something>.conf and only override
    # the directives you need. The file in /lib/systemd/system/docker.service
    # is "reserved" for the package vendor.
    sudo mkdir -p /etc/systemd/system/docker.service.d
    sudo sh -c 'cat > /etc/systemd/system/docker.service.d/override.conf << EOF
[Service]
EnvironmentFile=-/etc/default/docker
ExecStart=
ExecStart=/usr/bin/dockerd --host=fd:// --add-runtime=nvidia=/usr/bin/nvidia-container-runtime \$DOCKER_OPTS
EOF'
    # </DOCKER_CONFIG>
#ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock \$DOCKER_OPTS

    sudo systemctl daemon-reload
    sudo service docker start
}

__check_important_things__(){
    cat /etc/default/docker
    cat /lib/systemd/system/docker.service
    cat /etc/systemd/system/docker.service.d/override.conf
    gvim /lib/systemd/system/docker.service /etc/systemd/system/docker.service.d/override.conf

    cat /etc/docker/daemon.json

    cat /etc/default/docker | grep DOCKER_OPTS
    cat /etc/default/docker | grep DOCKER_TMPDIR
 
    service docker status
    service docker start

    # Maybe remove the old docker dir?
    sudo rm -rf /var/lib/docker
    sudo service docker restart


    sudo pkill -SIGHUP dockerd
    # https://github.com/moby/moby/issues/3127
    # ENSURE ALL DOCKER PROCS ARE CLOSED
    docker ps -q | xargs docker kill
    sudo service docker stop
    sudo systemctl daemon-reload
    sudo service docker start

    journalctl -xe

    sudo systemctl daemon-reload
    sudo systemctl restart docker.service
    
}

__docker_test__(){
    # TEST:

    if [ "$(groups $USER | grep docker)" = "" ]; then
        echo $@ >&2 
        exit 255
    fi
    docker run hello-world

    sudo docker run hello-world
}
