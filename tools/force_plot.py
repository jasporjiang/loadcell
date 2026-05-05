# Author: Shaopeng Jiang 2026.05
#!/usr/bin/env python3
r"""Live force plotter and CSV logger for the force reading output.

Examples:
  python tools\force_plot.py
  python tools\force_plot.py --port COM4
  python tools\force_plot.py --csv data\force_test.csv
  python tools\force_plot.py --no-csv
"""

from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
import threading
import time
from pathlib import Path
from typing import Deque, Optional, Tuple


# User settings. Edit these first for the easiest workflow.
DEFAULT_PORT = "COM4"
DEFAULT_BAUD = 115200
DEFAULT_CSV_PATH = Path("data/force_run.csv")
DEFAULT_PLOT_WINDOW_SECONDS = 20.0
DEFAULT_MAX_POINTS = 5000


FORCE_LINE_RE = re.compile(
    r"(?:force|force_n)\s*[:=]\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def parse_force(line: str) -> Optional[float]:
    """Extract force in newtons from firmware text like 'Force: 0.1234 N'."""
    match = FORCE_LINE_RE.search(line)
    if match:
        return float(match.group(1))

    stripped = line.strip()
    if stripped and NUMBER_RE.fullmatch(stripped):
        return float(stripped)

    return None


def list_serial_ports() -> list[Tuple[str, str]]:
    from serial.tools import list_ports

    return [(port.device, port.description) for port in list_ports.comports()]


def choose_port(port_arg: Optional[str]) -> str:
    if port_arg:
        return port_arg

    ports = list_serial_ports()
    if len(ports) == 1:
        device, description = ports[0]
        print(f"Using {device} ({description})")
        return device

    print("Please specify the serial port, for example:")
    print("  python tools/force_plot.py --port COM4")
    print()

    if ports:
        print("Available ports:")
        for device, description in ports:
            print(f"  {device}: {description}")
    else:
        print("No serial ports found.")

    sys.exit(2)


def read_serial(
    port: str,
    baud: int,
    samples: Deque[Tuple[float, float]],
    lock: threading.Lock,
    stop_event: threading.Event,
    csv_path: Optional[Path],
) -> None:
    import serial

    with serial.Serial(port, baudrate=baud, timeout=1) as ser:
        ser.reset_input_buffer()
        start = time.monotonic()
        csv_file = None
        csv_writer = None

        if csv_path:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_file = csv_path.open("w", newline="", encoding="utf-8")
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["time_s", "force_N"])

        try:
            while not stop_event.is_set():
                raw_line = ser.readline()
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace").strip()
                force = parse_force(line)
                if force is None:
                    print(line)
                    continue

                elapsed = time.monotonic() - start
                with lock:
                    samples.append((elapsed, force))

                if csv_writer:
                    csv_writer.writerow([f"{elapsed:.6f}", f"{force:.6f}"])
                    csv_file.flush()
        finally:
            if csv_file:
                csv_file.close()


def run_plot(
    port: str,
    baud: int,
    window_seconds: float,
    max_points: int,
    csv_path: Optional[Path],
) -> None:
    import matplotlib.animation as animation
    import matplotlib.pyplot as plt

    samples: Deque[Tuple[float, float]] = collections.deque(maxlen=max_points)
    lock = threading.Lock()
    stop_event = threading.Event()

    reader = threading.Thread(
        target=read_serial,
        args=(port, baud, samples, lock, stop_event, csv_path),
        daemon=True,
    )
    reader.start()

    if csv_path:
        print(f"Saving CSV data to: {csv_path}")
    else:
        print("CSV saving disabled.")

    fig, ax = plt.subplots()
    (line,) = ax.plot([], [], linewidth=1.8)
    ax.set_title(f"Load Cell Force ({port}, {baud} baud)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Force (N)")
    ax.grid(True, alpha=0.3)

    def update(_frame: int):
        with lock:
            data = list(samples)

        if not data:
            return (line,)

        xs, ys = zip(*data)
        latest_time = xs[-1]
        min_time = max(0.0, latest_time - window_seconds)

        visible = [(x, y) for x, y in data if x >= min_time]
        visible_xs, visible_ys = zip(*visible)

        line.set_data(visible_xs, visible_ys)
        ax.set_xlim(min_time, max(window_seconds, latest_time + 0.1))

        min_force = min(visible_ys)
        max_force = max(visible_ys)
        padding = max(0.1, (max_force - min_force) * 0.1)
        ax.set_ylim(min_force - padding, max_force + padding)

        return (line,)

    ani = animation.FuncAnimation(fig, update, interval=100, blit=False)

    try:
        plt.show()
    finally:
        stop_event.set()
        reader.join(timeout=1)
        # Keep a reference so matplotlib does not garbage-collect the animation.
        _ = ani


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot loadcell force from serial.")
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        help="Serial port, for example COM4 or /dev/ttyACM0",
    )
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Serial baud rate")
    parser.add_argument(
        "--window",
        type=float,
        default=DEFAULT_PLOT_WINDOW_SECONDS,
        help="Seconds shown in the live plot",
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=DEFAULT_MAX_POINTS,
        help="Maximum samples kept in memory",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="CSV file to write. Edit DEFAULT_CSV_PATH at the top for the normal save location.",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Plot only, without saving data.",
    )
    args = parser.parse_args()

    port = choose_port(args.port)
    csv_path = None if args.no_csv else args.csv
    run_plot(port, args.baud, args.window, args.max_points, csv_path)


if __name__ == "__main__":
    main()
