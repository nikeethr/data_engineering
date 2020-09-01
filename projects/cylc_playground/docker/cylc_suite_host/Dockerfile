FROM centos:8

ARG MYUSER=cylc-user
ARG MYGROUP=cylc
USER root

RUN yum -y update && yum -y upgrade

# Set locale
# Gtk throws a warning...
RUN yum install -y \
    langpacks-en \
    langpacks-de \
    glibc-all-langpacks

# --- Cylc ---
RUN dnf install -y \
        git \
        python2 \
        python2-devel \
        python2-pip \
        pygtk2 \
        openssl \
        at \
        sudo \
        systemd \
        vim
# ---

# --- SSH ---
# install openssh-server
RUN yum -y install --enablerepo=PowerTools \
        openssh-server \
        openssh-clients \
        xorg-x11-server-Xorg \
        xorg-x11-xauth \
        xorg-x11-apps
# ---

# Setup user + ssh
RUN groupadd $MYGROUP && \
    useradd --shell /bin/bash -g $MYGROUP -m $MYUSER && \
    usermod -a -G daemon,wheel $MYUSER && \
    echo "${MYUSER}:1234" | chpasswd && \
    mkdir /home/$MYUSER/.ssh && \
    chmod 0700 /home/$MYUSER/.ssh && \
    chown $MYUSER:$MYGROUP -R /home/$MYUSER

# update ssh settings
RUN echo "X11UseLocalhost no" >> /etc/ssh/sshd_config

# For centos:7 you need to run the following instead:
# RUN /usr/sbin/sshd-keygen
# For later centos:
RUN ssh-keygen -A
# The above will create a key for each key type

# Expose port 22 used for SSH connections
EXPOSE 22

# This should be removed after installation, but doing this just incase to
# allow SSH login
RUN rm -rf /run/nologin

# install pip packages
USER $MYUSER
COPY requirements.txt /tmp/
RUN pip2 install -r /tmp/requirements.txt --user

# copy other stuff
COPY .vimrc /home/$MYUSER/.vimrc

# start the sshd daemon, -D flag specifies that sshd will not detach - which is
# needed for container to keep running.
USER root
CMD /usr/sbin/sshd -D
