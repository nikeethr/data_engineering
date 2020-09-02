FROM local/c8_base

LABEL maintainer="nikeeth.ramanathan@gmail.com"

ARG MYUSER=cylc-user
ARG MYGROUP=cylc
ARG CYLC_VERSION=7.8.6

USER root

# To be able to run `sudo service xxx start`
RUN yum -y update && \
    yum -y upgrade && \
    yum -y install initscripts && \
    yum clean all

# Set locale
# Gtk throws a warning...
RUN yum install -y \
        langpacks-en \
        langpacks-de \
        glibc-all-langpacks && \
    yum clean all

# --- Install Cylc dependencies ---
# enable PowerTools
RUN dnf -y install dnf-plugins-core && \
    dnf config-manager --set-enabled PowerTools && \
    dnf clean all

# install dependencies
RUN dnf -y install \
        gcc gcc-c++ make \
        git \
        python2 python2-devel python2-pip \
        graphviz graphviz-devel \
        pygtk2 \
        rsync \
        at \
        sudo \
        vim && \
    dnf clean all

# install pip packages
COPY requirements.txt /tmp/
RUN pip2 install -r /tmp/requirements.txt
# ---

# --- Install SSH ---
# install openssh-server
RUN yum -y install --enablerepo=PowerTools \
        openssh-server \
        openssh-clients \
        xorg-x11-server-Xorg \
        xorg-x11-xauth \
        xorg-x11-apps && \
    yum clean all
# ---

# --- Install Cylc ---
# TODO: this is quite messy, since repo migrated from cylc to cylc-flow
# it might be better to clone from git and add the repo/usr/bin/cylc to path
WORKDIR /opt

RUN curl -L -o cylc-${CYLC_VERSION}.tar.gz \
        https://github.com/cylc/cylc-flow/archive/${CYLC_VERSION}.tar.gz && \
    tar -xvf cylc-${CYLC_VERSION}.tar.gz && \
    mv cylc-flow-${CYLC_VERSION} cylc-${CYLC_VERSION} && \
    ln -s /opt/cylc-${CYLC_VERSION} /opt/cylc && \
    cp /opt/cylc-${CYLC_VERSION}/usr/bin/cylc /usr/local/bin/ && \
    cd cylc-${CYLC_VERSION} && \
    make

WORKDIR /
# ---

# --- Setup user ---
# Setup user + ssh
RUN groupadd $MYGROUP && \
    useradd --shell /bin/bash -g $MYGROUP -m $MYUSER && \
    usermod -a -G daemon,wheel $MYUSER && \
    echo "${MYUSER} ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/$MYUSER && \
    chmod 0440 /etc/sudoers.d/$MYUSER && \
    mkdir /home/$MYUSER/.ssh && \
    chmod 0700 /home/$MYUSER/.ssh && \
    chown -R $MYUSER /home/$MYUSER && \
    chown -R $MYUSER /opt/cylc-${CYLC_VERSION}
# ---

# --- Setup SSH ---
# update ssh settings
RUN echo "X11UseLocalhost no" >> /etc/ssh/sshd_config

# For centos:7 you need to run the following instead:
# RUN /usr/sbin/sshd-keygen
# For later centos:
RUN ssh-keygen -A
# The above will create a key for each key type

# Expose port 22 used for SSH connections
EXPOSE 22

# enable sshd service
RUN systemctl enable sshd

# This should be removed after installation, but doing this just incase to
# allow SSH login
RUN rm -rf /run/nologin
# ---

# copy user specific stuff
USER $MYUSER

WORKDIR /home/$MYUSER
COPY --chown=$MYUSER:$MYGROUP .vimrc .
COPY --chown=$MYUSER:$MYGROUP docker_entrypoint.sh .

# --- move this to rightful spots ---
# setup cylc config/editor/examples
RUN cylc get-global-config > /opt/cylc/etc/global.rc && \
    cylc import-examples /tmp && \
    mv ~/cylc-run/examples/$(cylc --version)/tutorial ~/cylc-run/tut && \
    mkdir -p ~/.vim/syntax && \
    cp /opt/cylc/etc/syntax/cylc.vim ~/.vim/syntax/cylc.vim
# ---

USER root

CMD ./docker_entrypoint.sh
