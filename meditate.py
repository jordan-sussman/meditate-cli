#!/usr/bin/env python3
"""
Meditate CLI
Meditative breathing in your terminal.
"""

import argparse
import math
import shutil
import sys
import time
import termios
import tty
from collections import namedtuple
from enum import Enum, auto


class BreathingPhase(Enum):
    INHALE = auto()
    HOLD_IN = auto()
    EXHALE = auto()
    HOLD_OUT = auto()


BreathingPattern = namedtuple("BreathingPattern", ["name", "phases"])


PATTERNS = {
    "box": BreathingPattern(
        name="Box Breathing",
        phases=[
            (BreathingPhase.INHALE, 4.0),
            (BreathingPhase.HOLD_IN, 4.0),
            (BreathingPhase.EXHALE, 4.0),
            (BreathingPhase.HOLD_OUT, 4.0),
        ],
    ),
    "relax": BreathingPattern(
        name="4-7-8 Relaxing Breath",
        phases=[
            (BreathingPhase.INHALE, 4.0),
            (BreathingPhase.HOLD_IN, 7.0),
            (BreathingPhase.EXHALE, 8.0),
            (BreathingPhase.HOLD_OUT, 0.0),
        ],
    ),
    "equal": BreathingPattern(
        name="Equal Breathing (4-4)",
        phases=[
            (BreathingPhase.INHALE, 4.0),
            (BreathingPhase.HOLD_IN, 0.0),
            (BreathingPhase.EXHALE, 4.0),
            (BreathingPhase.HOLD_OUT, 0.0),
        ],
    ),
    "coherent": BreathingPattern(
        name="Coherent Breathing (5-5)",
        phases=[
            (BreathingPhase.INHALE, 5.0),
            (BreathingPhase.HOLD_IN, 0.0),
            (BreathingPhase.EXHALE, 5.0),
            (BreathingPhase.HOLD_OUT, 0.0),
        ],
    ),
    "triangle": BreathingPattern(
        name="Triangle Breathing (4-4-4)",
        phases=[
            (BreathingPhase.INHALE, 4.0),
            (BreathingPhase.HOLD_IN, 4.0),
            (BreathingPhase.EXHALE, 4.0),
            (BreathingPhase.HOLD_OUT, 0.0),
        ],
    ),
}

COLOR_RESET = "\033[0m"
COLOR_BREATH = "\033[38;5;117m"
COLOR_TEXT = "\033[38;5;250m"
COLOR_ACCENT = "\033[38;5;121m"
COLOR_DIM = "\033[38;5;234m"

ASPECT_RATIO = 2.1
MIN_RADIUS = 4.0
FPS = 60


class TerminalRenderer:
    @staticmethod
    def clear_screen() -> None:
        sys.stdout.write("\033[H\033[J")

    @staticmethod
    def hide_cursor() -> None:
        sys.stdout.write("\033[?25l")

    @staticmethod
    def show_cursor() -> None:
        sys.stdout.write("\033[?25h")

    @staticmethod
    def get_terminal_size() -> tuple[int, int]:
        size = shutil.get_terminal_size((80, 24))
        return size.columns, size.lines

    def draw_frame(self, scale: float, label: str, session_progress: float, phase: BreathingPhase) -> None:
        cols, rows = self.get_terminal_size()
        center_x, center_y = cols // 2, rows // 2
        max_radius = min(cols // 4, rows // 2) - 3
        core_radius = MIN_RADIUS + (max_radius - MIN_RADIUS) * scale
        current_color = COLOR_ACCENT if phase in (BreathingPhase.HOLD_IN, BreathingPhase.HOLD_OUT) else COLOR_BREATH
        frame = [[" " for _ in range(cols)] for _ in range(rows)]
        
        for y in range(rows):
            dy = y - center_y

            for x in range(cols):
                dx = (x - center_x) / ASPECT_RATIO
                dist_sq = dx**2 + dy**2
                dist = math.sqrt(dist_sq)
                
                if abs(dist - core_radius) < 0.8:
                    char = "●" if scale > 0.6 else "•"
                    frame[y][x] = f"{current_color}{char}{COLOR_RESET}"
                elif dist < core_radius and (x + y) % 12 == 0:
                    frame[y][x] = f"{COLOR_DIM}.{COLOR_RESET}"

        label_text = label.upper()
        label_start = center_x - (len(label_text) // 2)

        for i, char in enumerate(label_text):
            if 0 <= label_start + i < cols:
                frame[center_y][label_start + i] = f"{COLOR_ACCENT}{char}{COLOR_RESET}"

        prog_bar_len = min(cols - 10, 40)
        filled = int(session_progress * prog_bar_len)
        prog_bar = f"[{'=' * filled}{' ' * (prog_bar_len - filled)}]"
        prog_start = center_x - (len(prog_bar) // 2)
        prog_y = rows - 1
        
        for i, char in enumerate(prog_bar):
            if 0 <= prog_start + i < cols:
                frame[prog_y][prog_start + i] = f"{COLOR_TEXT}{char}{COLOR_RESET}"

        sys.stdout.write("\033[H" + "\n".join("".join(row) for row in frame))
        sys.stdout.flush()


class MeditationEngine:
    def __init__(self, pattern: BreathingPattern, total_duration_mins: float):
        self.pattern = pattern
        self.total_duration = total_duration_mins * 60
        self.start_time = 0.0
        self.cycle_duration = sum(p[1] for p in pattern.phases)
        self.cycles_completed = 0
        self._last_time_in_cycle = 0.0

    def start(self):
        self.start_time = time.perf_counter()

    def get_status(self, current_time: float) -> tuple[BreathingPhase, float, float, float, bool]:
        elapsed = current_time - self.start_time
        session_progress = min(elapsed / self.total_duration, 1.0)
        time_in_cycle = elapsed % self.cycle_duration
        
        if time_in_cycle < self._last_time_in_cycle:
            self.cycles_completed += 1
        self._last_time_in_cycle = time_in_cycle

        if elapsed >= self.total_duration and time_in_cycle < 0.1:
            return BreathingPhase.HOLD_OUT, 1.0, 1.0, 0.0, True
        
        current_offset = 0.0

        for phase, duration in self.pattern.phases:
            if current_offset <= time_in_cycle < current_offset + duration:
                phase_elapsed = time_in_cycle - current_offset
                phase_progress = phase_elapsed / duration if duration > 0 else 1.0
                
                if phase == BreathingPhase.INHALE:
                    scale = phase_progress
                elif phase == BreathingPhase.HOLD_IN:
                    scale = 1.0
                elif phase == BreathingPhase.EXHALE:
                    scale = 1.0 - phase_progress
                else:
                    scale = 0.0
                
                return phase, phase_progress, session_progress, scale, False
            current_offset += duration
            
        return BreathingPhase.HOLD_OUT, 0.0, session_progress, 0.0, False


def get_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def interactive_setup() -> tuple[BreathingPattern, float]:
    pattern_keys = list(PATTERNS.keys())
    selected_idx = 0

    while True:
        TerminalRenderer.clear_screen()
        print(f"\n{COLOR_ACCENT}🧘 Welcome to Meditate CLI{COLOR_RESET}\n")
        print("Select a breathing pattern (Use ↑/↓ and Enter):\n")

        for i, key in enumerate(pattern_keys):
            pattern = PATTERNS[key]
            if i == selected_idx:
                print(f"{COLOR_ACCENT}  > {pattern.name} ({key}){COLOR_RESET}")
            else:
                print(f"    {pattern.name} ({key})")

        key = get_key()

        if key == '\x1b[A':
            selected_idx = (selected_idx - 1) % len(pattern_keys)
        elif key == '\x1b[B':
            selected_idx = (selected_idx + 1) % len(pattern_keys)
        elif key in ('\r', '\n'):
            selected_key = pattern_keys[selected_idx]
            break
        elif key == '\x03':
            raise KeyboardInterrupt

    print(f"\nSelected: {COLOR_ACCENT}{PATTERNS[selected_key].name}{COLOR_RESET}")
    duration_input = input("Enter session duration in minutes [default: 5.0]: ").strip()

    try:
        duration = float(duration_input) if duration_input else 5.0
    except ValueError:
        duration = 5.0

    return PATTERNS[selected_key], duration


def main() -> None:
    renderer = TerminalRenderer()
    
    try:
        if len(sys.argv) == 1:
            pattern, duration = interactive_setup()
        else:
            parser = argparse.ArgumentParser(
                description="A calming meditation CLI that guides your breathing with ASCII animations.",
                epilog="Example: python meditate.py --pattern relax --duration 10"
            )
            parser.add_argument("--pattern", choices=list(PATTERNS.keys()), default="box")
            parser.add_argument("--duration", type=float, default=5.0)
            args = parser.parse_args()
            pattern = PATTERNS[args.pattern]
            duration = args.duration

        engine = MeditationEngine(pattern, duration)
        
        renderer.hide_cursor()
        renderer.clear_screen()
        
        for i in range(5, 0, -1):
            renderer.clear_screen()
            cols, rows = renderer.get_terminal_size()
            msg = f"{COLOR_ACCENT}Settle in... {i}{COLOR_RESET}"
            sys.stdout.write(f"\033[{rows//2}H\033[{cols//2 - len(msg)//2}C{msg}")
            sys.stdout.flush()
            time.sleep(1)
        
        renderer.clear_screen()
        engine.start()
        
        frame_time = 1.0 / FPS
        
        while True:
            start_loop = time.perf_counter()
            phase, _, session_progress, scale, finished = engine.get_status(start_loop)
            
            if finished:
                break
                
            phase_label = phase.name.replace("_", " ")
            renderer.draw_frame(scale, phase_label, session_progress, phase)
            
            elapsed = time.perf_counter() - start_loop
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        pass
    finally:
        renderer.clear_screen()
        renderer.show_cursor()
        final_msg = f"{COLOR_ACCENT}Meditation complete. Namaste.{COLOR_RESET}"
        if 'engine' in locals():
            stats_msg = f"{COLOR_TEXT}You completed {engine.cycles_completed} full breathing cycles.{COLOR_RESET}"
            print(f"\n{final_msg}\n{stats_msg}\n")
        else:
            print(f"\n{final_msg}\n")


if __name__ == "__main__":
    main()
