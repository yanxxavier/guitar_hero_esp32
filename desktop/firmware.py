import shutil
import os
import hashlib
import json
import platform
import tarfile
import tempfile
import urllib.request
import zipfile
import subprocess
import sys
from pathlib import Path
from .config import data_dir
from .runtime import external_env
from .ownership import Ownership

ROOT = Path(__file__).resolve().parents[1]

def cli_path():
    name = 'arduino-cli.exe' if sys.platform == 'win32' else 'arduino-cli'
    installed = data_dir() / 'tools/bin' / name
    if installed.exists():
        return str(installed)
    local = ROOT / '.tools/bin' / name
    return str(local) if local.exists() else shutil.which(name)

def tool_env():
    env = external_env()
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    if (data_dir() / 'tools/isolated.json').exists():
        env['ARDUINO_DIRECTORIES_DATA'] = str(data_dir() / 'tools/arduino-data')
    return env

def prepare(progress=lambda _:None):
    if (ROOT/'firmware/prebuilt/manifest.json').exists():
        prebuilt_images()
        return 'Firmware v11 e gravador incluídos no aplicativo. Nenhuma gravação foi iniciada.'
    cli=cli_path()
    if not cli:
        system='Windows' if sys.platform=='win32' else 'Linux'
        if platform.machine().lower() not in ('x86_64','amd64'):
            raise ValueError('Instalação automática de ferramentas disponível para Linux/Windows 64 bits x86. Instale Arduino CLI manualmente nesta arquitetura.')
        progress('Baixando Arduino CLI oficial…')
        version='1.5.1'
        suffix='zip' if system=='Windows' else 'tar.gz'
        filename=f'arduino-cli_{version}_{system}_64bit.{suffix}'
        release=f'https://github.com/arduino/arduino-cli/releases/download/v{version}/'
        with urllib.request.urlopen(release+f'{version}-checksums.txt',timeout=30) as r:
            checks=r.read().decode()
        expected=next((line.split()[0] for line in checks.splitlines() if line.split() and line.split()[-1].lstrip('*')==filename),None)
        if not expected:raise ValueError('O fabricante não informou o checksum da ferramenta.')
        with tempfile.TemporaryDirectory() as temp:
            archive=Path(temp)/filename
            with urllib.request.urlopen(release+filename,timeout=90) as r,archive.open('wb') as out:
                shutil.copyfileobj(r,out)
            if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
                raise ValueError('Download da ferramenta não passou na verificação SHA256.')
            name='arduino-cli.exe' if system=='Windows' else 'arduino-cli'
            folder=data_dir()/'tools/bin';folder.mkdir(parents=True,exist_ok=True)
            target=folder/name
            if suffix=='zip':
                with zipfile.ZipFile(archive) as z:binary=z.read(name)
            else:
                with tarfile.open(archive) as t:
                    member=t.getmember(name)
                    if not member.isfile():raise ValueError('Pacote da ferramenta inválido.')
                    binary=t.extractfile(member).read()
            target.write_bytes(binary);target.chmod(0o755);cli=str(target)
    env=tool_env()
    listed=subprocess.run([cli,'core','list','--format','json'],capture_output=True,text=True,timeout=60,env=env)
    try:
        installed=json.loads(listed.stdout).get('platforms',[])
        ready=any(p.get('id')=='esp32:esp32' and p.get('installed_version')=='2.0.17' for p in installed)
    except ValueError:ready=False
    if not ready:
        # Install into app-specific Arduino data rather than replacing another project's core.
        env['ARDUINO_DIRECTORIES_DATA']=str(data_dir()/'tools/arduino-data')
        progress('Preparando core ESP32 2.0.17 oficial… o primeiro download pode demorar.')
        url='https://espressif.github.io/arduino-esp32/package_esp32_index.json'
        for args in ([cli,'core','update-index','--additional-urls',url],
                     [cli,'core','install','esp32:esp32@2.0.17','--additional-urls',url]):
            result=subprocess.run(args,capture_output=True,text=True,timeout=900,env=env)
            if result.returncode:raise ValueError((result.stderr or result.stdout)[-4000:])
        marker=data_dir()/'tools/isolated.json';marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text('{}')
    return 'Ferramentas prontas: Arduino CLI e ESP32 2.0.17. Nenhum firmware foi gravado.'

def prebuilt_images():
    folder=ROOT/'firmware/prebuilt'
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('chip')!='esp32' or manifest.get('firmware')!='CONFIG v11':
        raise ValueError('Pacote de firmware incompatível com o ESP32 deste projeto.')
    images=[]
    for entry in manifest['images']:
        name=entry['file']
        if Path(name).name!=name:raise ValueError('Nome de arquivo inválido no pacote de firmware.')
        path=folder/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Firmware corrompido; extraia novamente o pacote da release.')
        images.append((int(entry['address'],16),path))
    if sorted(a for a,_ in images)!=[0x1000,0x8000,0xe000,0x10000]:
        raise ValueError('Mapa de flash inválido no pacote.')
    return images

def upload(port, progress=lambda _:None):
    if not port:raise ValueError('Selecione a porta USB antes de gravar.')
    owner=Ownership().acquire()
    try:
        return _upload(port,progress)
    finally:
        owner.close()

def _upload(port, progress):
    if (ROOT/'firmware/prebuilt/manifest.json').exists():
        import contextlib
        import io
        import esptool
        images=prebuilt_images()
        args=['--chip','esp32','--port',port,'--baud','460800','--before','default-reset','--after','hard-reset',
              'write-flash','--flash-mode','keep','--flash-freq','keep','--flash-size','keep']
        for address,path in images:args.extend([hex(address),str(path)])
        progress('Gravando firmware v11 incluído… mantenha o USB conectado.')
        output=io.StringIO()
        try:
            with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
                try:esptool.main(args)
                except SystemExit as e:
                    if e.code:raise RuntimeError('Gravação falhou: '+output.getvalue()[-3000:]) from e
        except Exception as e:
            raise ValueError(str(e)+'\n'+output.getvalue()[-3000:]) from e
        return 'Firmware v11 gravado e verificado pelo esptool. Reconecte a guitarra.'
    prepare(progress)
    cli = cli_path()
    if not cli:
        raise ValueError('Instale Arduino CLI e o core esp32:esp32 2.0.17 conforme o guia do aplicativo. Nenhuma gravação foi iniciada.')
    if not port: raise ValueError('Selecione a porta USB antes de gravar.')
    sketch = ROOT / 'firmware/configuravel'
    build = data_dir() / 'build/configuravel'
    env = tool_env()
    for args in ([cli, 'compile', '--fqbn', 'esp32:esp32:esp32', '--build-path', str(build), str(sketch)],
                 [cli, 'upload', '--fqbn', 'esp32:esp32:esp32', '--port', port, '--input-dir', str(build), str(sketch)]):
        progress('Compilando…' if 'compile' in args else 'Gravando ESP32… mantenha o USB conectado.')
        result = subprocess.run(args, capture_output=True, text=True, timeout=300, env=env)
        if result.returncode:
            raise ValueError((result.stderr or result.stdout)[-4000:])
    return 'Firmware configurável v11 gravado. Reconecte pela aba Guitarra.'
