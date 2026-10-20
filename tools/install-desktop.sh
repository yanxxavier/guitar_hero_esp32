#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_root"
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-desktop.txt
.venv/bin/python - <<'PY'
from pathlib import Path
import subprocess
import shutil
from PySide6.QtCore import QLibraryInfo
plugin=Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))/'platforms/libqxcb.so'
if plugin.exists() and shutil.which('ldd'):
    result=subprocess.run(['ldd',str(plugin)],capture_output=True,text=True)
    if 'libxcb-cursor.so.0 => not found' in result.stdout:
        if not shutil.which('apt-get') or not shutil.which('dpkg-deb'):
            raise SystemExit('Instale libxcb-cursor0 pelo gerenciador de pacotes da sua distribuição e execute o instalador novamente.')
        folder=Path('.tools/qt-runtime').resolve();folder.mkdir(parents=True,exist_ok=True)
        subprocess.run(['apt-get','download','libxcb-cursor0'],cwd=folder,check=True)
        for archive in folder.glob('*.deb'):
            subprocess.run(['dpkg-deb','-x',str(archive),str(folder)],check=True)
PY
chmod +x tools/start-guitar-lab.sh
.venv/bin/python - <<'PY'
from pathlib import Path
root=Path.cwd()
target=Path.home()/'.local/share/applications/guitar-lab.desktop'
target.parent.mkdir(parents=True,exist_ok=True)
exec_path=str(root/'tools/start-guitar-lab.sh').replace('\\','\\\\').replace('"','\\"').replace('`','\\`').replace('$','\\$')
target.write_text('[Desktop Entry]\nType=Application\nName=Guitar Lab\nComment=Configurar e testar a guitarra ESP32\nExec="'+exec_path+'"\nIcon=input-gaming\nTerminal=false\nCategories=Game;Utility;\nStartupWMClass=Guitar Lab\n')
target.chmod(0o755)
print('Instalado. Procure Guitar Lab no menu de aplicativos.')
PY
