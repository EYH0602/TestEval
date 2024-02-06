#!/bin/bash
# Environment setup for non-docker user.
export WORKDIR=`pwd`
export CORES=`nproc`

export PYTHONPATH=$PYTHONPATH:$WORKDIR