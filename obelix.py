from genomstack import RobotIO, Mission


io = RobotIO('tilthex_simu')
io.setup()

mission = Mission(io)

mission.spin()
mission.start(prompt=True)

mission.goto(-3, 2, 2, 1, prompt=True)
mission.goto(0, 0, 1, 0, prompt=True)

mission.land(prompt=True)

mission.stop(prompt=True)
