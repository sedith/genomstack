#!/bin/bash

## GLOBAL KILL SCRIPT

pkill -9 mrsim-pocolibs  &
pkill -9 optitrack-pocol &
pkill -9 rotorcraft-poco &
pkill -9 pom-pocolibs    &
pkill -9 maneuver-pocoli &
pkill -9 phynt-pocolibs  &
pkill -9 nhfc-pocolibs   &
pkill -9 uavatt-pocolibs &
pkill -9 uavpos-pocolibs &
pkill -9 uavmpc-pocolibs &
pkill -9 camgazebo-pocol &
pkill -9 t265-pocolibs   &
pkill -9 d435-pocolibs   &
pkill -9 camviz-pocolibs &
pkill -9 arucotag-pocoli &
pkill -9 ikf-pocolibs    &
pkill -9 tagcontrol-poco &
pkill -9 joystick-pocoli &
pkill -9 tagodom-pocolib &
pkill -9 genomixd        &
sleep 0.3
h2 end

rm ~/.*.pid-`hostname`
