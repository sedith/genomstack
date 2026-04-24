#!/bin/bash

h2 init
sleep 0.2
genomixd &
sleep 0.5

optitrack-pocolibs -f &
uavatt-pocolibs -f &
uavpos-pocolibs -f &
rotorcraft-pocolibs -f &
pom-pocolibs -f &
maneuver-pocolibs -f &
nhfc-pocolibs -f &
