FROM centos:8

ARG MYUSER=cylc-user
ARG MYGROUP=cylc

# installopenssh-server
RUN yum -y install openssh-server && \
    yum -y install openssh-clients && \
    yum -y install xorg-x11-server-Xorg && \
    yum -y install xorg-x11-xauth && \
    yum -y install xorg-x11-apps --enablerepo=PowerTools

# Setup user + ssh
RUN groupadd $MYGROUP && \
    useradd -m -g $MYGROUP $MYUSER && \
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

# start the sshd daemon, -D flag specifies that sshd will not detach - which is
# needed for container to keep running.
CMD /usr/sbin/sshd -D
