"""Safety of the virtual output, independent of OS permissions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'dashboard'))
from bridge import Bridge

class Device:
    def __init__(self):
        self.frames = []
        self.closed = False
    def write(self, kind, code, value): self.frames.append(value)
    def syn(self): pass
    def close(self): self.closed = True

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.device = Device()
        self.bridge = Bridge(lambda: self.device, lambda: self.now)
        self.bridge.ensure()
    def test_duplicate_heartbeat_does_not_repeat_press(self):
        self.bridge.frame(True)
        self.bridge.frame(True)
        self.bridge.frame(False)
        self.assertEqual(self.device.frames, [1, 0])
    def test_held_button_heartbeats_keep_output_down(self):
        self.bridge.frame(True)
        for i in range(1, 20):
            self.now = i * .25
            self.bridge.frame(True)
            self.bridge.tick()
        self.assertTrue(self.bridge.pressed)
        self.assertEqual(self.device.frames, [1])
    def test_silence_releases_output(self):
        self.bridge.frame(True)
        self.now = 2
        self.bridge.tick()
        self.assertFalse(self.bridge.pressed)
        self.assertTrue(self.bridge.timed_out)
        self.assertEqual(self.device.frames, [1, 0])
    def test_disconnect_releases_output(self):
        self.bridge.frame(True)
        self.bridge.release()
        self.assertEqual(self.device.frames, [1, 0])
    def test_close_releases_and_destroys_device(self):
        self.bridge.frame(True)
        self.bridge.close()
        self.assertEqual(self.device.frames, [1, 0])
        self.assertTrue(self.device.closed)
        self.assertIsNone(self.bridge.device)
    def test_permissions_failure_does_not_crash_or_claim_ready(self):
        def denied(): raise PermissionError('uinput denied')
        bridge = Bridge(denied, lambda: self.now)
        bridge.tick()
        bridge.frame(True)
        self.assertFalse(bridge.snapshot()['ready'])
        self.assertEqual(bridge.sent, 0)

if __name__ == '__main__': unittest.main()
