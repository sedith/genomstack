from genomstack import RobotIO, Mission
from genomstack.joystick import JoystickController


io = RobotIO('tilthex_simu')
io.setup()

mission = Mission(io)
mission.spin()

ctrl = JoystickController(mission)
ctrl.print_help()
ctrl.run()
