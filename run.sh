docker run \
  --rm \
  --privileged \
  -v /dev/dri:/dev/dri \
  -v `pwd`/data:/root/data \
  -it ischluff/vmaf:latest /bin/bash
