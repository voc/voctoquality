FROM debian:buster

# setup timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# get and install building tools + ffmpeg
RUN sed -i "s#debian buster main#debian buster main contrib non-free#g" /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ninja-build \
        python3 \
        python3-matplotlib \
        ca-certificates \
        pkg-config \
        yasm \
        libva-dev libva2 \
        libx264-dev libx264-155 \
        libx265-dev libx265-165 \
        libvpx-dev libvpx5 \
        i965-va-driver-shaders \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists

# retrieve source code
RUN git clone --branch v1.3.15 --depth 1 https://github.com/Netflix/vmaf.git /vmaf
RUN git clone --branch n4.1.4 --depth 1 https://github.com/FFmpeg/FFmpeg.git /ffmpeg

# build vmaf + ffmpeg
RUN cd /vmaf && make -j $(nproc --all) && make install
RUN cd /ffmpeg && \
    ./configure --enable-version3 --enable-gpl --enable-nonfree --enable-small \
        --enable-libvmaf --enable-vaapi \
        --enable-libvpx --enable-libx264 --enable-libx265 && \
    make -j $(nproc --all)

# setup env
ENV PATH=/ffmpeg:$PATH

WORKDIR /root/data/
