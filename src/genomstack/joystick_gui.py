"""Pygame GUI overlay for the joystick controller."""

from __future__ import annotations

from typing import Callable

import pygame


# ── layout ───────────────────────────────────────────────────────────────────
_GUI_W, _GUI_H = 720, 420
_SPLIT = 355  # x boundary: controller panel | actions panel

# ── colour palette ───────────────────────────────────────────────────────────
_C: dict[str, tuple[int, int, int]] = {
    'bg':      (22,  22,  22),
    'panel':   (38,  38,  38),
    'border':  (68,  68,  68),
    'text':    (215, 215, 215),
    'dim':     (105, 105, 105),
    'accent':  (55,  155, 255),
    'pressed': (255, 195,  45),
    'bar_bg':  (55,  55,  55),
    'sep':     (75,  75,  75),
}


class JoystickGUI:
    """Pygame window that visualises live joystick state and registered actions.

    Lifecycle::

        gui = JoystickGUI(cfg)
        gui.init(joystick_name)   # after pygame.init()
        # inside the main loop:
        gui.draw(joystick, read_axis, custom_buttons, cycle_buttons, active_button)
    """

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._screen: pygame.Surface | None = None
        self._font_hd: pygame.font.Font | None = None
        self._font:    pygame.font.Font | None = None
        self._font_sm: pygame.font.Font | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def init(self, joystick_name: str) -> None:
        """Create the pygame window. Must be called after ``pygame.init()``."""
        self._screen = pygame.display.set_mode((_GUI_W, _GUI_H))
        pygame.display.set_caption(f'Joystick — {joystick_name}')
        self._font_hd = pygame.font.SysFont('monospace', 16, bold=True)
        self._font    = pygame.font.SysFont('monospace', 14)
        self._font_sm = pygame.font.SysFont('monospace', 12)

    def draw(
        self,
        joystick: pygame.joystick.JoystickType,
        read_axis: Callable[[str], float],
        custom_buttons: dict[int, tuple[str, object]],
        cycle_buttons: dict[int, dict],
        active_button: int | None,
    ) -> None:
        """Render one frame. Call at the end of each control-loop iteration."""
        if self._screen is None:
            return
        s = self._screen
        s.fill(_C['bg'])

        self._draw_controller_panel(s, joystick, read_axis)
        self._draw_actions_panel(s, joystick, custom_buttons, cycle_buttons, active_button)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Panel renderers
    # ------------------------------------------------------------------

    def _draw_controller_panel(
        self,
        s: pygame.Surface,
        jy: pygame.joystick.JoystickType,
        read_axis: Callable[[str], float],
    ) -> None:
        pygame.draw.rect(s, _C['panel'], (0, 0, _SPLIT, _GUI_H))
        pygame.draw.line(s, _C['sep'], (_SPLIT, 0), (_SPLIT, _GUI_H), 2)
        hdr = self._font_hd.render('CONTROLLER', True, _C['text'])
        s.blit(hdr, (10, 10))

        n_ax = jy.get_numaxes()
        l_x = jy.get_axis(0) if n_ax > 0 else 0.0
        l_y = jy.get_axis(1) if n_ax > 1 else 0.0
        r_x = jy.get_axis(3) if n_ax > 3 else 0.0
        r_y = jy.get_axis(4) if n_ax > 4 else 0.0
        lt  = (jy.get_axis(2) + 1) * 0.5 if n_ax > 2 else 0.0
        rt  = (jy.get_axis(5) + 1) * 0.5 if n_ax > 5 else 0.0

        # sticks
        self._draw_stick(s,  88, 145, 52, l_x, l_y, 'LEFT')
        self._draw_stick(s, 267, 145, 52, r_x, r_y, 'RIGHT')

        # velocity bars (deadzone + scale applied via read_axis)
        max_vel = self._cfg.get('max_velocity', 0.5)
        max_yaw = self._cfg.get('max_yaw_rate', 0.5)

        def _n(v: float, m: float) -> float:
            return max(-1.0, min(1.0, v / m)) if m else 0.0

        bw, bh = 108, 13
        self._draw_bar(s,  34, 215, bw, bh, _n(read_axis('vz'), max_vel), 'vz')
        self._draw_bar(s,  34, 237, bw, bh, _n(read_axis('wz'), max_yaw), 'wz')
        self._draw_bar(s, 213, 215, bw, bh, _n(read_axis('vx'), max_vel), 'vx')
        self._draw_bar(s, 213, 237, bw, bh, _n(read_axis('vy'), max_vel), 'vy')

        # triggers
        self._draw_trigger(s,  34, 268, 108, 11, lt, 'LT')
        self._draw_trigger(s, 213, 268, 108, 11, rt, 'RT')

        # button chips
        btn = self._cfg['buttons']
        n_btn = jy.get_numbuttons()
        chip_row = [
            (btn['land'],          'A',     28),
            (btn['motors_off'],    'B',     28),
            (btn.get('x', -1),     'X',     28),
            (btn['takeoff'],       'Y',     28),
            (btn['enable_manual'], 'LB',    36),
            (5,                    'RB',    36),
            (btn['back'],          'BACK',  46),
            (btn['start'],         'START', 52),
        ]
        cx = 10
        for idx, lbl, w in chip_row:
            pressed = bool(jy.get_button(idx)) if 0 <= idx < n_btn else False
            self._draw_chip(s, cx, 300, w, 24, lbl, pressed)
            cx += w + 5

    def _draw_actions_panel(
        self,
        s: pygame.Surface,
        jy: pygame.joystick.JoystickType,
        custom_buttons: dict[int, tuple[str, object]],
        cycle_buttons: dict[int, dict],
        active_button: int | None,
    ) -> None:
        x0 = _SPLIT + 12
        hdr = self._font_hd.render('ACTIONS', True, _C['text'])
        s.blit(hdr, (x0, 10))
        pygame.draw.line(s, _C['sep'], (x0, 34), (_GUI_W - 10, 34), 1)

        btn = self._cfg['buttons']
        n_btn = jy.get_numbuttons()
        builtin = [
            (btn['start'],         'START', 'arm & servo'),
            (btn['takeoff'],       'Y',     'takeoff'),
            (btn['land'],          'A',     'land'),
            (btn['motors_off'],    'B',     'stop motors'),
            (btn['back'],          'BACK',  'emergency stop & quit'),
            (btn['enable_manual'], 'LB',    'manual velocity (hold)'),
        ]
        y = 44
        for idx, lbl, desc in builtin:
            active = bool(jy.get_button(idx)) if 0 <= idx < n_btn else False
            self._draw_action_row(s, x0, y, lbl, desc, active)
            y += 26

        if custom_buttons or cycle_buttons:
            pygame.draw.line(s, _C['sep'], (x0, y + 5), (_GUI_W - 10, y + 5), 1)
            y += 14
            for idx, (name, _) in custom_buttons.items():
                self._draw_action_row(s, x0, y, self._btn_name(idx), name,
                                      active_button == idx)
                y += 26
            for idx, entry in cycle_buttons.items():
                n = len(entry['callbacks'])
                next_i = entry['index']
                cur_i = (next_i - 1) % n if active_button == idx else None
                btn_lbl = self._btn_name(idx)
                btn_active = active_button == idx
                for i, label in enumerate(entry['labels']):
                    is_running = btn_active and i == cur_i
                    is_next = not btn_active and i == next_i
                    prefix = '▶ ' if is_running else ('→ ' if is_next else '  ')
                    row_btn_lbl = btn_lbl if i == 0 else ''
                    self._draw_action_row(s, x0, y, row_btn_lbl,
                                          f'{prefix}({i + 1}/{n}) {label}',
                                          is_running, btn_active)
                    y += 22

    # ------------------------------------------------------------------
    # Primitive drawing helpers
    # ------------------------------------------------------------------

    def _btn_name(self, index: int) -> str:
        for name, idx in self._cfg['buttons'].items():
            if idx == index:
                return name.upper()
        return str(index)

    def _draw_stick(
        self,
        s: pygame.Surface,
        cx: int, cy: int, r: int,
        x_val: float, y_val: float,
        label: str,
    ) -> None:
        pygame.draw.circle(s, _C['bg'], (cx, cy), r)
        pygame.draw.circle(s, _C['border'], (cx, cy), r, 2)
        pygame.draw.line(s, _C['border'], (cx - r + 6, cy), (cx + r - 6, cy), 1)
        pygame.draw.line(s, _C['border'], (cx, cy - r + 6), (cx, cy + r - 6), 1)
        dot_r = 9
        dx = int(cx + x_val * (r - dot_r - 2))
        dy = int(cy + y_val * (r - dot_r - 2))
        pygame.draw.circle(s, _C['accent'], (dx, dy), dot_r)
        lbl = self._font_sm.render(label, True, _C['dim'])
        s.blit(lbl, (cx - lbl.get_width() // 2, cy + r + 5))

    def _draw_bar(
        self,
        s: pygame.Surface,
        x: int, y: int, w: int, h: int,
        value: float,
        label: str,
    ) -> None:
        pygame.draw.rect(s, _C['bar_bg'], (x, y, w, h), border_radius=3)
        mid = x + w // 2
        fw = int(abs(value) * w // 2)
        if fw > 0:
            fx = mid if value >= 0 else mid - fw
            pygame.draw.rect(s, _C['accent'], (fx, y, fw, h), border_radius=3)
        pygame.draw.line(s, _C['border'], (mid, y - 2), (mid, y + h + 2), 1)
        lbl = self._font_sm.render(label, True, _C['dim'])
        s.blit(lbl, (x - lbl.get_width() - 4, y + (h - lbl.get_height()) // 2))

    def _draw_trigger(
        self,
        s: pygame.Surface,
        x: int, y: int, w: int, h: int,
        value: float,
        label: str,
    ) -> None:
        pygame.draw.rect(s, _C['bar_bg'], (x, y, w, h), border_radius=3)
        fw = int(value * w)
        if fw > 0:
            pygame.draw.rect(s, _C['accent'], (x, y, fw, h), border_radius=3)
        lbl = self._font_sm.render(label, True, _C['dim'])
        s.blit(lbl, (x - lbl.get_width() - 4, y + (h - lbl.get_height()) // 2))

    def _draw_chip(
        self,
        s: pygame.Surface,
        x: int, y: int, w: int, h: int,
        label: str,
        pressed: bool,
    ) -> None:
        color = _C['pressed'] if pressed else _C['bar_bg']
        tc = (20, 20, 20) if pressed else _C['dim']
        pygame.draw.rect(s, color, (x, y, w, h), border_radius=5)
        pygame.draw.rect(s, _C['border'], (x, y, w, h), 1, border_radius=5)
        t = self._font_sm.render(label, True, tc)
        s.blit(t, (x + (w - t.get_width()) // 2, y + (h - t.get_height()) // 2))

    def _draw_action_row(
        self,
        s: pygame.Surface,
        x: int, y: int,
        btn_label: str,
        description: str,
        active: bool,
        chip_active: bool | None = None,
    ) -> None:
        chip_w, chip_h = 52, 20
        # chip_active overrides `active` for the button chip highlight
        chip_lit = chip_active if chip_active is not None else active
        if btn_label:
            color = _C['pressed'] if chip_lit else _C['bar_bg']
            tc = (20, 20, 20) if chip_lit else _C['dim']
            pygame.draw.rect(s, color, (x, y, chip_w, chip_h), border_radius=4)
            t = self._font_sm.render(btn_label[:7].center(7), True, tc)
            s.blit(t, (x + (chip_w - t.get_width()) // 2, y + (chip_h - t.get_height()) // 2))
        desc_color = _C['pressed'] if active else _C['text']
        desc_t = self._font.render(description, True, desc_color)
        s.blit(desc_t, (x + chip_w + 8, y + (chip_h - desc_t.get_height()) // 2))
