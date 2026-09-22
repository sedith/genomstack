## robot-facing API, available when the external genomix binding is installed
try:
    from .mission import Mission
    from .robot_io import RobotIO
except ModuleNotFoundError as e:
    print('module genomix not found, genomstack io not usable for this session')

from .config import Config
from .process import LocalRunner, RemoteTmuxRunner, is_localhost
