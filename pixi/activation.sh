#!/bin/bash
# Pixi activation script — sets environment variables for genom/gazebo

export GZ_LAUNCH_PLUGIN_PATH=$CONDA_PREFIX/lib/gz-launch-8/plugins:$GZ_LAUNCH_PLUGIN_PATH
export GZ_SIM_SYSTEM_PLUGIN_PATH=$CONDA_PREFIX/lib/gazebo:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$PIXI_PROJECT_ROOT/telekyb3-pixi-main/models:$GZ_SIM_RESOURCE_PATH
export ROBOTPKG_BASE=$CONDA_PREFIX
