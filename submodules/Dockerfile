FROM balenalib/raspberrypi3-python:3.7.4

USER root

ARG userid="31415"
ARG groupid="31415"
ARG vidid="31415"
ARG i2cid="31415"
ARG spiid="31415"
ARG gpioid="31415"

RUN addgroup --gid ${groupid} lig && \
    adduser lig --uid ${userid} --gid ${groupid} \
    --gecos '' --disabled-password

#RUN addgroup --gid ${vidid} video && \
#RUN addgroup --gid ${i2cid} i2c && \
RUN addgroup --gid ${spiid} spi && \
    addgroup --gid ${gpioid} gpio

RUN usermod -a -G video lig && \
    usermod -a -G i2c lig && \
    usermod -a -G spi lig && \
    usermod -a -G gpio lig

# This updates to the raspberry pi python repo to make sure that we
#   download binaries whenever possible vs. building from source
COPY ./config/pip.conf /etc/pip.conf

RUN apt update && apt install -y libatlas3-base libgfortran5 vim

RUN pip3 install --upgrade pip setuptools

USER lig

# Need to install as root because a user (site-packages) install isn't avail.
# We use a pip_install file to install most things to save time via caching
#   since the dependencies don't change often, but my libraries might
USER root
WORKDIR /home/lig/
COPY --chown=lig:lig ./config/pip_install.txt .
RUN pip3 install --no-cache-dir -r pip_install.txt

WORKDIR /home/lig/
COPY --chown=lig:lig ./ligmos ./ligmos
WORKDIR /home/lig/ligmos
RUN pip3 install -e .

WORKDIR /home/lig/
COPY --chown=lig:lig ./PiCamHelpers ./PiCamHelpers
WORKDIR /home/lig/PiCamHelpers
RUN pip3 install -e .

WORKDIR /home/lig/
COPY --chown=lig:lig ./JohnnyFive ./JohnnyFive
WORKDIR /home/lig/JohnnyFive
RUN pip3 install -e .

# Ultimonitor requires no installation
WORKDIR /home/lig/
COPY --chown=lig:lig ./Ultimonitor ./Ultimonitor

USER lig
WORKDIR /home/lig
RUN mkdir /home/lig/www/ && mkdir /home/lig/snaps/ && \
    mkdir /home/lig/snaps/anim/ && mkdir /home/lig/logs && \
    mkdir /home/lig/Ultimonitor/logs/ && mkdir /home/lig/Ultimonitor/ultisnaps/

CMD ["/bin/bash"]
