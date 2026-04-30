from genomstack import RobotIO, Mission
import time

io = RobotIO('tilthex')
# io.setup()

# mission = Mission(io)

# mission.start_logs()

# mission.spin()
# mission.start(prompt=True)

# mission.goto(-3, 2, 2, 1, prompt=True)
# mission.goto(0, 0, 1, 0, prompt=True)

# mission.land(prompt=True)

for _ in range(10):
    time.sleep(1)
    print(io.read('pom_lidar', 'frame/robot')['frame']['pos'])


# mission.stop(prompt=True)
