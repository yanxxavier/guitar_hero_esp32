import configparser
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .config import data_dir
from .runtime import external

def running():
    if sys.platform == 'win32':
        # Only process names, never command lines or unrelated window contents.
        result = external(['tasklist', '/FI', 'IMAGENAME eq clonehero.exe', '/FO', 'CSV', '/NH'],
                                capture_output=True, text=True, creationflags=0x08000000)
        return 'clonehero.exe' in result.stdout.lower()
    if sys.platform == 'darwin':
        result = external(['/usr/bin/pgrep', '-x', 'Clone Hero'], capture_output=True, text=True)
        return result.returncode == 0
    for p in Path('/proc').glob('[0-9]*/comm'):
        try:
            if p.read_text().strip().lower() == 'clonehero':
                return True
        except OSError:
            pass
    return False

def prepare(profile):
    if running():
        raise ValueError('Feche o Clone Hero antes de aplicar a configuração. Abra o jogo novamente depois.')
    folder = Path(profile['game_data']).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'settings.ini'
    original = path.read_text(encoding='utf-8-sig') if path.exists() else ''
    config = configparser.ConfigParser(interpolation=None, strict=False)
    config.read_string(original)
    if not config.has_section('audio'):
        config.add_section('audio')
    value = str(int(bool(profile['whammy_sfx'])))
    if path.exists():
        backups = data_dir() / 'backups'
        backups.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backups / ('settings-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.ini'))
    # Preserve every other setting and comments verbatim.
    lines = original.splitlines(keepends=True)
    section = None
    found = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            section = stripped[1:-1]
        if section == 'audio' and stripped.split('=', 1)[0].strip() == 'whammy_sfx':
            lines[i] = f'whammy_sfx = {value}\n'
            found = True
    if not found:
        if '[audio]' in original:
            text = ''.join(lines).replace('[audio]', f'[audio]\nwhammy_sfx = {value}', 1)
        else:
            text = ''.join(lines) + f'\n[audio]\nwhammy_sfx = {value}\n'
    else:
        text = ''.join(lines)
    temp = path.with_suffix('.guitar-lab.tmp')
    temp.write_text(text, encoding='utf8')
    temp.replace(path)
    Path(profile['songs']).expanduser().mkdir(parents=True, exist_ok=True)
    return 'Configuração aplicada. Whammy SFX ' + ('ativado.' if value == '1' else 'desativado.')

def discover_game():
    if sys.platform == 'win32':
        roots = [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Clone Hero',
                 Path('C:/Program Files/Clone Hero')]
        for root in roots:
            if root.is_dir():
                for p in root.rglob('clonehero.exe'):
                    return str(p)
    elif sys.platform == 'darwin':
        manifest = Path.home() / 'Library/Application Support/net.clonehero.launcher/game_installs.json'
        try:
            installs = json.loads(manifest.read_text())
            entries = sorted(installs.get('installs', []), key=lambda entry: entry.get('id') != installs.get('defaultInstallId'))
            for entry in entries:
                candidate = Path(entry.get('executablePath', ''))
                if not entry.get('disabled') and candidate.is_file() and os.access(candidate, os.X_OK):
                    return str(candidate)
        except (OSError, ValueError, TypeError):
            pass
        roots = [Path('/Applications'), Path.home() / 'Applications',
                 Path.home() / 'Library/Application Support/Steam/steamapps/common']
        for root in roots:
            if root.is_dir():
                for p in root.rglob('Clone Hero.app/Contents/MacOS/Clone Hero'):
                    if p.is_file() and os.access(p, os.X_OK):
                        return str(p)
    else:
        roots = [Path.home() / 'Applications/CloneHero', Path.home() / '.local/share/CloneHero']
        for root in roots:
            if root.is_dir():
                candidates = sorted(root.rglob('clonehero'), reverse=True)
                for p in candidates:
                    if p.is_file() and os.access(p, os.X_OK):
                        return str(p)
    return ''

def launch(profile):
    path = Path(profile['game']).expanduser()
    if not path.is_file():
        raise ValueError('Escolha o executável do Clone Hero na aba Configuração.')
    if running():
        return 'O Clone Hero já está aberto.'
    # No shell, command substitution or user-provided arguments.
    external([str(path)], spawn=True, cwd=path.parent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 'Clone Hero aberto. Mantenha Guitar Lab conectado durante a partida.'
