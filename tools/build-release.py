import argparse
import importlib.metadata
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop import __version__,manual,firmware

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-build',action='store_true');args=parser.parse_args()
    firmware.prebuilt_images()
    if not args.skip_build:
        command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--name','GuitarLab',
                 '--collect-all','esptool','--collect-all','esp_pylib','--collect-all','markdown','--copy-metadata','gdown']
        for src,dest in [('docs/manual.md','docs'),('docs/manual-assets','docs/manual-assets'),
                         ('docs/aplicativo.md','docs'),('firmware/prebuilt','firmware/prebuilt'),
                         ('firmware/configuravel/configuravel.ino','firmware/configuravel'),('tools/setup-permissions.sh','tools')]:
            command.extend(['--add-data',src+':'+dest])
        if sys.platform.startswith('linux'):
            libs=list((ROOT/'.tools/qt-runtime/usr/lib').glob('*/libxcb-cursor.so.0'))+list(Path('/usr/lib').glob('*/libxcb-cursor.so.0'))
            if libs:command.extend(['--add-binary',str(libs[0].resolve())+':.'])
        command.append('run_guitar_lab.py')
        subprocess.run(command,cwd=ROOT,check=True)
    folder=ROOT/'dist/GuitarLab'
    manual.render(folder/'Manual-GuitarLab.html')
    notices=[]
    licenses=folder/'licenses';licenses.mkdir(exist_ok=True)
    for dist in importlib.metadata.distributions():
        name=dist.metadata.get('Name','package');version=dist.version
        notices.append(name+' '+version+' — '+dist.metadata.get('Home-page',dist.metadata.get('License-Expression','')))
        for file in dist.files or []:
            parts=file.parts
            if any(p.endswith('.dist-info') for p in parts) and ('license' in str(file).lower() or 'copying' in file.name.lower()):
                source=Path(dist.locate_file(file))
                if source.is_file():
                    target=licenses/name/file.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (folder/'THIRD-PARTY-NOTICES.txt').write_text('\n'.join(sorted(notices)),encoding='utf8')
    (folder/'LEIA-ME.txt').write_text('Guitar Lab '+__version__+' beta\n\nExtraia a pasta inteira. Mantenha _internal ao lado do executável.\nAbra Manual-GuitarLab.html para o passo a passo.\nLinux: conexão real e verde validados no Zorin.\nWindows: teclado em primeiro plano; hardware pendente, sem whammy analógico.\nO programa não instala Clone Hero nem inclui músicas.\n',encoding='utf8')
    platform='Windows' if sys.platform=='win32' else 'Linux'
    assets=ROOT/'build/release-assets';assets.mkdir(parents=True,exist_ok=True)
    filename=f'GuitarLab-{__version__}-{platform}-x64'
    if platform=='Windows':
        archive=assets/(filename+'.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in sorted(folder.rglob('*')):
                if path.is_file():z.write(path,Path('GuitarLab')/path.relative_to(folder))
    else:
        script=folder/'instalar-menu.sh'
        script.write_text('''#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.local/share/applications"
python3 - "$task_root" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]);target=Path.home()/'.local/share/applications/guitar-lab.desktop'
exe=str(root/'GuitarLab').replace('\\\\','\\\\\\\\').replace('"','\\\\"').replace('`','\\\\`').replace('$','\\\\$')
target.write_text('[Desktop Entry]\\nType=Application\\nName=Guitar Lab\\nExec="'+exe+'"\\nIcon=input-gaming\\nTerminal=false\\nCategories=Game;Utility;\\n')
print('Atalho Guitar Lab criado no menu de aplicativos.')
PY
''')
        script.chmod(0o755)
        archive=assets/(filename+'.tar.gz')
        with tarfile.open(archive,'w:gz') as t:t.add(folder,arcname='GuitarLab')
    shutil.copy2(folder/'Manual-GuitarLab.html',assets/'Manual-GuitarLab.html')
    print('Pacote pronto:',archive)

if __name__=='__main__':main()
