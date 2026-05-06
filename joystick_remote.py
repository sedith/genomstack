from genomstack import RobotIO, Mission
from genomstack.joystick import JoystickController


io = RobotIO('tilthex_simu_remote')
io.setup()

mission = Mission(io, fetch_logs=False)
mission.spin()

ctrl = JoystickController(mission, show_gui=True)

ctrl.print_help()
ctrl.run()
