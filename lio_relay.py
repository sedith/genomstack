from genomstack import RobotIO
from genomstack.utils import quat2euler
import numpy as np
import time


def jacobian_euler2quat(euler):
    roll, pitch, yaw = euler

    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)

    J = np.zeros((4, 3))

    ## derivatives wrt roll
    J[0, 0] = 0.5 * (-sr * cp * cy + cr * sp * sy)
    J[1, 0] = 0.5 * ( cr * cp * cy + sr * sp * sy)
    J[2, 0] = 0.5 * (-sr * sp * cy + cr * cp * sy)
    J[3, 0] = 0.5 * (-sr * cp * sy - cr * sp * cy)

    ## derivatives wrt pitch
    J[0, 1] = 0.5 * (-cr * sp * cy + sr * cp * sy)
    J[1, 1] = 0.5 * (-sr * sp * cy - cr * cp * sy)
    J[2, 1] = 0.5 * ( cr * cp * cy - sr * sp * sy)
    J[3, 1] = 0.5 * (-cr * sp * sy - sr * cp * cy)

    ## derivatives wrt yaw
    J[0, 2] = 0.5 * (-cr * cp * sy + sr * sp * cy)
    J[1, 2] = 0.5 * (-sr * cp * sy - cr * sp * cy)
    J[2, 2] = 0.5 * (-cr * sp * sy + sr * cp * cy)
    J[3, 2] = 0.5 * ( cr * cp * cy + sr * sp * sy)

    return J


io = RobotIO('tilthex_simu')

var_p = 0.001 ** 2
var_a = 0.001 ** 2
# var_v = 0.1 ** 2
# var_w = 0.1 ** 2

p = [1,1,1]
q = [0,1,0,0]
J = jacobian_euler2quat(quat2euler(q))
cov_p = np.diag([var_p]*3)
cov_euler = np.diag([var_a]*3)
cov_q = J @ cov_euler @ J.T

while 1:
    sec, nsec = divmod(time.time_ns(), 1_000_000_000)
    data = {'measure': {
        'ts': {'sec': sec, 'nsec': nsec},
        'intrinsic': 0,
        'pos': {'x': p[0], 'y': p[1], 'z': p[2]},
        'att': {'qw': q[0], 'qx': q[1], 'qy': q[2], 'qz': q[3]},
        # 'vel': {'vx': v_w[0], 'vy': v_w[1], 'vz': v_w[2]},
        # 'avel': {'wx': w_w[0], 'wy': w_w[1], 'wz': w_w[2]},
        'vel': None,
        'avel': None,
        'acc': None,
        'aacc': None,
        'pos_cov': {'cov': list(cov_p[np.tril_indices(3)])},
        'att_cov': {'cov': list(cov_q[np.tril_indices(4)])},
        'att_pos_cov': {'cov': [0] * 12},
        # 'vel_cov': {'cov': [var_v, 0, var_v, 0, 0, var_v]},
        # 'avel_cov': {'cov': [var_w, 0, var_w, 0, 0, var_w]},
        'vel_cov': None,
        'avel_cov': None,
        'acc_cov': None,
        'aacc_cov': None}
    }
    
    io.publish('lidar', data)

    time.sleep(0.1)
