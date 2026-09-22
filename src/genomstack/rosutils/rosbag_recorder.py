import shlex
from ..process import LocalRunner, RemoteTmuxRunner, is_localhost, shell_path


class RosbagRecorder:
    def __init__(self, cfg):
        self.cfg = cfg

        ## select a runner on the same host as the robot stack
        if is_localhost(cfg.host):
            self.runner = LocalRunner(workspace=cfg.root, setup=cfg.setup)
        else:
            self.runner = RemoteTmuxRunner(
                host=cfg.host,
                setup=cfg.setup,
                session='genomstack_rosbag',
            )
        self.recording = False

    def start_log(self):
        if self.recording:
            return

        ## build the topic list and host-appropriate output path
        topics = ' '.join(shlex.quote(topic) for topic in self.cfg.ros2_bag_topics)
        output_path = shell_path(
            self.cfg.tmp_path / 'bag',
            expand=is_localhost(self.cfg.host),
        )

        ## start recording after the runner applies the global setup chain
        self.runner.start(
            'rosbag',
            f'ros2 bag record -o {output_path} {topics}',
        )
        self.recording = True

    def stop_log(self):
        if self.recording:
            self.runner.stop('rosbag')
            self.recording = False
