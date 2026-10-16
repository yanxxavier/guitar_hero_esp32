"""Serial-to-uinput bridge; no key injection into keyboards or mice."""
import time
from evdev import UInput, AbsInfo, ecodes as e

NAME = 'Guitar Lab Virtual Controller'
BUTTONS = ((1, e.BTN_SOUTH), (2, e.BTN_EAST), (4, e.BTN_NORTH),
           (8, e.BTN_WEST), (16, e.BTN_TL), (32, e.BTN_TR))


def make_device():
    # Generic gamepad capabilities help SDL identify the device as a controller.
    # D15/18/19/21/13 send five frets; BTN_EAST reserved for historical strum.
    caps = {e.EV_KEY: [e.BTN_SOUTH, e.BTN_EAST, e.BTN_NORTH, e.BTN_WEST,
                       e.BTN_TL, e.BTN_TR, e.BTN_SELECT, e.BTN_START, e.BTN_MODE],
            e.EV_ABS: [(e.ABS_X, AbsInfo(0, -32768, 32767, 0, 128, 0)),
                       (e.ABS_Y, AbsInfo(0, -32768, 32767, 0, 128, 0)),
                       (e.ABS_Z, AbsInfo(0, 0, 4095, 0, 0, 0))]}
    return UInput(caps, name=NAME, phys='guitar-lab/serial', bustype=e.BUS_VIRTUAL)


class Bridge:
    def __init__(self, factory=make_device, clock=time.monotonic):
        self.factory, self.clock = factory, clock
        self.device = None
        self.whammy = 0
        self.mask = 0
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
            self.mask = 0
            self.whammy = 0
            self.last_frame = None
        except (OSError, ValueError) as exc:
            self.error = str(exc)
            self.next_retry = self.clock() + 2

    @property
    def pressed(self):
        return bool(self.mask & 1)

    def send(self, mask, whammy=0):
        if self.device is None or (mask == self.mask and whammy == self.whammy):
            return
        try:
            changed = 0
            for bit, code in BUTTONS:
                if bool(mask & bit) != bool(self.mask & bit):
                    self.device.write(e.EV_KEY, code, int(bool(mask & bit)))
                    changed += 1
            if whammy != self.whammy:
                self.device.write(e.EV_ABS, e.ABS_Z, whammy)
                changed += 1
            self.device.syn()
            self.whammy = whammy
            self.mask = mask
            self.sent += changed
        except OSError as exc:
            self.error = str(exc)
            self.close()
            self.next_retry = self.clock() + 2

    def frame(self, mask, whammy=0):
        if not isinstance(mask, int) or not 0 <= mask <= 63:
            raise ValueError('Invalid input mask')
        if type(whammy) is not int or not 0 <= whammy <= 4095:
            raise ValueError("Invalid whammy value")
        self.last_frame = self.clock()
        self.timed_out = False
        self.send(mask, whammy)

    def tick(self):
        self.ensure()
        # Firmware v7 emits a state every 250ms, including while held.
        if self.last_frame is not None and self.clock() - self.last_frame > 1.5:
            self.send(0)
            self.timed_out = True

    def release(self):
        self.send(0)
        self.last_frame = None

    def close(self):
        if self.device:
            try:
                for _, code in BUTTONS:
                    self.device.write(e.EV_KEY, code, 0)
                if self.whammy:
                    self.device.write(e.EV_ABS, e.ABS_Z, 0)
                self.device.syn()
            except OSError:
                pass
            finally:
                self.device.close()
                self.device = None
        self.mask = 0
        self.whammy = 0
        self.last_frame = None

    def snapshot(self):
        device = getattr(self.device, 'device', None)
        return dict(ready=self.device is not None, name=NAME, button='BTN_SOUTH',
                    pressed=self.pressed, strum_pressed=bool(self.mask & 2), mask=self.mask, sent=self.sent, error=self.error,
                    timed_out=self.timed_out, event_path=getattr(device, 'path', None),
                    firmware_required='FRETS v7', whammy=self.whammy, axis='ABS_Z')
