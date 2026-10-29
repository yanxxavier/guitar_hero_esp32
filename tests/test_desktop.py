import configparser
import io
import hashlib
import json
import tempfile
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from desktop import config, game, music
from desktop.engine import Engine

class DesktopTests(unittest.TestCase):
    def test_confirmed_gpio12_map_is_accepted_without_allowing_gpio2(self):
        confirmed=[16,18,26,33,14,15,12,13,25]
        self.assertEqual(config.validate_pins(confirmed),confirmed)
        with self.assertRaises(ValueError):
            config.validate_pins([16,18,26,33,14,15,2,13,25])

    def test_offline_manual_embeds_all_images_and_version(self):
        from desktop import manual, __version__
        with tempfile.TemporaryDirectory() as temp:
            result=manual.render(Path(temp)/'manual.html').read_text(encoding='utf8')
            self.assertIn(__version__,result)
            self.assertNotIn('{{VERSION}}',result)
            self.assertNotIn('src="manual-assets/',result)
            self.assertEqual(result.count('src="data:image/png;base64,'),3)
            self.assertIn('Windows',result)

    def test_bundled_firmware_is_verified_before_accessing_hardware(self):
        from desktop import firmware
        with tempfile.TemporaryDirectory() as temp,patch('desktop.firmware.ROOT',Path(temp)):
            folder=Path(temp)/'firmware/prebuilt';folder.mkdir(parents=True)
            images=[]
            for address in (0x1000,0x8000,0xe000,0x10000):
                file=hex(address)+'.bin';data=str(address).encode();(folder/file).write_bytes(data)
                images.append(dict(address=hex(address),file=file,sha256=hashlib.sha256(data).hexdigest()))
            (folder/'manifest.json').write_text(json.dumps(dict(chip='esp32',firmware='CONFIG v11',images=images)))
            self.assertEqual(len(firmware.prebuilt_images()),4)
            (folder/images[0]['file']).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'corrompido'):firmware.prebuilt_images()

    def test_external_program_does_not_receive_bundled_libraries(self):
        from desktop.runtime import external_env
        with patch('sys.frozen',True,create=True),patch.dict('os.environ',{'LD_LIBRARY_PATH':'/bundle','LD_LIBRARY_PATH_ORIG':'/system'}):
            self.assertEqual(external_env()['LD_LIBRARY_PATH'],'/system')

    def test_profile_swap_keeps_nine_unique_inputs_and_chords(self):
        swapped=config.swap_pin(config.DEFAULT_PINS,0,18)
        self.assertEqual(swapped[:2],[18,21])
        self.assertEqual(config.translated_mask(4,config.DEFAULT_PINS,swapped),1)
        self.assertEqual(config.translated_mask(5,config.DEFAULT_PINS,swapped),5)
        self.assertEqual(config.translated_mask(0,config.DEFAULT_PINS,swapped),0)

    def test_duplicate_or_output_only_gpio_is_rejected(self):
        for pins in ([21]*9,list(config.DEFAULT_PINS[:-1])+[34],[] ):
            with self.assertRaises(ValueError):config.validate_pins(pins)

    def test_profile_roundtrip_and_broken_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'profile.json';p=config.defaults();p['whammy']=True
            config.save(p,path);self.assertEqual(config.load(path),p)
            path.write_text('{broken');self.assertEqual(config.load(path)['pins'],list(config.DEFAULT_PINS))

    def test_engine_tracks_real_hold_and_remap_without_false_initial_press(self):
        engine=Engine(config.defaults())
        engine.consume('GUITARHERO CHANNELS v10')
        engine.consume('STATE 0 3000')
        engine.consume('STATE 1 3000');start=engine.state['since'][0]
        engine.consume('STATE 257 3000');engine.consume('STATE 1 3000')
        self.assertEqual(engine.state['counts'][0],1)
        self.assertEqual(engine.state['since'][0],start)
        self.assertEqual(engine.state['mask'],1)
        engine.consume('STATE 0 3000');self.assertIsNone(engine.state['since'][0])

    def test_disabled_whammy_is_neutral_at_output(self):
        from unittest.mock import Mock
        engine=Engine(config.defaults());engine.output=Mock()
        engine.consume('GUITARHERO CHANNELS v10');engine.consume('STATE 61 4095')
        engine.output.frame.assert_called_with(61,0)
        engine.profile['whammy']=True;engine.consume('STATE 61 2048')
        engine.output.frame.assert_called_with(61,2048)

    def test_v10_new_gpio_needs_upgrade(self):
        engine=Engine(config.defaults());engine.state['connected']=True
        profile=config.defaults();profile['pins'][0]=25
        with self.assertRaises(ValueError):engine.apply(profile)

    def test_offline_profile_with_new_gpio_cannot_send_misleading_inputs(self):
        from unittest.mock import Mock
        profile=config.defaults();profile['pins'][0]=25
        engine=Engine(profile);engine.output=Mock();engine.consume('GUITARHERO CHANNELS v10')
        engine.consume('STATE 511 4095')
        self.assertEqual(engine.state['mask'],0);self.assertIn('GPIO',engine.state['error'])
        engine.output.frame.assert_called_with(0,0)

    def test_v11_profile_commits_only_after_ack(self):
        engine=Engine(config.defaults());engine.consume('GUITARHERO CONFIG v11')
        profile=config.defaults();profile['pins'][0]=25
        engine.pending=(profile,0)
        with patch('desktop.config.save') as saved:
            engine.consume('PINS 25,18,16,17,15,14,27,13,26')
            self.assertEqual(engine.profile['pins'][0],25);saved.assert_called_once()
        self.assertIsNone(engine.pending)

    def test_setup_preserves_other_settings_and_backs_up(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);path=p/'settings.ini';path.write_text('[game]\nvalue = 42\n\n[audio]\nwhammy_sfx = 1\n')
            profile=config.defaults();profile.update(game_data=temp,songs=str(p/'Songs'))
            with patch('desktop.game.running',return_value=False),patch('desktop.game.data_dir',return_value=p/'app'):
                game.prepare(profile)
            cfg=configparser.ConfigParser();cfg.read(path)
            self.assertEqual(cfg['game']['value'],'42');self.assertEqual(cfg['audio']['whammy_sfx'],'0')
            self.assertEqual(len(list((p/'app/backups').glob('*.ini'))),1)

    def test_setup_refuses_to_edit_running_game(self):
        with patch('desktop.game.running',return_value=True):
            with self.assertRaises(ValueError):game.prepare(config.defaults())

    def test_zip_traversal_rejected_before_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);z=root/'music.zip'
            with zipfile.ZipFile(z,'w') as f:f.writestr('../escape.txt','bad')
            with self.assertRaises(ValueError):music.safe_extract(z,root/'out')
            self.assertFalse((root/'escape.txt').exists())

    def test_zip_does_not_extract_executables(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);z=root/'music.zip'
            with zipfile.ZipFile(z,'w') as f:
                f.writestr('Song/run.exe',b'bad');f.writestr('Song/song.ini','[song]')
            music.safe_extract(z,root/'out')
            self.assertFalse((root/'out/Song/run.exe').exists())
            self.assertTrue((root/'out/Song/song.ini').exists())

    def test_html_cannot_be_installed_as_sng(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.sng';p.write_bytes(b'<html>'+b'x'*2000)
            with self.assertRaises(ValueError):music.validate_sng(p,{'artist':'X','name':'Y'})

    def test_serial_owner_lock_prevents_two_instances(self):
        from desktop.ownership import Ownership
        with tempfile.TemporaryDirectory() as temp,patch('desktop.ownership.data_dir',return_value=Path(temp)):
            first=Ownership().acquire()
            try:
                with self.assertRaises(RuntimeError):Ownership().acquire()
            finally:first.close()
            another=Ownership().acquire();another.close()

    def test_tilt_channel_tracks_state_and_pin_swap(self):
        from unittest.mock import Mock
        engine=Engine(config.defaults());engine.output=Mock()
        engine.consume('GUITARHERO CONFIG v11')
        engine.consume('PINS 16,21,27,17,18,12,13,4,19')
        engine.consume('TILT 15')
        engine.consume('TILT_STATE 0')
        self.assertFalse(engine.state['tilt'])
        self.assertEqual(engine.state['counts'][9],0)
        engine.consume('TILT_STATE 1')
        self.assertTrue(engine.state['tilt'])
        self.assertEqual(engine.state['counts'][9],1)
        engine.output.set_tilt.assert_called_with(True)
        engine.consume('TILT_STATE 0')
        self.assertFalse(engine.state['tilt'])
        pins, tilt = config.swap_with_tilt([16,21,27,17,18,12,13,4,19], 15, 9, 19)
        self.assertEqual(tilt, 19)
        self.assertEqual(pins[-1], 15)

class DesktopUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        cls.qt=QApplication.instance() or QApplication([])

    def test_arrows_select_corresponding_pin_and_results_are_selectable(self):
        from desktop.app import Window
        from PySide6.QtCore import Qt
        with tempfile.TemporaryDirectory() as temp,patch('desktop.config.data_dir',return_value=Path(temp)):
            w=Window(auto=False)
            try:
                self.assertEqual(w.tabs.count(),4)
                self.assertEqual(w.table.rowCount(),10)
                w.guitar.selected.emit(9)
                self.assertEqual(w.selected,9);self.assertEqual(w.pin.currentData(),15)
                w.guitar.selected.emit(3)
                self.assertEqual(w.selected,3);self.assertEqual(w.pin.currentData(),17)
                w.show_results([dict(artist='Linkin Park',name='Numb',charter='Neversoft',notesData={})])
                w.check_all();self.assertEqual(w.songs_table.item(0,0).checkState(),Qt.CheckState.Checked)
                self.assertIsNone(w.engine.thread)
            finally:w.close()

@unittest.skipUnless(sys.platform=='win32','ABI de entrada exclusiva do Windows')
class WindowsAbiTests(unittest.TestCase):
    def test_sendinput_structure_matches_windows_abi_without_sending_keys(self):
        import ctypes
        from desktop.windows_output import WindowsOutput
        output=WindowsOutput()
        self.assertEqual(ctypes.sizeof(output.INPUT),40 if ctypes.sizeof(ctypes.c_void_p)==8 else 28)
        self.assertEqual(output.mask,0)
        output._send(0)  # No changes and therefore no SendInput calls.

    def test_tilt_channel_tracks_state_and_pin_swap(self):
        from unittest.mock import Mock
        engine=Engine(config.defaults());engine.output=Mock()
        engine.consume('GUITARHERO CONFIG v11')
        engine.consume('PINS 16,21,27,17,18,12,13,4,19')
        engine.consume('TILT 15')
        engine.consume('TILT_STATE 0')
        self.assertFalse(engine.state['tilt'])
        self.assertEqual(engine.state['counts'][9],0)
        engine.consume('TILT_STATE 1')
        self.assertTrue(engine.state['tilt'])
        self.assertEqual(engine.state['counts'][9],1)
        engine.output.set_tilt.assert_called_with(True)
        engine.consume('TILT_STATE 0')
        self.assertFalse(engine.state['tilt'])
        pins, tilt = config.swap_with_tilt([16,21,27,17,18,12,13,4,19], 15, 9, 19)
        self.assertEqual(tilt, 19)
        self.assertEqual(pins[-1], 15)

if __name__=='__main__':unittest.main()
