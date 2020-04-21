# encoding comparison docker
Contains ffmpeg with libvmaf, vaapi, libvpx, libx264 and libx265 support.

Can be used to compare encoding quality with different settings or encoders.

## Build
```bash
docker build --tag vmaf .
```

or use
```
docker pull ischluff/vmaf:latest
```

## Usage
First clone this repo to your machine.

Then put your formats and custom graphing into a small python module.
As a reference you can use **data/compare_vaapi_h264.py**.

```bash
# Start the container
docker run \
  --rm \
  --privileged \
  -v /dev/dri:/dev/dri \
  -v `pwd`:/root \
  -it vmaf /bin/bash

# Run inside the container
./compare_vaapi_x264.py reference.nut
```
