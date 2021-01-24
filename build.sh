#!/bin/sh
tag=${1}
DOCKER_BUILDKIT=1 docker build -t ${tag} .
