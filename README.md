# genomstack

## Table of contents

- [installation](#installation)
- [objective](#objective)
- [concepts](#concepts)
    - [config: the entry point](#config-the-entry-point)
    - [robotio](#robotio)
    - [components](#components)
    - [external publishers](#external-publishers)
    - [sidecars](#sidecars)
- [usage](#usage)
    - [cli](#cli)
    - [workspace structure](#workspace-structure)
    - [configuration file](#configuration-file)
    - [logs](#logs)
    - [mission scripts](#mission-scripts)
    - [how to use it in practice](#how-to-use-it-in-practice)

## Installation

Install the library in editable mode while developing:

```bash
python3 -m pip install -e .
```

The GenoM runtime, component executables, and the robotpkg `genomix` Python module are external dependencies.
ROS 2 is only required by ROS sidecars, launch files, or bag recording.

## Objective

GenomStack simplifies the runtime of GenoM-based simulations and experiments.
It automates most of the repeated setup, process supervision, port wiring, and logging, moving most user effort to a single configuration file.

GenomStack provides a small common layer to describe the robot stack, start it consistently, and handle interactions during missions and with external processes.

## Concepts

### Config: the entry point

Each run starts from one YAML configuration file.
It identifies the host and shell environment, robot properties, GenoM components, port remappings, external publishers, sidecars, and logging policy.

### RobotIO

`RobotIO` is the robot-facing facade used by all processes.
From a given config file, it connects to GenoM through the `python-genomix` interface, loads component handles, and creates the external publishers.

It exposes the common operations needed by an experiment:

* configure and start components with `setup_components()` and `start_components()`
* read component ports with `read()`
* send data through external publishers with `publish()`
* start, stop, and export logs

The `silent=True` option suppresses initialization output and is intended for sidecars that only read and publish data.
It is not a safety mechanism, and every `RobotIO` instance retains access to configuration and lifecycle methods.
The user must ensure that only one experiment executive configures components, controls their lifecycle, and manages logs for a given stack.

### Components

Each GenoM component is handled by a Python wrapper describing how this component type is configured, wired, started, and logged.
In the YAML, each key is a running instance name and its `type` selects the component wrapper.
`RobotIO` builds these wrappers and gives access to their raw services through `component.call()`.

Each component contains two functions:

* `setup()` applies component configuration and port wiring
* `start()` activates runtime behavior when the experiment begins

All wrappers inherit from the `Component` base class and implement `setup()` and `start()` to apply parameters and connect ports.
They can override `start_log()`, and `stop_log()` when their lifecycle or logging differs from the defaults.

`RobotIO.start_components()` sorts wrappers by `START_ORDER`, so dependencies start before their consumers.

Each wrapper defines nominal port connections, while the config file can override them with `remap` entries keyed as `<instance>.<local-port>`.

### External publishers

External publishers let a non-GenoM process publish to a GenoM input port.
A config file names the target component, its publisher factory, and the port exposed by the external process.

```yaml
external_publishers:
    controller:
        target: uavatt
        publisher: uav_input
        port: controller/uav_input
```

Publishing is handled through the `RobotIO` interface with `io.publish('controller', message)`.

### Sidecars

Sidecars are non-GenoM, non-interactive processes that run alongside the components, such as controllers, sensor relays, ROS bridges, visualizers, simulators...
The sidecars are listed in the config file and started and managed automatically alongside the GenoM components.

Reusable sidecars are installed with `genomstack`, while specific ones live in the user workspace.

## Usage

### CLI

Installing the package provides the following commands:

```bash
genomstack_start <config>
genomstack_run <config> <sidecar>
genomstack_ros <config> <launchfile> [arguments ...]
```

which are defined as

* `genomstack_start` starts the GenoM runtime, genomixd, all configured component processes, and all sidecars
* `genomstack_run` starts and supervises one configured sidecar
* `genomstack_ros` runs one script from `ros/launch/`

Each command owns the processes it starts, keeps running while it supervises them, and stops them on keyboard interrupt.

Shell completion discovers configurations, sidecars, and ROS launch scripts.
Enable it once for the current user with the following command.

```bash
activate-global-python-argcomplete --user
```

### Workspace structure

Each workspace using the GenomStack library must follow a semi-rigid structure:

```text
workspace/
├── config/             # YAML configurations
├── calib/              # optional robot calibration files
├── logs/               # exported component logs and bags
├── sidecars/           # optional workspace-specific sidecars
├── ros/                # optional ROS resources
│   ├── launch/
│   └── config/
├── gazebo/             # optional simulation worlds and models
└── main.py             # interactive mission script
```

An example workspace repository will be linked here [TODO put repo link].
The `qrsim` and `txsim` configurations enable basic quadrotor and hexarotor simulations.

The workspace root is derived from the selected config file, which must be located directly inside the workspace's `config/` directory.
This convention lets GenomStack resolve calibration files, sidecars, ROS files, and logs without another workspace setting.

Run commands from the workspace root to use short configuration names.
For example, `qrsim` resolves to `./config/qrsim.yaml`.
Otherwise, explicit relative and absolute configuration paths are also accepted.

### Configuration file

A shortened configuration looks like the following.

```yaml
host: robothost
plugin_paths: [~/genom_devel/lib/genom/pocolibs/plugins]
tmp_path: ~/tmp_genomstack/

setup:
    - source ~/.genom_env.sh
    - source /opt/ros/humble/setup.bash
    - export ROS_DOMAIN_ID=42

inertial:
    mass: 1.67
    Jxx: 0.015
    Jyy: 0.015
    Jzz: 0.007

geom:
    rotors: 4
    armlen: 0.23
    cf: 5.9e-4
    ct: 1e-5
    rx: 0
    rz: -1

components:
    rotorcraft:
        type: rotorcraft
        serial: /tmp/pty-qr
        baud: 0
        calib: robot.json

remap: {}

external_publishers: {}

sidecars:
    gazebo-serv: cd gazebo && gz sim -s -r robot.world
    gazebo-gui: cd gazebo && gz sim -g robot.world

ros2_bag_topics: []
```

The required fields are listed below:

* `host`: machine reached through `genomix` and used for remote bag recording
* `tmp_path`: temporary directory dedicated to genomstack for GenoM logs and ROS bags
* `setup`: shell commands applied before managed processes
* `inertial` and `geom`: shared vehicle parameters
* `components`: component instances and their component-specific settings

The optional fields are listed below:

* `plugin_paths`: GenoM plugin directories passed to `genomix`
* `remap`: port overrides, keyed as `<component>.<local-port>`
* `external_publishers`: publishers used by non-GenoM processes
* `sidecars`: additional processes managed with the components
* `ros2_bag_topics`: ROS 2 topics recorded with the mission

Use `{}`, `[]`, or omit empty optional fields.

Machine-specific paths should be absolute or relative to `~`.

Sidecar commands are resolved according to the following rules:

* an absolute executable is used directly
* a relative path such as `sidecars/controller.py` is resolved from the workspace root
* a bare Python filename such as `rviz_bridge.py` selects a reusable sidecar installed with `genomstack`
* other commands are passed to the shell unchanged

Note for Gazebo: run the server and GUI as separate sidecars.
This lets the process manager stop both reliably, whereas a combined process may leave the server running upon keyboard interrupt.

### Logs

`RobotIO` owns experiment logging:

* component logs and optional ROS bags are first written under `tmp_path`
* a ROS bag is recorded when `ros2_bag_topics` is non-empty, on the configured robot host and through a remote `tmux` session when necessary
* stopping the mission exports the temporary files to a timestamped directory under the workspace's `logs/`

### Mission scripts

A mission script is the experiment executive that configures the components, controls their lifecycle and logging, and runs experiment-specific actions.
It can be autonomous and run on the component host, or interactive and run from a workstation connected through `genomix`.

`Mission` is an optional convenience layer around `RobotIO` for common actions such as spinning the rotors, starting the components, moving with `goto()` or `gotoz()` via the `maneuver` planner, and stopping the experiment.
With `relative=True`, commanded positions and headings are expressed relative to the robot pose captured when the `Mission` is created
(⚠️ in that case, the `io.setup_components()` must be called before the `Mission` constructor, such that the `pom` state-estimator is initialized).

A typical mission script creates `RobotIO`, applies the configuration, and then uses the `Mission` helpers or interacts directly through component calls.

```python
from genomstack import Mission, RobotIO

io = RobotIO('qrsim')
io.setup_components()
mission = Mission(io, relative=True)

io.start_logs()
mission.spin()
mission.start(z_start=0.5, ramp_duration=5, prompt=True)
# experiment-specific commands
mission.gotoz(z=-0.05, prompt=True)
mission.stop(prompt=True)
```

### How to use it in practice

1. install `genomstack`, GenoM, and the required components
2. copy the example workspace or reproduce the structure above
3. create a dedicated config file describing the robot and every process needed by the experiment
4. create experiment-specific sidecars, ROS files, and a `main.py` mission as needed
5. start the runtime from the workspace root
6. in another terminal, run the mission script with the same configuration
