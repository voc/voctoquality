docker run \
  --rm \
  --privileged \
  -v /dev/dri:/dev/dri \
  -v `pwd`/data:/root/data \
  -it vmaf /bin/bash
