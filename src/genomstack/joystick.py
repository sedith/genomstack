"""High-level joystick controller for drone teleoperation."""

from __future__ import annotations

import os
import math
import time
import threading
import yaml
from pathlib import Path
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .mission import Mission

import pygame  # noqa: E402

from .joystick_gui import JoystickGUI


_DEFAULT_CONFIG = Path(__file__).resolve().parent.parent.parent / 'config' / 'joystick.yaml'


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

    CONTROL_RATE: int = 50   # Hz — joystick / velocity control loop
    GUI_RATE:     int = 10   # Hz — pygame window refresh
    BATTERY_INTERVAL: float = 5.0  # seconds between battery reads

    def __init__(
        self,
        mission: Mission,
        config: dict | str | Path | None = None,
        show_gui: bool = False,
    ) -> None:
        self.mission = mission

        if config is None:
            config = _DEFAULT_CONFIG
        if not isinstance(config, dict):
            with open(config) as f:
                config = yaml.safe_load(f)
        # If the config has a 'controllers' map, resolution is deferred until
        # the joystick name is known (_resolve_controller is called from _init_pygame).
        self._raw_config = config
        self.cfg = config  # may be replaced after controller detection

        self._show_gui = show_gui
        self._gui: JoystickGUI | None = None

        self._running = False
        self._joystick: pygame.joystick.JoystickType | None = None
        self._custom_buttons: dict[int, tuple[str, Callable]] = {}
        self._cycle_buttons: dict[int, dict] = {}
        self._active_button: int | None = None
        self._last_gui_draw:   float = 0.0
        self._last_battery_read: float = 0.0
        self._cached_battery_v: float | None = None
        self._sequence_thread: threading.Thread | None = None
        self._manual_thread: threading.Thread | None = None
        self._manual_stop = threading.Event()
        # Serialise ALL genomix calls across threads: the genomix event loop
        # (event.mux.wait) is not thread-safe and a concurrent call can
        # silently consume a done-event meant for another thread's .wait().
        self._genomix_lock = threading.Lock()
        self._cached_state: dict | None = None
        # Raw registrations — resolved to button indices after _init_pygame()
        # finalises self.cfg (needed when config uses a 'controllers' map).
        self._button_registrations: list[tuple] = []
        self._cycle_registrations:  list[tuple] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def register_button(
        self,
        button: str | int,
        callback: Callable,
        label: str | None = None,
    ) -> None:
        """Bind a custom callback to a button.

        The callback runs in a background thread so blocking sequences
        (e.g. a series of ``mission.goto(…, ack=True)`` calls) do not
        stall the control loop.  Only one custom sequence runs at a time;
        pressing the button while a sequence is already running is ignored.

        Args:
            button: Either a named key from the config ``buttons`` section
                    (e.g. ``'x'``) or a raw pygame button index (int).
            callback: Zero-argument callable to execute on button press.
            label:    Optional human-readable description shown in the help
                      text and log messages.  Defaults to the callback name.
        """
        self._button_registrations.append((button, label or callback.__name__, callback))

    def register_button_cycle(
        self,
        button: str | int,
        callbacks: list[Callable],
        labels: list[str] | None = None,
    ) -> None:
        """Bind a list of callbacks to a button that cycles through them.

        Each press advances to the next callback in the list (wrapping around).
        The same threading rules as :meth:`register_button` apply.

        Args:
            button:    Named key from the config ``buttons`` section or a raw
                       pygame button index.
            callbacks: Ordered list of zero-argument callables to cycle through.
            labels:    Optional list of human-readable names, one per callback.
                       Defaults to each callable's ``__name__``.
        """
        if not callbacks:
            raise ValueError("callbacks list must not be empty")
        if labels is None:
            labels = [cb.__name__ for cb in callbacks]
        if len(labels) != len(callbacks):
            raise ValueError("labels and callbacks must have the same length")
        self._cycle_registrations.append((button, labels, callbacks))

    def _apply_button_registrations(self) -> None:
        """Resolve deferred button registrations now that self.cfg is final."""
        for button, name, callback in self._button_registrations:
            index = self.cfg['buttons'][button] if isinstance(button, str) else int(button)
            self._custom_buttons[index] = (name, callback)
        for button, labels, callbacks in self._cycle_registrations:
            index = self.cfg['buttons'][button] if isinstance(button, str) else int(button)
            self._cycle_buttons[index] = {
                'labels': labels,
                'callbacks': callbacks,
                'index': 0,
            }

    def run(self) -> None:
        """Connect to the joystick and start the blocking control loop."""
        self._init_pygame()
        self._apply_button_registrations()
        print(f"[joystick] connected: {self._joystick.get_name()}")
        self._running = True
        self._manual_stop.clear()
        self._manual_thread = threading.Thread(
            target=self._manual_loop,
            daemon=True,
            name='joystick-manual',
        )
        self._manual_thread.start()
        try:
            self._loop()
        finally:
            self._manual_stop.set()
            self._manual_thread.join(timeout=1.0)
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
        import platform
        _macos = platform.system() == 'Darwin'
        if not _macos and not self._show_gui:
            # dummy driver is fine on Linux/Windows without a GUI, but on macOS
            # it prevents SDL2 from enumerating HID gamepads.
            os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
            os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
        # Deliver joystick events even when the pygame window is not focused.
        os.environ.setdefault('SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS', '1')
        pygame.init()
        if _macos and not self._show_gui:
            # Minimal window required on macOS for HID enumeration to work.
            # When show_gui=True the full GUI window is created below instead.
            pygame.display.set_mode((1, 1))
        elif _macos and self._show_gui:
            # GUI window must exist before joystick.init() on macOS.
            self._gui = JoystickGUI(self.cfg)
            self._gui.init('Initialising…')
        pygame.joystick.init()
        n = pygame.joystick.get_count()
        if n == 0:
            raise RuntimeError(
                "No joystick detected. Please connect the controller."
            )
        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        self._resolve_controller(self._joystick.get_name())
        if self._show_gui:
            if self._gui is None:
                self._gui = JoystickGUI(self.cfg)
                self._gui.init(self._joystick.get_name())
            else:
                # GUI was pre-created on macOS; update cfg and title with real name.
                self._gui._cfg = self.cfg
                self._gui.init(self._joystick.get_name())

    def _resolve_controller(self, joystick_name: str) -> None:
        """If the config has a 'controllers' map, pick the matching entry.

        Matching rules (in order):
        1. The entry key (or its optional `match` field) must be a
           case-insensitive substring of the pygame joystick name.
        2. Among matching entries, if `num_axes` is specified it must equal
           the actual axis count — used to tell D-mode from X-mode F310s.
        """
        controllers = self._raw_config.get('controllers')
        if not controllers:
            return  # flat config — nothing to resolve
        name_lower = joystick_name.lower()
        actual_axes = self._joystick.get_numaxes()

        matched_key = None
        for key, entry in controllers.items():
            pattern = entry.get('match', key).lower()
            if pattern not in name_lower:
                continue
            if 'num_axes' in entry and entry['num_axes'] != actual_axes:
                continue
            matched_key = key
            break

        if matched_key is None:
            raise RuntimeError(
                f"No matching controller config for '{joystick_name}' "
                f"(axes={actual_axes}).\n"
                f"Available entries in config: {list(controllers.keys())}\n"
                f"Add a matching entry to config/joystick.yaml."
            )
        # Merge controller-specific keys over shared top-level defaults
        merged = {k: v for k, v in self._raw_config.items() if k != 'controllers'}
        merged.update({k: v for k, v in controllers[matched_key].items()
                       if k not in ('match', 'num_axes')})
        self.cfg = merged
        print(f"[joystick] using config: '{matched_key}' (matched '{joystick_name}', axes={actual_axes})")

    def _deadzone(self, value: float) -> float:
        dz = self.cfg.get('deadzone', 0.1)
        return 0.0 if abs(value) < dz else value

    def _read_axis(self, name: str) -> float:
        axis_cfg = self.cfg['axes'][name]
        raw = self._joystick.get_axis(axis_cfg['axis'])
        return self._deadzone(raw) * axis_cfg.get('scale', 1.0)

    def _read_button(self, name: str) -> bool:
        return bool(self._joystick.get_button(self.cfg['buttons'][name]))

    def _run_sequence(self, name: str, cb: Callable, button_index: int | None = None) -> None:
        # Hold the lock for the entire sequence: prevents manual velocity
        # commands from interrupting goto activities, and prevents concurrent
        # event.mux.wait() calls from stealing each other's done-events.
        self._active_button = button_index
        try:
            with self._genomix_lock:
                try:
                    cb()
                    print(f"[joystick] {name}: done")
                except Exception as exc:
                    print(f"[joystick] {name}: error — {exc}")
        finally:
            self._active_button = None

    def _collect_diagnostics(self) -> dict:
        """Non-blocking read of robot telemetry for the GUI diagnostics panel.

        All genomix calls are guarded with a non-blocking lock acquisition so
        that this method never races with the manual-control or sequence threads.
        If the lock is busy the cached value is returned as-is.
        """
        diag: dict = {'spinning': self.mission._spinning}
        now = time.monotonic()

        # battery: try to refresh at most once every BATTERY_INTERVAL seconds
        if now - self._last_battery_read >= self.BATTERY_INTERVAL:
            if self._genomix_lock.acquire(blocking=False):
                try:
                    self._last_battery_read = now
                    self._cached_battery_v = self.mission.io.get_battery()
                except Exception as e:
                    print(f'[joystick] battery read failed: {e}')
                finally:
                    self._genomix_lock.release()
        diag['battery_v'] = self._cached_battery_v

        # position / attitude: attempt each GUI cycle, skip if lock is busy
        if self._genomix_lock.acquire(blocking=False):
            try:
                self._cached_state = self.mission.io.get_state()
            except Exception as e:
                print(f'[joystick] pom read failed: {e}')
                self._cached_state = None
            finally:
                self._genomix_lock.release()

        state = self._cached_state
        if state is not None:
            diag['pos'] = state['pos']
            qw, qx, qy, qz = state['att']
            roll  = math.atan2(2*(qw*qx + qy*qz), 1 - 2*(qx*qx + qy*qy))
            pitch = math.asin( max(-1.0, min(1.0, 2*(qw*qy - qz*qx))))
            yaw   = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
            diag['rpy'] = (roll, pitch, yaw)
        else:
            diag['pos'] = None
            diag['rpy'] = None
        return diag

    def _manual_loop(self) -> None:
        """50 Hz background thread: send velocity commands while LB is held.

        Acquires _genomix_lock before each send, so manual control is
        automatically overridden by any other genomix operation (sequences,
        button handlers) that also holds the lock.
        """
        max_vel = self.cfg.get('max_velocity', 0.5)
        max_yaw = self.cfg.get('max_yaw_rate', 0.5)
        dt = 1.0 / self.CONTROL_RATE
        _was_active = False
        while not self._manual_stop.is_set():
            t0 = time.monotonic()
            active = self._read_button('enable_manual')
            if active:
                vx = self._read_axis('vx') * max_vel
                vy = self._read_axis('vy') * max_vel
                vz = self._read_axis('vz') * max_vel
                wz = self._read_axis('wz') * max_yaw
                with self._genomix_lock:
                    self.mission.io.components['maneuver'].call(
                        'velocity',
                        vx=vx, vy=vy, vz=vz, wz=wz,
                        ax=0, ay=0, az=0, duration=0,
                        oneway=True,
                    )
            elif _was_active:
                # LB just released — send one zero-velocity command
                with self._genomix_lock:
                    self.mission.io.components['maneuver'].call(
                        'velocity',
                        vx=0, vy=0, vz=0, wz=0,
                        ax=0, ay=0, az=0, duration=0,
                        oneway=True,
                    )
            _was_active = active
            elapsed = time.monotonic() - t0
            remaining = dt - elapsed
            if remaining > 0:
                time.sleep(remaining)

    def _loop(self) -> None:
        btn = self.cfg['buttons']
        dt = 1.0 / self.CONTROL_RATE

        while self._running:
            t0 = time.monotonic()

            # ---- event-driven button presses ----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("[joystick] window closed → stopping")
                    self._running = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    b = event.button
                    if b == btn['back']:
                        print("[joystick] BACK → emergency stop")
                        with self._genomix_lock:
                            self.mission.stop()
                        self._running = False
                    elif b == btn['start']:
                        print("[joystick] START → arm & servo")
                        with self._genomix_lock:
                            self.mission.start()
                    elif b == btn['takeoff']:
                        print("[joystick] Y → takeoff")
                        with self._genomix_lock:
                            self.mission.takeoff()
                    elif b == btn['land']:
                        print("[joystick] A → land")
                        with self._genomix_lock:
                            self.mission.land()
                    elif b == btn['motors_off']:
                        print("[joystick] B → motors off")
                        with self._genomix_lock:
                            self.mission.stop()
                    elif b in self._custom_buttons:
                        seq_name, cb = self._custom_buttons[b]
                        if self._sequence_thread and self._sequence_thread.is_alive():
                            print(f"[joystick] {seq_name}: sequence already running, ignoring")
                        else:
                            print(f"[joystick] {seq_name}: starting")
                            self._sequence_thread = threading.Thread(
                                target=self._run_sequence,
                                args=(seq_name, cb, b),
                                daemon=True,
                            )
                            self._sequence_thread.start()
                    elif b in self._cycle_buttons:
                        entry = self._cycle_buttons[b]
                        idx = entry['index']
                        seq_name = entry['labels'][idx]
                        cb = entry['callbacks'][idx]
                        n = len(entry['callbacks'])
                        if self._sequence_thread and self._sequence_thread.is_alive():
                            print(f"[joystick] {seq_name}: sequence already running, ignoring")
                        else:
                            print(f"[joystick] {seq_name}: starting ({idx + 1}/{n})")
                            entry['index'] = (idx + 1) % n
                            self._sequence_thread = threading.Thread(
                                target=self._run_sequence,
                                args=(seq_name, cb, b),
                                daemon=True,
                            )
                            self._sequence_thread.start()

            elapsed = time.monotonic() - t0
            remaining = dt - elapsed
            if remaining > 0:
                time.sleep(remaining)
            if self._gui is not None:
                now = time.monotonic()
                if now - self._last_gui_draw >= 1.0 / self.GUI_RATE:
                    self._last_gui_draw = now
                    self._gui.draw(
                        self._joystick,
                        self._read_axis,
                        self._custom_buttons,
                        self._cycle_buttons,
                        self._active_button,
                        self._collect_diagnostics(),
                    )
