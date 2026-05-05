"""High-level joystick controller for drone teleoperation."""

from __future__ import annotations

import os
import time
import yaml
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mission import Mission

# Suppress pygame stdout noise; dummy drivers allow headless use
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame  # noqa: E402  (must come after env vars)


_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / 'config' / 'joystick_f710.yaml'


class JoystickController:
    """Logitech F710 joystick controller for manual drone teleoperation.

    Connects to the first detected joystick and runs a blocking control loop.

    Button mapping (XInput mode, switch in 'X' position):
        START       : arm & servo the drone
        Y           : takeoff to cruise altitude
        A           : land
        B           : stop motors (disarm, session stays alive)
        BACK        : emergency stop & quit
        LB (hold)   : enable continuous velocity commands

    Velocity axes (while LB is held):
        Left  stick Y : vz   (altitude)
        Left  stick X : wz   (yaw rate)
        Right stick Y : vx   (forward / backward)
        Right stick X : vy   (left / right)
    """

    CONTROL_RATE: int = 50  # Hz

    def __init__(
        self,
        mission: Mission,
        config: dict | str | Path | None = None,
    ) -> None:
        self.mission = mission

        if config is None:
            config = _DEFAULT_CONFIG
        if not isinstance(config, dict):
            with open(config) as f:
                config = yaml.safe_load(f)
        self.cfg = config

        self._running = False
        self._joystick: pygame.joystick.JoystickType | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Connect to the joystick and start the blocking control loop."""
        self._init_pygame()
        print(f"[joystick] connected: {self._joystick.get_name()}")
        self._running = True
        try:
            self._loop()
        finally:
            pygame.quit()

    def print_help(self) -> None:
        print("""
=== Joystick Control  (Logitech F710 — XInput / 'X' mode) ===
  START       : arm & servo
  Y           : takeoff
  A           : land
  B           : stop motors (disarm)
  BACK        : emergency stop & quit
  LB (hold)   : enable velocity commands

  [while LB held]
  Left  stick Y : altitude     (vz)
  Left  stick X : yaw rate     (wz)
  Right stick Y : fwd / back   (vx)
  Right stick X : left / right (vy)
==============================================================
""")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_pygame(self) -> None:
        pygame.init()
        pygame.joystick.init()
        n = pygame.joystick.get_count()
        if n == 0:
            raise RuntimeError(
                "No joystick detected. Please connect the Logitech F710."
            )
        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()

    def _deadzone(self, value: float) -> float:
        dz = self.cfg.get('deadzone', 0.1)
        return 0.0 if abs(value) < dz else value

    def _read_axis(self, name: str) -> float:
        axis_cfg = self.cfg['axes'][name]
        raw = self._joystick.get_axis(axis_cfg['axis'])
        return self._deadzone(raw) * axis_cfg.get('scale', 1.0)

    def _read_button(self, name: str) -> bool:
        return bool(self._joystick.get_button(self.cfg['buttons'][name]))

    def _loop(self) -> None:
        btn = self.cfg['buttons']
        max_vel = self.cfg.get('max_velocity', 0.5)
        max_yaw = self.cfg.get('max_yaw_rate', 0.5)
        dt = 1.0 / self.CONTROL_RATE

        while self._running:
            t0 = time.monotonic()

            # ---- event-driven button presses ----
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    b = event.button
                    if b == btn['back']:
                        print("[joystick] BACK → emergency stop")
                        self.mission.stop()
                        self._running = False
                    elif b == btn['start']:
                        print("[joystick] START → arm & servo")
                        self.mission.start()
                    elif b == btn['takeoff']:
                        print("[joystick] Y → takeoff")
                        self.mission.takeoff()
                    elif b == btn['land']:
                        print("[joystick] A → land")
                        self.mission.land()
                    elif b == btn['motors_off']:
                        print("[joystick] B → motors off")
                        self.mission.io.components['rotorcraft'].call('stop')

            # ---- continuous velocity control (hold LB to enable) ----
            if self._read_button('enable_manual'):
                vx = self._read_axis('vx') * max_vel
                vy = self._read_axis('vy') * max_vel
                vz = self._read_axis('vz') * max_vel
                wz = self._read_axis('wz') * max_yaw
                self.mission.io.components['maneuver'].call(
                    'velocity',
                    vx=vx, vy=vy, vz=vz, wz=wz,
                    ax=0, ay=0, az=0, duration=0,
                )

            elapsed = time.monotonic() - t0
            remaining = dt - elapsed
            if remaining > 0:
                time.sleep(remaining)
