"""Monitor serial do primeiro botão; Ctrl+C encerra sem alterar firmware."""
import argparse
from datetime import datetime
from pathlib import Path
import time
import serial

parser = argparse.ArgumentParser()
parser.add_argument('--port', default='/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0')
parser.add_argument('--reset', action='store_true', help='reinicia o ESP32 para capturar identificação e pinagem de boot')
args = parser.parse_args()
Path('logs').mkdir(exist_ok=True)
with serial.Serial(args.port, 115200, timeout=1) as device, open('logs/botao-serial.log', 'a', buffering=1) as log:
    print('Monitor ativo: aperte e solte o botão.', flush=True)
    try:
        if args.reset:
            device.dtr = False
            device.rts = True
            time.sleep(.1)
            device.rts = False
            print('ESP32 reiniciado; capturando identificação e pinagem.', flush=True)
        while True:
            raw = device.readline()
            if raw:
                message = raw.decode('utf-8', errors='replace').strip()
                line = f'{datetime.now().astimezone().isoformat()} {message}'
                print(line, flush=True)
                log.write(line + '\n')
    except KeyboardInterrupt:
        pass
