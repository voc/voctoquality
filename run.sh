#!/bin/bash
name=${1:-ischluff/vmaf:latest}
docker run \
  --rm \
  --privileged \
  -v /dev/dri:/dev/dri \
  -v `pwd`/data:/root/data \
  -it $name /bin/bash
