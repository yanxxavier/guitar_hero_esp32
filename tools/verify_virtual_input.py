"""Reads only this project's virtual controller, never other input devices."""
from contextlib import closing
import argparse
import select
import time
from evdev import InputDevice, ecodes
parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=120)
args = parser.parse_args()
from pathlib import Path
paths = [Path('/dev/input') / node.parents[1].name for node in Path('/sys/class/input').glob('event*/device/name') if node.read_text().strip() == 'Guitar Lab Virtual Controller']
if not paths:
    raise SystemExit('Controle virtual não encontrado.')
with closing(InputDevice(str(paths[0]))) as device:
    print(f'Observando {device.path}: {device.name}', flush=True)
    deadline = time.monotonic() + args.seconds
    while time.monotonic() < deadline:
        ready, _, _ = select.select([device], [], [], min(1, max(0, deadline-time.monotonic())))
        if ready:
            for event in device.read():
                if event.type == ecodes.EV_KEY:
                    print(f'{event.timestamp():.6f} {ecodes.BTN[event.code]} {event.value}', flush=True)
