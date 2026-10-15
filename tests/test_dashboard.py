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
        app.state.update(pressed=None, presses=0, releases=0, connected=True)
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

if __name__ == '__main__':
    unittest.main()
