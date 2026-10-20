"""Safety of the virtual output, independent of OS permissions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'dashboard'))
from bridge import Bridge
from evdev import ecodes as e

class Device:
    def __init__(self):
        self.frames = []
        self.codes = []
        self.closed = False
    def write(self, kind, code, value):
        self.frames.append(value)
        self.codes.append((code, value))
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
        self.assertEqual(self.device.frames, [1] + [0] * 9)
        self.assertTrue(self.device.closed)
        self.assertIsNone(self.bridge.device)
    def test_permissions_failure_does_not_crash_or_claim_ready(self):
        def denied(): raise PermissionError('uinput denied')
        bridge = Bridge(denied, lambda: self.now)
        bridge.tick()
        bridge.frame(True)
        self.assertFalse(bridge.snapshot()['ready'])
        self.assertEqual(bridge.sent, 0)

    def test_strum_transitions_preserve_green(self):
        for mask in [1, 3, 1, 3, 1]: self.bridge.frame(mask)
        self.assertEqual(self.device.codes, [(e.BTN_SOUTH, 1), (e.BTN_MODE, 1), (e.BTN_MODE, 0), (e.BTN_MODE, 1), (e.BTN_MODE, 0)])
        self.assertEqual(self.bridge.mask, 1)

    def test_timeout_releases_both_buttons(self):
        self.bridge.frame(3)
        self.now = 2
        self.bridge.tick()
        self.assertEqual(self.bridge.mask, 0)
        self.assertEqual(self.device.codes[-2:], [(e.BTN_SOUTH, 0), (e.BTN_MODE, 0)])

    def test_analog_changes_preserve_held_buttons_and_ignore_duplicates(self):
        self.bridge.frame(3, 1000)
        self.bridge.frame(3, 1000)
        self.bridge.frame(3, 4095)
        self.assertEqual(self.device.codes, [(e.BTN_SOUTH, 1), (e.BTN_MODE, 1), (e.ABS_Z, 1000), (e.ABS_Z, 4095)])
        self.assertEqual(self.bridge.mask, 3)

    def test_analog_timeout_and_close_return_to_zero(self):
        self.bridge.frame(0, 2048)
        self.now = 2
        self.bridge.tick()
        self.assertEqual(self.device.codes[-1], (e.ABS_Z, 0))
        self.assertEqual(self.bridge.whammy, 0)
        self.bridge.frame(0, 4095)
        self.bridge.close()
        self.assertEqual(self.device.codes[-1], (e.ABS_Z, 0))

    def test_invalid_analog_never_updates_heartbeat_or_output(self):
        for value in [-1, 4096, 1.5, True]:
            with self.assertRaises(ValueError): self.bridge.frame(3, value)
        self.assertIsNone(self.bridge.last_frame)
        self.assertEqual(self.device.codes, [])

    def test_five_frets_chord_and_partial_release(self):
        self.bridge.frame(61, 2000)
        self.bridge.frame(60, 2000)
        self.assertEqual(self.bridge.mask, 60)
        self.assertEqual(self.device.codes[-1], (e.BTN_SOUTH, 0))
        self.now = 2
        self.bridge.tick()
        self.assertEqual(self.bridge.mask, 0)
        self.assertEqual(self.bridge.whammy, 0)
        self.assertIn((e.BTN_TR, 0), self.device.codes)

    def test_new_commands_and_chord_preserve_frets(self):
        self.bridge.frame(61, 1000)
        self.bridge.frame(61 | 256, 1000)
        self.assertEqual(self.device.codes[-1], (e.BTN_EAST, 1))
        self.bridge.frame(61 | 2 | 64 | 128, 1000)
        self.assertTrue(self.bridge.pressed)
        self.assertIn((e.BTN_START, 1), self.device.codes)
        self.assertIn((e.BTN_SELECT, 1), self.device.codes)
        self.assertIn((e.BTN_MODE, 1), self.device.codes)
        self.bridge.release()
        self.assertEqual(self.bridge.mask, 0)
        self.assertEqual(self.bridge.whammy, 0)
        for code in [e.BTN_EAST, e.BTN_MODE, e.BTN_START, e.BTN_SELECT]:
            self.assertIn((code, 0), self.device.codes)

    def test_mask_outside_nine_buttons_is_rejected(self):
        with self.assertRaises(ValueError): self.bridge.frame(512)
        self.assertEqual(self.device.codes, [])

if __name__ == '__main__': unittest.main()
