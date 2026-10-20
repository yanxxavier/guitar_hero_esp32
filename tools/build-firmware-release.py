"""Build only project firmware from source; never reads the connected board."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop import firmware

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='firmware/prebuilt');args=parser.parse_args()
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    # Remove no files and never open serial: only CLI core setup and compilation.
    firmware.prepare(print)
    cli=firmware.cli_path();env=firmware.tool_env();build=ROOT/'build/release-firmware'
    subprocess.run([cli,'compile','--fqbn','esp32:esp32:esp32','--build-path',str(build),str(ROOT/'firmware/configuravel')],check=True,env=env)
    data=subprocess.check_output([cli,'config','get','directories.data'],env=env,text=True).strip().strip('"')
    core=Path(data)/'packages/esp32/hardware/esp32/2.0.17'
    source=ROOT/'firmware/configuravel/configuravel.ino'
    entries=[('0x1000',build/'configuravel.ino.bootloader.bin','bootloader.bin'),
             ('0x8000',build/'configuravel.ino.partitions.bin','partitions.bin'),
             ('0xe000',core/'tools/partitions/boot_app0.bin','boot_app0.bin'),
             ('0x10000',build/'configuravel.ino.bin','firmware.bin')]
    images=[]
    for address,path,name in entries:
        target=output/name;shutil.copy2(path,target)
        images.append(dict(address=address,file=name,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (output/'manifest.json').write_text(json.dumps(dict(chip='esp32',firmware='CONFIG v11',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),images=images),indent=2))
    print('Firmware de release compilado; nenhuma leitura ou gravação da placa.')

if __name__=='__main__':main()
