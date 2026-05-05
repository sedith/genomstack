#!/bin/bash
# ROS2 activation script — sources the ROS2 environment from the pixi prefix

if [ -f "$CONDA_PREFIX/setup.bash" ]; then
    # shellcheck disable=SC1090
    source "$CONDA_PREFIX/setup.bash"
fi
