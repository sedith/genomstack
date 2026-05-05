from genomstack import RobotIO, Mission
from genomstack.joystick import JoystickController


io = RobotIO('tilthex_simu')
io.setup()

mission = Mission(io)
mission.spin()

ctrl = JoystickController(mission)

# --- register custom button sequences ---
# The callback runs in a background thread, so blocking (ack=True) calls
# are fine and won't stall the joystick control loop.

def survey1():
    mission.goto(-3,  2, 2, 0, duration=0).wait()
    mission.goto( 3,  2, 2, 0, duration=0).wait()
    
def survey2():
    mission.goto( 3, -2, 2, 0, duration=0).wait()
    mission.goto( 0,  0, 1, 0, duration=0).wait()

# bind to the X button — 'x' is a named alias in joystick_f710.yaml for
# index 2, which has no built-in action and is free for custom use.
# You can also pass a raw button index (int) for any other unclaimed button.
ctrl.register_button_cycle('x', [survey1, survey2], labels=['Survey 1', 'Survey 2'])

ctrl.print_help()
ctrl.run()
