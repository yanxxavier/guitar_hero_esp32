"""Serial-to-uinput bridge; no key injection into keyboards or mice."""
import time
from evdev import UInput, AbsInfo, ecodes as e

NAME = 'Guitar Lab Virtual Controller'


def make_device():
    # Generic gamepad capabilities help SDL identify the device as a controller.
    # Only BTN_SOUTH receives hardware input in the one-button prototype.
    caps = {e.EV_KEY: [e.BTN_SOUTH, e.BTN_EAST, e.BTN_NORTH, e.BTN_WEST,
                       e.BTN_TL, e.BTN_TR, e.BTN_SELECT, e.BTN_START, e.BTN_MODE],
            e.EV_ABS: [(e.ABS_X, AbsInfo(0, -32768, 32767, 0, 128, 0)),
                       (e.ABS_Y, AbsInfo(0, -32768, 32767, 0, 128, 0))]}
    return UInput(caps, name=NAME, phys='guitar-lab/serial', bustype=e.BUS_VIRTUAL)


class Bridge:
    def __init__(self, factory=make_device, clock=time.monotonic):
        self.factory, self.clock = factory, clock
        self.device = None
        self.pressed = False
        self.last_frame = None
        self.next_retry = 0
        self.sent = 0
        self.error = None
        self.timed_out = False

    def ensure(self):
        if self.device or self.clock() < self.next_retry:
            return
        try:
            self.device = self.factory()
            self.error = None
            self.pressed = False
            self.last_frame = None
        except (OSError, ValueError) as exc:
            self.error = str(exc)
            self.next_retry = self.clock() + 2

    def send(self, pressed):
        if self.device is None or pressed == self.pressed:
            return
        try:
            self.device.write(e.EV_KEY, e.BTN_SOUTH, int(pressed))
            self.device.syn()
            self.pressed = pressed
            self.sent += 1
        except OSError as exc:
            self.error = str(exc)
            self.close()
            self.next_retry = self.clock() + 2

    def frame(self, pressed):
        self.last_frame = self.clock()
        self.timed_out = False
        self.send(pressed)

    def tick(self):
        self.ensure()
        # Firmware v2 emits a state every 250ms, including while held.
        if self.last_frame is not None and self.clock() - self.last_frame > 1.5:
            self.send(False)
            self.timed_out = True

    def release(self):
        self.send(False)
        self.last_frame = None

    def close(self):
        if self.device:
            try:
                self.device.write(e.EV_KEY, e.BTN_SOUTH, 0)
                self.device.syn()
            except OSError:
                pass
            finally:
                self.device.close()
                self.device = None
        self.pressed = False
        self.last_frame = None

    def snapshot(self):
        device = getattr(self.device, 'device', None)
        return dict(ready=self.device is not None, name=NAME, button='BTN_SOUTH',
                    pressed=self.pressed, sent=self.sent, error=self.error,
                    timed_out=self.timed_out, event_path=getattr(device, 'path', None),
                    firmware_required='BUTTON-TEST v2')
