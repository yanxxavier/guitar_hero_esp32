"""Painel de bancada local. Iniciar com .venv/bin/python dashboard/server.py."""
import argparse
import atexit
import signal
import sys
import json
import re
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import serial

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from bridge import Bridge
BRIDGE = Bridge()
STOP = threading.Event()
PROJECT = ROOT.parent
PORT = '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'
LOCK = threading.RLock()
DATA = PROJECT / 'logs' / 'dashboard'
DATA.mkdir(parents=True, exist_ok=True)
CHECKS = DATA / 'checks.json'
try:
    checks = json.loads(CHECKS.read_text())
except (OSError, ValueError):
    checks = {}
state = dict(whammy_raw=None, whammy_min=None, whammy_max=None, connected=False, status='Procurando ESP32', port=PORT, pressed=None,
             presses=0, releases=0, strum_pressed=None, strum_presses=0, strum_releases=0, firmware=None, last_event=None, started=time.time(),
             events=deque(maxlen=120), checks=checks, error=None)


def event(kind, message):
    item = dict(time=datetime.now().astimezone().isoformat(timespec='milliseconds'), kind=kind, message=message)
    with LOCK:
        state['events'].appendleft(item)
        with (DATA / 'events.jsonl').open('a') as log:
            log.write(json.dumps(item, ensure_ascii=False) + '\n')


def consume(line):
    with LOCK:
        if line.startswith('GUITARHERO '):
            state['firmware'] = line
            event('firmware', line)
        elif re.fullmatch(r'(?:BUTTON [01]|STATE [0-3](?: [0-9]{1,4})?)', line):
            parts = line.split()
            mask = int(parts[1])
            raw = int(parts[2]) if len(parts) == 3 else None
            if raw is not None and raw > 4095:
                event('serial', 'Quadro analógico inválido: ' + line)
                return
            state['whammy_raw'] = raw
            if raw is not None:
                state['whammy_min'] = raw if state['whammy_min'] is None else min(raw, state['whammy_min'])
                state['whammy_max'] = raw if state['whammy_max'] is None else max(raw, state['whammy_max'])
            state['last_frame'] = time.time()
            BRIDGE.frame(mask, raw if raw is not None else 0)
            for bit, field, presses, releases, name in [
                (1, 'pressed', 'presses', 'releases', 'GREEN · D15'),
                (2, 'strum_pressed', 'strum_presses', 'strum_releases', 'PALHETADA · D13')
            ]:
                value = bool(mask & bit)
                old = state[field]
                state[field] = value
                if old is not None and old != value:
                    state[presses if value else releases] += 1
                if old != value:
                    state['last_event'] = time.time()
                    event('button', name + (' · PRESSIONADO' if value else ' · SOLTO'))
        elif line:
            event('serial', line[:400])


def disconnect(message):
    with LOCK:
        BRIDGE.release()
        state.update(connected=False, whammy_raw=None, pressed=None, strum_pressed=None, error=message, status='Aguardando conexão')


def reader():
    while not STOP.is_set():
        try:
            with serial.Serial(state['port'], 115200, timeout=.1, exclusive=True) as device:
                with LOCK:
                    state.update(connected=True, whammy_raw=None, pressed=None, strum_pressed=None, firmware=None, error=None, status='Serial conectada')
                event('connection', 'ESP32 conectado · 115200 baud')
                # Reset with button released; obtains identification and current state.
                device.dtr = False
                device.rts = True
                time.sleep(.1)
                device.rts = False
                while not STOP.is_set():
                    raw = device.readline(512)
                    if raw:
                        consume(raw.decode('utf-8', errors='replace').strip())
        except (serial.SerialException, OSError) as exc:
            was_connected = state['connected']
            disconnect(str(exc))
            if was_connected:
                event('connection', 'Serial desconectada; estado do botão desconhecido')
            time.sleep(2)


def snapshot():
    with LOCK:
        return {**state, 'bridge': BRIDGE.snapshot(), 'events': list(state['events']), 'uptime': round(time.time() - state['started'])}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, body, content_type='application/json', code=200):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/api/state', '/api/report'):
            self.send(json.dumps(snapshot(), ensure_ascii=False).encode())
        else:
            files = {'/': ('index.html', 'text/html; charset=utf-8'),
                     '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                     '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if self.path not in files:
                self.send(b'Not found', 'text/plain', 404)
                return
            name, mime = files[self.path]
            self.send((ROOT / 'static' / name).read_bytes(), mime)

    def do_POST(self):
        # Accept mutations only from this same-origin local page.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            self.send(b'{}', code=403)
            return
        size = int(self.headers.get('Content-Length', 0))
        if size > 4096:
            self.send(b'{}', code=413)
            return
        try:
            payload = json.loads(self.rfile.read(size) or '{}')
            with LOCK:
                if self.path == '/api/reset':
                    state.update(whammy_min=state["whammy_raw"], whammy_max=state["whammy_raw"], presses=0, releases=0, strum_presses=0, strum_releases=0, started=time.time())
                    event('session', 'Nova contagem iniciada')
                elif self.path == '/api/check':
                    key = payload['key']
                    if key not in ['serial', 'button', 'nine', 'whammy', 'linux', 'ally', 'assembly', 'music']:
                        raise ValueError('Unknown check')
                    state['checks'][key] = bool(payload['value'])
                    CHECKS.write_text(json.dumps(state['checks']))
                else:
                    self.send(b'{}', code=404)
                    return
            self.send(b'{"ok":true}')
        except (ValueError, KeyError, TypeError):
            self.send(b'{}', code=400)


def bridge_worker():
    while not STOP.wait(.1):
        with LOCK:
            was_ready = BRIDGE.device is not None
            BRIDGE.tick()
            if not was_ready and BRIDGE.device is not None:
                event('bridge', 'Controle virtual criado · Green BTN_SOUTH / Palhetada BTN_EAST')


def stop(*_):
    STOP.set()
    with LOCK:
        BRIDGE.close()


def terminate(*_):
    raise SystemExit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=PORT)
    parser.add_argument('--http-port', type=int, default=8765)
    args = parser.parse_args()
    state['port'] = args.port
    atexit.register(stop)
    signal.signal(signal.SIGTERM, terminate)
    threading.Thread(target=bridge_worker, daemon=True).start()
    threading.Thread(target=reader, daemon=True).start()
    print(f'Guitar Lab: http://127.0.0.1:{args.http_port}', flush=True)
    try:
        ThreadingHTTPServer(('127.0.0.1', args.http_port), Handler).serve_forever()
    finally:
        stop()
