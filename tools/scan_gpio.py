"""Read temporary PINSCAN v3; never flash, create a controller or save a mapping.

The operator changes --stage-file between requested physical buttons. All raw
edges are written to --log for review; simultaneous pins are not auto-assigned.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import serial
from desktop.ownership import Ownership

PINS=(0,2,4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33,34,35,36,39)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',required=True)
    parser.add_argument('--stage-file',type=Path,required=True)
    parser.add_argument('--log',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=900)
    args=parser.parse_args()
    args.log.parent.mkdir(parents=True,exist_ok=True)
    owner=Ownership().acquire()
    try:
        with serial.Serial(args.port,115200,timeout=.1,exclusive=sys.platform!='win32') as dev,args.log.open('a',encoding='utf8') as out:
            dev.dtr=False;dev.rts=True;time.sleep(.1);dev.rts=False
            deadline=time.monotonic()+args.seconds;identified=False;confirmed=False;previous=None
            while time.monotonic()<deadline:
                line=dev.readline(512).decode('utf8',errors='replace').strip()
                if line=='GUITARHERO PINSCAN v3':identified=True;confirmed=False;previous=None
                if identified and line.startswith('PINS '):
                    if tuple(map(int,line[5:].split(',')))!=PINS:raise ValueError('Lista de GPIOs inesperada.')
                    confirmed=True;print(line,flush=True)
                match=re.fullmatch(r'SCAN (\d{1,10})',line)
                if not confirmed or not match:continue
                mask=int(match[1])
                if mask >= 1<<len(PINS):raise ValueError('Máscara de GPIO inválida.')
                if mask==previous:continue
                try:stage=args.stage_file.read_text(encoding='utf8').strip()
                except OSError:stage='sem etapa'
                row=dict(time=time.time(),stage=stage,initial=previous is None,
                         down=[pin for i,pin in enumerate(PINS) if mask&(1<<i)],
                         pressed=[] if previous is None else [pin for i,pin in enumerate(PINS) if mask&(1<<i) and not previous&(1<<i)],
                         released=[] if previous is None else [pin for i,pin in enumerate(PINS) if previous&(1<<i) and not mask&(1<<i)])
                previous=mask;text=json.dumps(row,ensure_ascii=False);out.write(text+'\n');out.flush();print(text,flush=True)
            if not confirmed:raise RuntimeError('O ESP32 não enviou PINSCAN v3. Nenhum mapa foi criado.')
    finally:owner.close()

if __name__=='__main__':main()
