#!/bin/sh
# Build script: compiles and installs all sources into $CONDA_PREFIX
# Requires `pixi run checkout` to have been run first.

set -e

cd "$CONDA_PREFIX/src"

# openrobots-idl
echo "=========================================="
echo "Building openrobots-idl ..."
echo "=========================================="
cd openrobots-idl
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# genom3
echo "=========================================="
echo "Building genom3 ..."
echo "=========================================="
cd ../..
cd genom3
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# genomix
echo "=========================================="
echo "Building genomix ..."
echo "=========================================="
cd ../..
cd genomix
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# python-genomix
echo "=========================================="
echo "Building python-genomix ..."
echo "=========================================="
cd ../..
cd python-genomix
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# pocolibs middleware
echo "=========================================="
echo "Building pocolibs ..."
echo "=========================================="
cd ../..
cd pocolibs
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# pocolibs genom3 template
echo "=========================================="
echo "Building genom3-pocolibs ..."
echo "=========================================="
cd ../..
cd genom3-pocolibs
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# libkdtp
echo "=========================================="
echo "Building libkdtp ..."
echo "=========================================="
cd ../..
cd libkdtp
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# ----------------
# telekyb3 components
# ----------------

# rotorcraft-genom3
echo "=========================================="
echo "Building rotorcraft-genom3 ..."
echo "=========================================="
cd ../..
cd rotorcraft-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# nhfc-genom3
echo "=========================================="
echo "Building nhfc-genom3 ..."
echo "=========================================="
cd ../..
cd nhfc-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# uavatt-genom3
echo "=========================================="
echo "Building uavatt-genom3 ..."
echo "=========================================="
cd ../..
cd uavatt-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# uavpos-genom3
echo "=========================================="
echo "Building uavpos-genom3 ..."
echo "=========================================="
cd ../..
cd uavpos-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# maneuver-genom3
echo "=========================================="
echo "Building maneuver-genom3 ..."
echo "=========================================="
cd ../..
cd maneuver-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# ----------------
# OpenRobots components
# ----------------

# pom-genom3
echo "=========================================="
echo "Building pom-genom3 ..."
echo "=========================================="
cd ../..
cd pom-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# optitrack-genom3
echo "=========================================="
echo "Building optitrack-genom3 ..."
echo "=========================================="
cd ../..
cd optitrack-genom3
autoreconf -vif
mkdir -p build && cd build
../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# qualisys-genom3 (optional — uncomment if checked out)
# echo "=========================================="
# echo "Building qualisys-genom3 ..."
# echo "=========================================="
# cd ../..
# cd qualisys-genom3
# autoreconf -vif
# mkdir -p build && cd build
# ../configure --with-templates=pocolibs/server,pocolibs/client/c --prefix="$CONDA_PREFIX" \
#     CPPFLAGS="$CPPFLAGS -I$CONDA_PREFIX/include/qualisys_cpp_sdk"
# make install -j"${CPU_COUNT:-$(nproc)}"

# ----------------
# Gazebo simulation plugins
# ----------------

# optitrack-gazebo
echo "=========================================="
echo "Building optitrack-gazebo ..."
echo "=========================================="
cd ../..
cd optitrack-gazebo
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# libmrsim
echo "=========================================="
echo "Building libmrsim ..."
echo "=========================================="
cd ../..
cd libmrsim
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

# mrsim-gazebo
echo "=========================================="
echo "Building mrsim-gazebo ..."
echo "=========================================="
cd ../..
cd mrsim-gazebo
autoreconf -vif
mkdir -p build && cd build
../configure --prefix="$CONDA_PREFIX"
make install -j"${CPU_COUNT:-$(nproc)}"

echo "=========================================="
echo "Build complete."
echo "Run 'pixi run start' to launch GenoM components."
echo "=========================================="
