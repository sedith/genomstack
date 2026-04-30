# genom_obelix

Small python wrapper to launch, configure and control GenoM components for aerial robots setup.

This repository contains the experiment configuration, launch scripts, ROS 2 helpers, and mission scripts used to operate the robot.

A python package, called `genomstack`, provides a reusable API that abstracts the genom component stack.

The goal is to make common experiment workflows easier:

- start GenoM components
- configure the robot stack
- optionally run ROS 2 nodes for lidar / LIO / visualization
- run missions
- retrieve logs and bags after experiments

## Requirements

This assumes that the genom environment is installed and correctly configured on the local and remote hosts.
Similarly, gazebo, ROS2 etc, should be installed and configured before run.

To handle remote launching of modules, please make sure that the robot host is properly configured in `~/.ssh/config`:

```sshconfig
Host <robot host>
    HostName <robot ip>
    User <robot user>
    ForwardAgent yes
```

Then the config can simply use:

```yaml
host: <robot host>
```

### Remote execution

The config specifies `workspace`: the path to where this repository is cloned on the remote robot. It is needed so remote scripts can run commands such as:
```bash
cd ~/workspace
python3 ros2/launcher.py tilthex.yaml
```

## Installation

From the workspace root:

```bash
git clone https://github.com/sedith/genom_obelix.git
cd genom_obelix
pip install -e .
```

## Repository layout

```text
workspace/
    config/             # yaml configuration files
    calib/              # imu calibration files
    logs/               # logfiles and ROS bags
    gz/                 # some simulation worldfile
    ros2/
        config/         # ROS 2 parameter files
        launcher.py     # ROS 2 pipeline launcher
        bag_record.py   # ROS 2 bag recorder
    src/genomstack/     # python api for genom stack
        config.py           # parsed config file with dict-like and/or attribute access
        runtime.py          # genom layer interface (gemomix...)
        robotio.py          # low-level GenoM I/O layer
        mission.py          # high-level mission interface
        components/         # component abstraction
            base.py
            rotorcraft.py    
            ...
    obelix.py           # main entry point (mission launch script)
    lio_relay.py        # background ROS2->genom relay for lio
    ...                 # other scripts
```

## Experiment specification

Users interact with the obelix from a declarative standpoint, through a YAML config file.

The config defines:
* runtime parameters as `host` and `workspace`
* robot parameters such as `mass`, `geom`
* list of genom components to load and their configuration
* list of external publishers to specific component ports
* optional ROS 2 settings

Component keys are the names of the running instances (`-i` for pocolibs). The `type` field selects the actual genom component wrapper. The remaining fields are used to provide component-specific configurarion parameters.

For instance:
```yaml
components:
    mocap:
        type: optitrack
        host: localhost
        port: "1509"
```
will load a component running via `optitrack-pocolibs -f -i mocap &`,
and configure it with `mocap.connect('localhost', '1509')`.


## Running an experiment

### 1. Start the GenoM processes

For now, this is still done through shell scripts.

```bash
./bin/start_genom.sh
```

> Be careful to match instance names with those in the configuration yaml 
> A python script to handle auto start of components (local and remote) is still a todo

### 2. Optionally start ROS 2 processing

The ROS 2 launcher reads the main config, which should contain:
```yaml
ros2:
    enabled: true
    ...
```

Run with:
```bash
python3 ros2/launcher.py <cfg_file>.yaml
```

ROS 2 nodes run on the same host as the GenoM components.

```bash
python3 ros2/launcher.py <cfg_file>.yaml
```

### 3. Run the mission

The mission management is handled with an high-level API in python:

```python
from genomstack import Mission

m = Mission("tilthex")

m.setup()
m.spin()
m.start(prompt=True)

m.takeoff(1, prompt=True)
m.goto(0, 0, 1.0, 0.0, duration=5, prompt=True)

m.land(prompt=True)
m.stop(prompt=True)
```

> Note: Individual components can still be accessed easily to do custom mission launch

## `genomstack` Python package

The `genomstack` package is the Python API used to interact with the GenoM stack.

Main layers:

* `Config`
    * loads the experiment YAML file to python, providing dict-like and attribute-style access
    * resolves useful paths such as calibration files and log directories
* `Runtime`
    * connects to `genomix`
    * loads genom components
* `Component`
    * each component is wrapped in a class inheriting the `Component` base
    * for each component, a specific `setup()` procedure is defined (set parameters, connect ports, etc)
    * provides access to the component API with `call()` and `connect_port()`
* `ExternalPublisher`
    * used to feed custom data into a component, for example lidar or estimator output into `pom`
    * creates the pocolibs port file in `/tmp/`, connects it to the target component port
    * assumes the user provides the correctly formatted GenoM message dictionary
* `RobotIO`
    * interface to the whole robot stack
    * owns the runtime, components, and external publishers
    * provides `setup()`, `read()` for each component, and `publish()` for each external publisher
* `Mission`
    * high-level experiment/flight interface
    * owns a `RobotIO`
    * provides user-facing methods such as `spin()`, `start()`, `takeoff()`, `goto()`, `land()`, `stop()`
    * handles experiment recording through genom logs and ROS bags

## ROS 2

The ROS 2 folder is kept outside the python package. It is an add-on around the experiment, rather than part of the core genom API.

The main config still contains the ROS 2 options so that the experiment is described in one place.

### ROS 2 setup

The launcher sources the setup files listed in the config:

```yaml
ros2:
  setup:
    - /opt/ros/humble/setup.bash
    - ~/ros2_ws/install/setup.bash
```

This means you do not need to manually source ROS 2 before running:
```bash
python3 ros2/launcher.py tilthex.yaml
```

### ROS domain

Set the ROS domain in the config:

```yaml
ros2:
  domain_id: 42
```

The launcher exports:

```bash
ROS_DOMAIN_ID=42
ROS_LOCALHOST_ONLY=0
```

Use the same domain for the robot-side ROS nodes and local RViz. -->

## Logs and bags

ROS bag and genom logs are handled by the `Mission` layer. They are generated in `/tmp/` on the host then copied locally. Each experiment creates one log directory `logs/<date>`.

For remote experiments, logs and bags are retrieved with `scp`.

## Disclaimers

This stack is currently designed for development use.

Important rules:

* only one `main` process should call `RobotIO.setup()` for a given robot
* other background processes should normally use only `read()` and `publish()`
* remote log and bag retrieval assumes SSH/SCP are configured correctly

## TODO

to be tested:
* ROS 2 launcher
* ROS bag start/stop from `Mission`
* retrieve remote logs and bags

to be implemented:
* genom components launcher for local and remote hosts
* script to run genom components running remotely on robot
* script for publishing to pom (lio relay)
* gz lidar and imu to test stuff in sim
