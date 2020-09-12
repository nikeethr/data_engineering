FROM centos

# install openssh-server
RUN yum -y install openssh-server

# install mysql client
# for server you will need `yum -y install mysql mysql-server`
RUN yum -y install mysql

# install aws cli (needs unzip, groff, glibc, less)
RUN yum -y install unzip
RUN dnf install -y  --enablerepo=PowerTools groff
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

# Add remote user to ssh into container via jenkins
# 1. create remote user
# 2. give remote_user a password
# 3. create home directory + .ssh for remote user
# 4. change permissions of .ssh to allowed permissions (700)
# For centos:7 you will use this line instead to set password:
# echo "1234" | passwd remote_user --stdin && \
RUN useradd remote_user && \
    echo "remote_user:1234" | chpasswd && \
    mkdir /home/remote_user/.ssh && \
    chmod 700 /home/remote_user/.ssh

# Copy generated key as authorized keys
COPY remote-key.pub /home/remote_user/.ssh/authorized_keys

# Copy table info
COPY table_patient_info.txt /tmp/table_patient_info.txt

# Copy script to backup database
# TODO: this can instead be mapped to a volume
RUN mkdir /tmp/scripts
COPY backup_db.sh /tmp/scripts/backup_db.sh

# change owner to remote user
# make sure authorized_key is only r/w via remote_owner
RUN chown remote_user:remote_user -R /home/remote_user/.ssh/ && \
    chmod 600 /home/remote_user/.ssh/authorized_keys

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
# nice for monitoring.
CMD /usr/sbin/sshd -D
