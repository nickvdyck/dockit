FROM ubuntu

RUN apt update && \
    apt install -y iproute2 net-tools iputils-ping htop curl btrfs-tools python3 python3-pip && \
    rm /etc/dpkg/dpkg.cfg.d/excludes && \
    apt-get update && \
        dpkg -l | grep ^ii | cut -d' ' -f3 | xargs apt-get install -y --reinstall && \
        rm -r /var/lib/apt/lists/* && \
    apt update && \
    apt upgrade -y && \
    apt install -y man manpages-posix manpages-posix-dev

RUN dd if=/dev/zero of=volumes-disk.img bs=512 count=4194304 && \
    mkfs.btrfs volumes-disk.img && \
    mkdir /volumes

WORKDIR /app

COPY init.sh /init.sh
