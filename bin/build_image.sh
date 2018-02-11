#!/bin/bash

docker build \
    -f Dockerfile.raspbian \
    -t databat/sonar\
    .
