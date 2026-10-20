"""Public Encore catalog + the chart source's public Drive downloads.

Downloads are opt-in, staged, validated, then installed without overwriting songs.
No execution, cookies/accounts, quota workarounds, or copies into the repository.
"""
import hashlib
import importlib
import json
import re
import shutil
import struct
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
import gdown
import requests
from .config import data_dir

ALLOWED = {'.ini', '.chart', '.mid', '.ogg', '.opus', '.mp3', '.wav', '.png', '.jpg', '.jpeg', '.webp', '.txt'}
MAX_BYTES = 1024 * 1024 * 1024

def search(query, difficulty='easy', page=1):
    if not query.strip():
        raise ValueError('Digite o nome de uma música ou banda.')
    payload = dict(search=query.strip(), per_page=25, page=page, instrument='guitar',
                   difficulty=difficulty or None, drumType=None, drumsReviewed=False, sort=None, source='bridge')
    request = urllib.request.Request('https://api.enchor.us/search', data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    return data.get('data', [])

def normal(s):
    return re.sub(r'[^a-z0-9]', '', re.sub('<[^>]+>', '', s).lower())

def safe_title(chart):
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', chart['artist'] + ' - ' + chart['name']).strip(' .')
    return (title[:150] or 'Música') + ' [' + str(int(chart['chartId'])) + ']'

def validate_sng(path, chart):
    size = path.stat().st_size
    if not 1000 < size <= MAX_BYTES:
        raise ValueError('Tamanho inválido para o arquivo da música.')
    with path.open('rb') as f:
        if f.read(6) != b'SNGPKG' or struct.unpack('<I', f.read(4))[0] != 1:
            raise ValueError('O download não contém um arquivo SNG compatível.')
        f.read(16)
        length, count = struct.unpack('<QQ', f.read(16))
        if not 8 <= length < 1000000 or count > 10000:
            raise ValueError('Metadados SNG inválidos.')
        meta = {}
        for _ in range(count):
            n = struct.unpack('<i', f.read(4))[0]
            if not 0 <= n < 100000: raise ValueError('Metadados SNG inválidos.')
            key = f.read(n).decode('utf8')
            n = struct.unpack('<i', f.read(4))[0]
            if not 0 <= n < 100000: raise ValueError('Metadados SNG inválidos.')
            meta[key] = f.read(n).decode('utf8')
        if f.tell() != 34 + length:
            raise ValueError('Comprimento dos metadados SNG incorreto.')
        _, count = struct.unpack('<QQ', f.read(16))
        if count > 10000: raise ValueError('Índice SNG inválido.')
        names = []
        for _ in range(count):
            name = f.read(f.read(1)[0]).decode('utf8')
            length, offset = struct.unpack('<QQ', f.read(16))
            if offset + length > size: raise ValueError('Download SNG incompleto.')
            names.append(name)
        if not any(n in names for n in ('notes.mid', 'notes.chart')) or not any(Path(n).suffix in ('.ogg', '.opus', '.mp3', '.wav') for n in names):
            raise ValueError('A música precisa de chart e áudio.')
        if normal(meta.get('name', '')) != normal(chart['name']) or normal(meta.get('artist', '')) != normal(chart['artist']):
            raise ValueError('O arquivo da fonte não corresponde à música selecionada.')
    return meta

def safe_extract(archive, target):
    with zipfile.ZipFile(archive) as z:
        if sum(i.file_size for i in z.infolist()) > MAX_BYTES:
            raise ValueError('O ZIP descompactado excede 1 GB.')
        for info in z.infolist():
            name = PurePosixPath(info.filename.replace('\\', '/'))
            if name.is_absolute() or '..' in name.parts or (name.parts and ':' in name.parts[0]):
                raise ValueError('Caminho inseguro no ZIP.')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Links simbólicos não são aceitos em músicas.')
            if info.is_dir() or name.suffix.lower() not in ALLOWED:
                continue
            dest = target.joinpath(*name.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, dest.open('wb') as dst:
                shutil.copyfileobj(src, dst)

def folder_valid(path, chart):
    import configparser
    cfg = configparser.ConfigParser(interpolation=None, strict=False)
    cfg.read(path / 'song.ini', encoding='utf-8-sig')
    if not cfg.has_section('song'):
        raise ValueError('A pasta não contém song.ini válido.')
    if normal(cfg.get('song', 'name', fallback='')) != normal(chart['name']) or normal(cfg.get('song', 'artist', fallback='')) != normal(chart['artist']):
        raise ValueError('A pasta da fonte não corresponde à música selecionada.')
    if not any((path / n).exists() for n in ('notes.mid', 'notes.chart')) or not any(p.suffix in ('.ogg', '.opus', '.mp3', '.wav') for p in path.iterdir()):
        raise ValueError('A pasta precisa de chart e áudio.')

def _drive_file(file_id, path):
    if not re.fullmatch(r'[-\w]{20,}', file_id or ''):
        raise ValueError('A fonte não informou um arquivo público válido.')
    gdown.download(id=file_id, output=str(path), quiet=True, use_cookies=False, timeout=(20, 90))
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('O arquivo excede 1 GB.')

def install(chart, destination):
    root = Path(destination).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    title = safe_title(chart)
    drive_name = chart.get('driveFileName') or ''
    is_sng = drive_name.lower().endswith('.sng')
    final = root / (title + '.sng' if is_sng else title)
    if final.exists():
        if is_sng: validate_sng(final, chart)
        else: folder_valid(final, chart)
        return 'Já instalada: ' + chart['name']
    if chart.get('driveFileId') and not drive_name.lower().endswith(('.sng', '.zip')):
        raise ValueError('Essa fonte usa um pacote não suportado (' + Path(drive_name).suffix + '). Escolha outro chart ou abra a fonte pública.')
    with tempfile.TemporaryDirectory(prefix='.guitar-lab-', dir=root) as temp:
        stage = Path(temp)
        if chart.get('driveFileId'):
            archive = stage / ('chart.sng' if is_sng else 'chart.zip')
            _drive_file(chart['driveFileId'], archive)
            if is_sng:
                validate_sng(archive, chart)
                archive.rename(final)
            else:
                unpack = stage / 'unpacked'
                safe_extract(archive, unpack)
                candidates = list(unpack.rglob('song.ini'))
                selected = None
                for ini in candidates:
                    try:
                        folder_valid(ini.parent, chart)
                        selected = ini.parent
                        break
                    except ValueError:
                        pass
                if not selected: raise ValueError('Não encontrei a música selecionada dentro do pacote.')
                selected.rename(final)
        else:
            folder_id = chart.get('applicationDriveId')
            if not folder_id: raise ValueError('A fonte pública desta música está indisponível.')
            # Pinning gdown keeps this discovery adapter predictable; no recursive pack downloads.
            parse = importlib.import_module('gdown.download_folder')._parse_embedded_folder_view
            session = requests.Session()
            for segment in (chart.get('drivePath') or '').split('/'):
                if not segment: continue
                _, children = parse(sess=session, folder_id=folder_id, verify=True, timeout=30)
                matches = [c for c in children if c[1] == segment and c[2] == 'application/vnd.google-apps.folder']
                if len(matches) != 1: raise ValueError('A pasta da música mudou na fonte. Escolha outro chart.')
                folder_id = matches[0][0]
            _, files = parse(sess=session, folder_id=folder_id, verify=True, timeout=30)
            if len(files) > 100: raise ValueError('A fonte aponta para um pacote grande. Escolha um chart individual.')
            song = stage / 'song'
            song.mkdir()
            for file_id, name, kind in files:
                if Path(name).name != name or name in ('.', '..'):
                    raise ValueError('Nome de arquivo inválido na fonte.')
                if Path(name).suffix.lower() in ALLOWED:
                    _drive_file(file_id, song / name)
            folder_valid(song, chart)
            song.rename(final)
    records = data_dir() / 'downloads'
    records.mkdir(parents=True, exist_ok=True)
    (records / (str(int(chart['chartId'])) + '.json')).write_text(json.dumps(dict(
        artist=chart['artist'], name=chart['name'], chartId=chart['chartId'], path=str(final),
        source='https://drive.google.com/open?id=' + chart['applicationDriveId']), ensure_ascii=False, indent=2))
    return 'Instalada: ' + chart['name']
