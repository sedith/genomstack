from genomstack import Robot, Config


cfg = Config('tilthex_simu')
r = Robot(cfg)

r.setup()
r.spin()
r.start(prompt=True)

r.goto(-5, 2, 3, 1, prompt=True)
r.land(prompt=True)

r.stop(prompt=True)

# # import subprocess
# # subprocess.run("ls -l", shell=True)

# import genomix
# import os
# from math import pi
# import json
# import time
# import numpy as np



# def quat2euler(q):
#     """Compute the euler angles associated to a quaternion.
#     q       -- quaternion with scalar as first element [qw qx qy qz]
#     """
#     q = [q['qw'], q['qx'], q['qy'], q['qz']]
#     roll = np.arctan2(2 * (q[0]*q[1] + q[2]*q[3]), 1 - 2 * (q[1]*q[1] + q[2]*q[2]))
#     pitch = np.arcsin(2 * (q[0]*q[2] - q[3]*q[1]))
#     yaw = np.arctan2(2 * (q[0]*q[3] + q[1]*q[2]), 1 - 2 * (q[2]*q[2] + q[3]*q[3]))
#     return {'roll': np.rad2deg(roll), 'pitch': np.rad2deg(pitch), 'yaw': np.rad2deg(yaw)}


# ## init
# g = genomix.connect('porche')

# # g.rpath(os.environ['ROBOTPKG_BASE'] + '/lib/genom/ros/plugins')
# g.rpath('/home/onepiece/devel/lib/genom/pocolibs/plugins')

# ## load components clients
# # optitrack = g.load('optitrack')
# # mocap = g.load('vicon')
# mocap = g.load('qualisys')
# rotorcraft = g.load('rotorcraft')
# pom = g.load('pom')
# # nhfc = g.load('nhfc')
# uavpos = g.load('uavpos')
# uavatt = g.load('uavatt')
# maneuver = g.load('maneuver')

# ## optitrack
# # optitrack.connect({
# #     'host': 'localhost', 'host_port': '1509', 'mcast': '', 'mcast_port': '0'
# # })

# ## mocap
# mocap.connect('10.135.2.40')

# ## rotorcraft
# # rotorcraft.connect({'serial': '/tmp/pty-tx', 'baud': 0})
# rotorcraft.connect({'serial': '/dev/ttyACM0', 'baud': 0})
# rotorcraft.set_sensor_rate({'rate': {'imu': 1000, 'mag': 0, 'motor': 20, 'battery': 1}})
# rotorcraft.set_imu_filter({'gfc': [20, 20, 20], 'afc': [5, 5, 5], 'mfc': [20, 20, 20]})

# calib = json.load(open("calib/imucalib.json"))
# rotorcraft.set_imu_calibration(calib)

# rotorcraft.connect_port({'local': 'rotor_input', 'remote': 'uavatt/rotor_input'})

# ## pom
# pom.set_prediction_model('::pom::constant_acceleration')
# pom.set_process_noise({'max_jerk': 100, 'max_dw': 50})
# pom.set_history_length({'history_length': 0.25})
# # pom.set_mag_field({'magdir': { 'x': 23.8e-06, 'y': -0.4e-06, 'z': -39.8e-06 }})

# pom.connect_port({'local': 'measure/imu', 'remote': 'rotorcraft/imu'})
# pom.add_measurement('imu')
# # pom.connect_port({'local': 'measure/mag', 'remote': 'rotorcraft/mag'})
# # pom.add_measurement('mag')
# # pom.connect_port({'local': 'measure/mocap', 'remote': 'optitrack/bodies/TX'})
# pom.connect_port({'local': 'measure/mocap', 'remote': 'qualisys/bodies/pcHexa2'})
# pom.add_measurement('mocap')

# # ## nhfc
# # nhfc.set_saturation({'sat': {'x': 1, 'v': 1, 'ix': 0}})
# # nhfc.set_servo_gain({ 'gain': {
# #   'Kpxy': 5, 'Kpz': 5, 'Kqxy': 4, 'Kqz': 4,
# #   'Kvxy': 6, 'Kvz': 6, 'Kwxy': 1, 'Kwz': 1,
# #   'Kixy': 0, 'Kiz': 0
# # }})
# # nhfc.set_control_mode({'att_mode': '::nhfc::tilt_prioritized'})
# # nhfc.set_wlimit({'wmin': 16, 'wmax': 100})
# # nhfc.set_gtmrp_geom({
# #     'rotors': 6, 'cx': 0, 'cy': 0, 'cz': 0, 'armlen': 0.39, 
# #     'mbodyw': 0.2, 'mbodyh': 0.08, 'mmotor': 0.07, 'mass': 3.25,
# #     'rx':-20, 'ry': 0, 'rz': -1, 'cf': 11.4e-4, 'ct': 2.4e-5})
# # nhfc.set_emerg({'emerg': {'descent': 0.1, 'dx': 0.5, 'dq': 1, 'dv': 3, 'dw': 3}})

# # nhfc.connect_port({'local': 'rotor_measure', 'remote': 'rotorcraft/rotor_measure'})
# # nhfc.connect_port({'local': 'state', 'remote': 'pom/frame/robot'})
# # nhfc.connect_port({'local': 'reference', 'remote': 'maneuver/desired'})

# m = 3.22  # 2.93 / 3.22
# ## uavpos/att
# uavpos.set_mass(m)
# uavpos.set_xyradius(2)
# uavpos.set_servo_gain(20, 15, 10, 10, 0, 0)
# uavpos.set_saturation(0.3, 0.2, 0)

# uavpos.connect_port(local='state', remote='pom/frame/robot')
# uavpos.connect_port(local='reference', remote='maneuver/desired')

# uavatt.set_mass(m)
# uavatt.set_gtmrp_geom(rotors=6, armlen=0.39, mass=m, rx=-20, rz=-1, cf=11.4e-4, ct=2.4e-5)
# uavatt.set_servo_gain(15, 15, 1.5, 1)
# uavatt.set_emerg(9.5, 19.5)
# uavatt.set_wlimit(16, 110)

# uavatt.connect_port(local='state', remote='pom/frame/robot')
# uavatt.connect_port(local='uav_input', remote='uavpos/uav_input')
# uavatt.connect_port(local='rotor_measure', remote='rotorcraft/rotor_measure')


# ## maneuver
# maneuver.set_bounds({'xmin': -10, 'xmax': +10, 'ymin': -10, 'ymax': +10, 'zmin': 0, 'zmax': +10, 'yawmin': -2*pi, 'yawmax': +2*pi})

# maneuver.connect_port({'local': 'state', 'remote': 'pom/frame/robot'})

# for _ in [0,1]:
#     time.sleep(2)
#     print('pom:')
#     print(pom.frame('robot')['frame']['pos'])
#     print(quat2euler(pom.frame('robot')['frame']['att']))
#     print('mocap:')
#     print(mocap.bodies('pcHexa2')['bodies']['pos'])
#     print(quat2euler(mocap.bodies('pcHexa2')['bodies']['att']))
#     print()


# input('go?')

# # Start logging the components
# rotorcraft.log('logs/rotorcraft.log')
# pom.log_state('logs/pom.log')
# pom.log_measurements('logs/pom-measurements.log')
# # nhfc.log('logs/nhfc.log')
# uavpos.log('logs/uavpos.log')
# uavatt.log('logs/uavatt.log')
# maneuver.log('logs/maneuver.log')

# rotorcraft.stop()
# rotorcraft.start()

# input('to?')

# # nhfc.set_current_position()
# rotorcraft.servo(ack=True)

# maneuver.set_current_state()
# maneuver.take_off(0.6, 5, ack=True)
# # nhfc.servo(ack=True)
# uavpos.servo(ack=True)
# uavatt.servo(ack=True)


# input('goto?')
# maneuver.goto(1,1,1, 0, 0, ack=True)

# input('goto?')
# maneuver.goto(-1,-1,1, 1.57, 0, ack=True)

# input('goto?')
# maneuver.goto(0,-1,1.5, -1.57, 0, ack=True)

# input('goto?')
# maneuver.goto(1,1,0.8, 0, 0, ack=True)

# input('goto?')
# maneuver.goto(0,0,1, 0, 0, ack=True)

# input('land?')
# maneuver.take_off(0.25, 3, ack=True)

# input('stop?')

# rotorcraft.stop()
# # nhfc.stop()
# uavpos.stop()
# uavatt.stop()
# maneuver.stop()

# rotorcraft.log_stop()
# pom.log_stop()
# # nhfc.log_stop()
# uavpos.log_stop()
# uavatt.log_stop()
# maneuver.log_stop()
