"""Verifica contagem de eventos sem tocar no hardware ou nos logs reais."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('dashboard_server', Path(__file__).parents[1] / 'dashboard/server.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.DATA = Path(self.temp.name)
        app.state.update(frets=app.new_frets(), whammy_raw=None, whammy_min=None, whammy_max=None, pressed=None, presses=0, releases=0, connected=True, strum_pressed=None, strum_presses=0, strum_releases=0)
        app.state['events'].clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_first_state_is_not_a_press(self):
        app.consume('BUTTON 1')
        self.assertTrue(app.state['pressed'])
        self.assertEqual(app.state['presses'], 0)

    def test_duplicates_do_not_inflate_counts(self):
        for line in ['BUTTON 0', 'BUTTON 1', 'BUTTON 1', 'BUTTON 0', 'BUTTON 0']:
            app.consume(line)
        self.assertEqual((app.state['presses'], app.state['releases']), (1, 1))

    def test_disconnect_removes_stale_pressed_state(self):
        app.consume('BUTTON 1')
        app.disconnect('USB removido')
        self.assertIsNone(app.state['pressed'])
        self.assertFalse(app.state['connected'])
        app.consume('BUTTON 0')
        self.assertEqual(app.state['releases'], 0)

    def test_boot_noise_is_not_button_input(self):
        app.consume('rst:0x1 (POWERON_RESET)')
        app.consume('BUTTON unexpected')
        self.assertIsNone(app.state['pressed'])
        self.assertEqual(app.state['presses'], 0)

    def test_strum_does_not_release_held_green(self):
        for line in ['STATE 0', 'STATE 1', 'STATE 3', 'STATE 1']:
            app.consume(line)
        self.assertTrue(app.state['pressed'])
        self.assertFalse(app.state['strum_pressed'])
        self.assertEqual((app.state['presses'], app.state['releases']), (1, 0))
        self.assertEqual((app.state['strum_presses'], app.state['strum_releases']), (1, 1))

    def test_invalid_state_does_not_change_inputs(self):
        app.consume('STATE 0')
        app.consume('STATE 64')
        app.consume('STATE -1')
        self.assertFalse(app.state['pressed'])
        self.assertFalse(app.state['strum_pressed'])

    def test_disconnect_clears_both_indicators(self):
        app.consume('STATE 3')
        app.disconnect('USB removido')
        self.assertIsNone(app.state['pressed'])
        self.assertIsNone(app.state['strum_pressed'])

    def test_full_frames_track_analog_range_without_button_counts(self):
        for line in ['STATE 1 0', 'STATE 1 2048', 'STATE 1 4095']:
            app.consume(line)
        self.assertEqual((app.state['whammy_raw'], app.state['whammy_min'], app.state['whammy_max']), (4095, 0, 4095))
        self.assertTrue(app.state['pressed'])
        self.assertEqual(app.state['presses'], 0)
        app.disconnect('removed')
        self.assertIsNone(app.state['whammy_raw'])

    def test_invalid_analog_rejects_entire_frame(self):
        app.consume('STATE 0 1000')
        for line in ['STATE 3 4096', 'STATE 3 -1', 'STATE 3 abc', 'STATE 3 20 extra']:
            app.consume(line)
        self.assertEqual(app.state['whammy_raw'], 1000)
        self.assertFalse(app.state['pressed'])
        self.assertFalse(app.state['strum_pressed'])

    def test_each_fret_and_chords_keep_independent_counts(self):
        app.consume('STATE 0 1000')
        for bit in [1, 4, 8, 16, 32]:
            app.consume(f'STATE {bit} 1000')
            app.consume('STATE 0 1000')
        app.consume('STATE 61 2000')
        app.consume('STATE 60 2000')
        self.assertFalse(app.state['frets']['green']['pressed'])
        for key in ['red', 'yellow', 'blue', 'orange']:
            self.assertTrue(app.state['frets'][key]['pressed'])
        app.disconnect('removed')
        self.assertTrue(all(f['pressed'] is None for f in app.state['frets'].values()))
        app.consume('STATE 0 1000')
        self.assertEqual(app.state['frets']['orange']['releases'], 1)

if __name__ == '__main__':
    unittest.main()
