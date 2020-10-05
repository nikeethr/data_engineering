FROM jenkins/jenkins:lts

# jenkins container initialises as `jenkins` user
USER root

# install ansible using pip as root (platform independent)
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py && \
    pip install ansible --upgrade

# switch back to jenkins user to run as usual
USER jenkins
