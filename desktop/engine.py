import copy
import queue
import re
import sys
import threading
import time
from collections import deque
import serial
from serial.tools import list_ports
from . import config
from .ownership import Ownership

def ports():
    return [dict(device=p.device, label=f'{p.device} · {p.description}', preferred=p.vid in (0x1A86, 0x10C4, 0x0403))
            for p in list_ports.comports()]

def output_factory():
    if sys.platform == 'win32':
        from .windows_output import WindowsOutput
        return WindowsOutput()
    if sys.platform == 'darwin':
        from .macos_output import MacOSOutput
        return MacOSOutput()
    from dashboard.bridge import Bridge
    return Bridge()

class Engine:
    def __init__(self, profile):
        self.profile = copy.deepcopy(profile)
        if 'tilt_pin' not in self.profile:
            self.profile['tilt_pin'] = config.DEFAULT_TILT_PIN
        self.profile_initialized = (config.data_dir() / 'profile.json').is_file()
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.commands = queue.Queue()
        self.thread = None
        self.output = None
        self.raw_mask = 0
        self.raw_tilt = None
        self.reported = list(config.DEFAULT_PINS)
        self.reported_tilt = self.profile['tilt_pin']
        self.last_frame = None
        self.pending = None
        self.pending_tilt = None
        self.state = dict(connected=False, firmware='', status='Desconectado', error='',
                          mask=0, raw=0, tilt=False, edge_seq=0, last_pin=None, port='',
                          counts=[0]*10, holds=[0.0]*10, since=[None]*10, logs=[], output={},
                          profile=copy.deepcopy(self.profile), reported_pins=self.reported[:],
                          reported_tilt=self.reported_tilt, configured=False)
        self.state['profile_revision'] = 0

    def log(self, message):
        self.state['logs'] = (self.state['logs'] + [time.strftime('%H:%M:%S') + '  ' + message])[-100:]

    def snapshot(self):
        with self.lock:
            result = copy.deepcopy(self.state)
            result['profile'] = copy.deepcopy(self.profile)
            if self.output:
                result['output'] = self.output.snapshot()
            return result

    def start(self, port=''):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run, args=(port,), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)

    def apply(self, profile):
        config.validate_pins(profile['pins'])
        if 'tilt_pin' in profile:
            config.validate_tilt_pin(profile['tilt_pin'])
        else:
            profile = copy.deepcopy(profile)
            profile['tilt_pin'] = self.profile.get('tilt_pin', config.DEFAULT_TILT_PIN)
        with self.lock:
            if self.state['connected'] and not self.state['configured'] and not set(profile['pins']).issubset(self.reported):
                raise ValueError('Esse GPIO exige o firmware configurável v11. Instale-o pela aba Configuração.')
        self.commands.put(('profile', copy.deepcopy(profile)))
        if not (self.thread and self.thread.is_alive()):
            with self.lock:
                self.profile = copy.deepcopy(profile)
                config.save(self.profile)
                self.profile_initialized = True
                self.state['profile_revision'] += 1

    def consume(self, line):
        if line.startswith('GUITARHERO '):
            if 'CHANNELS v10' not in line and 'CONFIG v11' not in line:
                raise ValueError('Firmware incompatível. Instale CHANNELS v10 ou CONFIG v11.')
            self.state['firmware'] = line
            self.state['configured'] = 'CONFIG v11' in line
            self.reported = list(config.DEFAULT_PINS)
            self.raw_tilt = None
            self.log(line)
            return
        if line.startswith('PINS '):
            pins = config.validate_pins([int(s) for s in line[5:].split(',')])
            self.reported = pins
            self.state['reported_pins'] = pins[:]
            if self.state['configured'] and not self.pending and (not self.profile_initialized or not set(self.profile['pins']).issubset(pins)):
                self.profile['pins'] = pins[:]
                config.save(self.profile)
                self.profile_initialized = True
                self.state['profile_revision'] += 1
                self.log('Pinagem inicial carregada da configuração salva no ESP32.')
            if self.pending and pins == self.pending[0]['pins']:
                self.profile['pins'] = self.pending[0]['pins'][:]
                if not self.pending_tilt:
                    self.profile = self.pending[0]
                self.pending = None
                config.save(self.profile)
                self.profile_initialized = True
                self.state['profile_revision'] += 1
                self.log('Pinagem gravada e confirmada pelo ESP32.')
            return
        if line.startswith('TILT '):
            pin = config.validate_tilt_pin(int(line[5:].strip()))
            self.reported_tilt = pin
            self.state['reported_tilt'] = pin
            if self.state['configured'] and not self.pending_tilt and self.profile.get('tilt_pin') != pin:
                self.profile['tilt_pin'] = pin
                config.save(self.profile)
                self.state['profile_revision'] += 1
                self.log(f'Inclinação (Tilt) carregada do ESP32 em D{pin}.')
            if self.pending_tilt and pin == self.pending_tilt[0].get('tilt_pin'):
                self.profile['tilt_pin'] = pin
                if not self.pending:
                    self.profile = self.pending_tilt[0]
                self.pending_tilt = None
                config.save(self.profile)
                self.profile_initialized = True
                self.state['profile_revision'] += 1
                self.log(f'Inclinação (Tilt) gravada e confirmada pelo ESP32 em D{pin}.')
            return
        tilt_match = re.fullmatch(r'TILT_STATE ([01])', line)
        if tilt_match and self.state['firmware']:
            active = tilt_match.group(1) == '1'
            now = time.monotonic()
            first_tilt = self.raw_tilt is None
            if not first_tilt and active != self.raw_tilt:
                self.state['edge_seq'] += 1
                self.state['last_pin'] = self.reported_tilt
            if active and not self.state['tilt']:
                if not first_tilt:
                    self.state['counts'][9] += 1
                self.state['since'][9] = now
            if not active and self.state['tilt']:
                start = self.state['since'][9]
                self.state['holds'][9] = now - start if start else 0
                self.state['since'][9] = None
            self.raw_tilt = active
            self.state['tilt'] = active
            if self.output and hasattr(self.output, 'set_tilt'):
                self.output.set_tilt(active and not self.pending and not self.pending_tilt)
            return
        match = re.fullmatch(r'STATE (\d{1,3}) (\d{1,4})', line)
        if not match or not self.state['firmware']:
            return
        raw_mask, raw = map(int, match.groups())
        if raw_mask > 511 or raw > 4095:
            return
        now = time.monotonic()
        for pin, bit in zip(self.reported, config.BITS):
            if raw_mask & bit and not self.raw_mask & bit:
                self.state['edge_seq'] += 1
                self.state['last_pin'] = pin
        first = self.last_frame is None
        self.raw_mask = raw_mask
        mask = config.translated_mask(raw_mask, self.reported, self.profile['pins'])
        supported = set(self.profile['pins']).issubset(self.reported)
        if not supported:
            mask = 0
        previous = self.state['mask']
        for i, bit in enumerate(config.BITS):
            if mask & bit and not previous & bit:
                if not first:
                    self.state['counts'][i] += 1
                self.state['since'][i] = now
            if not mask & bit and previous & bit:
                start = self.state['since'][i]
                self.state['holds'][i] = now - start if start else 0
                self.state['since'][i] = None
        self.last_frame = now
        self.state.update(mask=mask, raw=raw, status='Guitarra conectada',
                          error='' if supported else 'O perfil usa GPIOs que o firmware não lê. Grave v11 ou restaure os terminais atuais.')
        if self.output:
            self.output.frame(0 if self.pending else mask, raw if self.profile['whammy'] and not self.pending and supported else 0)

    def run(self, requested):
        owner = Ownership()
        try:
            owner.acquire()
            while not self.stop_event.is_set():
                available = ports()
                preferred = [p['device'] for p in available if p['preferred']]
                selected = requested or self.profile['port'] or (preferred[0] if len(preferred)==1 else '')
                if not selected:
                    with self.lock:
                        self.state.update(status='Selecione a porta USB' if len(preferred)>1 else 'Conecte o ESP32 por USB', error='', connected=False)
                    self.stop_event.wait(1)
                    continue
                try:
                    with serial.Serial(selected, 115200, timeout=.03, write_timeout=1, exclusive=True) as dev:
                        with self.lock:
                            self.state.update(connected=True, firmware='', configured=False, port=selected, status='Identificando ESP32', error='')
                            self.last_frame = None
                            self.raw_mask = 0
                            self.raw_tilt = None
                            self.pending = None
                            self.pending_tilt = None
                            self.output = output_factory()
                            if hasattr(self.output, 'ensure'):
                                self.output.ensure()
                            self.log('USB conectada: ' + selected)
                        dev.dtr = False
                        dev.rts = True
                        self.stop_event.wait(.1)
                        dev.rts = False
                        opened = time.monotonic()
                        while not self.stop_event.is_set():
                            line = dev.readline(512).decode('utf8', errors='replace').strip()
                            with self.lock:
                                if line:
                                    self.consume(line)
                                while not self.commands.empty():
                                    _, profile = self.commands.get_nowait()
                                    if self.pending or self.pending_tilt:
                                        raise ValueError('Aguarde a confirmação da pinagem anterior.')
                                    pins_changed = self.state['configured'] and profile['pins'] != self.reported
                                    tilt_pin = profile.get('tilt_pin', config.DEFAULT_TILT_PIN)
                                    tilt_changed = self.state['configured'] and tilt_pin != self.reported_tilt
                                    if pins_changed or tilt_changed:
                                        self.output.release()
                                        now_cmd = time.monotonic()
                                        if pins_changed:
                                            self.pending = (profile, now_cmd)
                                            dev.write(('CFG PINS ' + ','.join(map(str, profile['pins'])) + '\n').encode())
                                            self.log('Aplicando pinagem no ESP32…')
                                        if tilt_changed:
                                            self.pending_tilt = (profile, now_cmd)
                                            dev.write((f'CFG TILT {tilt_pin}\n').encode())
                                            self.log(f'Aplicando Inclinação (Tilt) em D{tilt_pin} no ESP32…')
                                    elif set(profile['pins']).issubset(self.reported):
                                        self.output.release()
                                        self.profile = profile
                                        config.save(profile)
                                        self.profile_initialized = True
                                        self.state['profile_revision'] += 1
                                        self.log('Perfil atualizado.')
                                    else:
                                        self.state['error'] = 'GPIO novo exige firmware configurável v11.'
                                if self.pending and time.monotonic() - self.pending[1] > 3:
                                    self.pending = None
                                    self.state['error'] = 'ESP32 não confirmou a pinagem; perfil anterior mantido.'
                                if self.pending_tilt and time.monotonic() - self.pending_tilt[1] > 3:
                                    self.pending_tilt = None
                                    self.state['error'] = 'ESP32 não confirmou o pino de Tilt; perfil anterior mantido.'
                                if self.last_frame is not None and time.monotonic() - self.last_frame > 1.5:
                                    self.output.release()
                                    self.state.update(mask=0, tilt=False, since=[None]*10, status='Sem dados do ESP32', error='Estado liberado por segurança.')
                                if self.last_frame is None and time.monotonic() - opened > 8:
                                    raise ValueError('O dispositivo não enviou o protocolo da guitarra. Confira a porta e o firmware.')
                                self.output.tick()
                except (OSError, serial.SerialException, ValueError) as exc:
                    with self.lock:
                        self.state.update(connected=False, mask=0, tilt=False, status='Aguardando conexão', error=str(exc))
                        self.log(str(exc))
                    self.stop_event.wait(1)
                finally:
                    with self.lock:
                        if self.output:
                            self.output.close()
                            self.output = None
                        self.state.update(connected=False, mask=0, tilt=False, since=[None]*10)
                        self.last_frame = None
                        self.raw_tilt = None
        except RuntimeError as exc:
            with self.lock:
                self.state.update(error=str(exc), status='Outra instância está usando a guitarra')
        finally:
            owner.close()
            with self.lock:
                self.state.update(connected=False, mask=0, tilt=False, status='Desconectado')
