FROM ubuntu:18.04

# setup timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# get and install building tools + ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ninja-build \
        python3 \
        python3-coverage \
        python3-flake8 \
        python3-matplotlib \
        python3-pandas \
        ca-certificates \
        pkg-config \
        yasm \
        libva-dev libva2 \
        libssl-dev \
        libx264-dev libx264-152 \
        libx265-dev libx265-146 \
        libvpx-dev libvpx5 \
        i965-va-driver-shaders \
        mesa-va-drivers \
        nvidia-cuda-dev \
        nvidia-cuda-toolkit \
        clang \
        wget \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists

# retrieve source code
RUN git clone --branch v1.3.15 --depth 1 https://github.com/Netflix/vmaf.git /vmaf
RUN git clone --branch n4.1.4 --depth 1 https://github.com/FFmpeg/FFmpeg.git /ffmpeg
RUN git clone --branch n9.1.23.1 --depth 1 https://github.com/FFmpeg/nv-codec-headers.git /nv-codec-headers

# build vmaf + ffmpeg
RUN cd /vmaf && make -j $(nproc --all) && make install
RUN cd /nv-codec-headers && make install
RUN cd /ffmpeg && \
    ./configure --enable-version3 --enable-gpl --enable-nonfree --enable-small \
        --enable-openssl \
        --enable-libvmaf --enable-vaapi \
        --enable-libvpx --enable-libx264 --enable-libx265 \
        --enable-nvenc --enable-libnpp && \
    make -j $(nproc --all)

# setup env
ENV PATH=/ffmpeg:$PATH
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all

WORKDIR /root/data/
