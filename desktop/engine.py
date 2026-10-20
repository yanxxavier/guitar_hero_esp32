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
    from dashboard.bridge import Bridge
    return Bridge()

class Engine:
    def __init__(self, profile):
        self.profile = copy.deepcopy(profile)
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.commands = queue.Queue()
        self.thread = None
        self.output = None
        self.raw_mask = 0
        self.reported = list(config.DEFAULT_PINS)
        self.last_frame = None
        self.pending = None
        self.state = dict(connected=False, firmware='', status='Desconectado', error='',
                          mask=0, raw=0, edge_seq=0, last_pin=None, port='',
                          counts=[0]*9, holds=[0.0]*9, since=[None]*9, logs=[], output={},
                          profile=copy.deepcopy(profile), reported_pins=self.reported[:], configured=False)
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
        with self.lock:
            if self.state['connected'] and not self.state['configured'] and not set(profile['pins']).issubset(self.reported):
                raise ValueError('Esse GPIO exige o firmware configurável v11. Instale-o pela aba Configuração.')
        self.commands.put(('profile', copy.deepcopy(profile)))
        if not (self.thread and self.thread.is_alive()):
            with self.lock:
                self.profile = copy.deepcopy(profile)
                config.save(self.profile)
                self.state['profile_revision'] += 1

    def consume(self, line):
        if line.startswith('GUITARHERO '):
            if 'CHANNELS v10' not in line and 'CONFIG v11' not in line:
                raise ValueError('Firmware incompatível. Instale CHANNELS v10 ou CONFIG v11.')
            self.state['firmware'] = line
            self.state['configured'] = 'CONFIG v11' in line
            self.reported = list(config.DEFAULT_PINS)
            self.log(line)
            return
        if line.startswith('PINS '):
            pins = config.validate_pins([int(s) for s in line[5:].split(',')])
            self.reported = pins
            self.state['reported_pins'] = pins[:]
            if self.pending and pins == self.pending[0]['pins']:
                self.profile = self.pending[0]
                self.pending = None
                config.save(self.profile)
                self.state['profile_revision'] += 1
                self.log('Pinagem gravada e confirmada pelo ESP32.')
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
                    with serial.Serial(selected, 115200, timeout=.03, write_timeout=1, exclusive=sys.platform!='win32') as dev:
                        with self.lock:
                            self.state.update(connected=True, firmware='', configured=False, port=selected, status='Identificando ESP32', error='')
                            self.last_frame = None
                            self.raw_mask = 0
                            self.pending = None
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
                                    if self.pending:
                                        raise ValueError('Aguarde a confirmação da pinagem anterior.')
                                    if self.state['configured'] and profile['pins'] != self.reported:
                                        self.output.release()
                                        self.pending = (profile, time.monotonic())
                                        dev.write(('CFG PINS ' + ','.join(map(str, profile['pins'])) + '\n').encode())
                                        self.log('Aplicando pinagem no ESP32…')
                                    elif set(profile['pins']).issubset(self.reported):
                                        self.output.release()
                                        self.profile = profile
                                        config.save(profile)
                                        self.state['profile_revision'] += 1
                                        self.log('Perfil atualizado.')
                                    else:
                                        self.state['error'] = 'GPIO novo exige firmware configurável v11.'
                                if self.pending and time.monotonic() - self.pending[1] > 3:
                                    self.pending = None
                                    self.state['error'] = 'ESP32 não confirmou a pinagem; perfil anterior mantido.'
                                if self.last_frame is not None and time.monotonic() - self.last_frame > 1.5:
                                    self.output.release()
                                    self.state.update(mask=0, since=[None]*9, status='Sem dados do ESP32', error='Estado liberado por segurança.')
                                if self.last_frame is None and time.monotonic() - opened > 8:
                                    raise ValueError('O dispositivo não enviou o protocolo da guitarra. Confira a porta e o firmware.')
                                self.output.tick()
                except (OSError, serial.SerialException, ValueError) as exc:
                    with self.lock:
                        self.state.update(connected=False, mask=0, status='Aguardando conexão', error=str(exc))
                        self.log(str(exc))
                    self.stop_event.wait(1)
                finally:
                    with self.lock:
                        if self.output:
                            self.output.close()
                            self.output = None
                        self.state.update(connected=False, mask=0, since=[None]*9)
                        self.last_frame = None
        except RuntimeError as exc:
            with self.lock:
                self.state.update(error=str(exc), status='Outra instância está usando a guitarra')
        finally:
            owner.close()
            with self.lock:
                self.state.update(connected=False, mask=0, status='Desconectado')
