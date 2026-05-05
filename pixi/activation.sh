#!/bin/bash
# Pixi activation script — sets environment variables for genom/gazebo

export GZ_LAUNCH_PLUGIN_PATH=$CONDA_PREFIX/lib/gz-launch-8/plugins:$GZ_LAUNCH_PLUGIN_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$CONDA_PREFIX/lib/gazebo:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$CONDA_PREFIX/share:$PIXI_PROJECT_ROOT/gz/models:$GZ_SIM_RESOURCE_PATH
export ROBOTPKG_BASE=$CONDA_PREFIX
