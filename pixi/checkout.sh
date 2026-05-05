#!/bin/sh
# Checkout script: clones all source repositories into $CONDA_PREFIX/src
# Run once after `pixi install`, before `pixi run build`.

set -e

cd "$CONDA_PREFIX"
mkdir -p src && cd src

echo "=========================================="
echo "Cloning core GenoM toolchain ..."
echo "=========================================="

# openrobots-idl: common genom IDL
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/openrobots-idl.git

# genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/genom3.git

# genomix
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/genomix.git

# python-genomix
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/genomix/python-genomix.git

# pocolibs middleware
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/pocolibs.git

# pocolibs genom3 template
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/genom3/genom3-pocolibs.git

# libkdtp (motion planning, required by nhfc)
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/libkdtp.git

echo "=========================================="
echo "Cloning telekyb3 components ..."
echo "=========================================="

# rotorcraft-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/telekyb3/rotorcraft-genom3

# nhfc-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/telekyb3/nhfc-genom3.git

# uavatt-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/telekyb3/uavatt-genom3.git

# uavpos-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/telekyb3/uavpos-genom3.git

# maneuver-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/telekyb3/maneuver-genom3.git

echo "=========================================="
echo "Cloning OpenRobots components ..."
echo "=========================================="

# pom-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/pom-genom3.git

# optitrack-genom3
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/optitrack-genom3.git

# qualisys-genom3 (optional — requires SSH access to Inria GitLab)
# git -c core.eol=lf -c core.autocrlf=false clone --branch fix_qualisys_sdk_new_api git@gitlab.inria.fr:rainbow/software/telekyb3/qualisys-genom3.git

echo "=========================================="
echo "Cloning Gazebo simulation plugins ..."
echo "=========================================="

# optitrack-gazebo
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/optitrack-gazebo.git

# libmrsim
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/libmrsim.git

# mrsim-gazebo
git -c core.eol=lf -c core.autocrlf=false clone git://git.openrobots.org/robots/mrsim-gazebo.git

echo "=========================================="
echo "Checkout complete."
echo "Run 'pixi run build' to compile and install."
echo "=========================================="
