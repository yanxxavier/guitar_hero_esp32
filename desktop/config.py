import copy
import json
import os
import sys
from pathlib import Path

ACTIONS = ('green', 'red', 'yellow', 'blue', 'orange', 'up', 'down', 'start', 'select')
LABELS = ('Verde', 'Vermelho', 'Amarelo', 'Azul', 'Laranja', 'Palheta ↑', 'Palheta ↓', 'Start', 'Select / Star Power')
TILT_LABEL = 'Inclinação (Tilt)'
ALL_LABELS = LABELS + (TILT_LABEL,)
BITS = (1, 4, 8, 16, 32, 2, 256, 64, 128)
DEFAULT_PINS = (21, 18, 16, 17, 15, 14, 27, 13, 26)
DEFAULT_TILT_PIN = 15
GPIO = (4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)

def data_dir():
    if sys.platform == 'win32':
        return Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming')) / 'GuitarLab'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/GuitarLab'
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'guitar-lab'

def defaults():
    if sys.platform == 'win32':
        # Qt's Documents location (including OneDrive redirection) is used by the GUI.
        game_data = Path.home() / 'Documents/Clone Hero'
    else:
        game_data = (Path.home() / 'Clone Hero' if sys.platform == 'darwin'
                     else Path.home() / '.clonehero')
    return dict(pins=list(DEFAULT_PINS), tilt_pin=DEFAULT_TILT_PIN, port='', whammy=False, whammy_sfx=False,
                game='', game_data=str(game_data), songs=str(game_data / 'Songs'), auto_connect=True)

def validate_pins(pins):
    if len(pins) != 9 or any(type(p) is not int or p not in GPIO for p in pins):
        raise ValueError('Escolha nove GPIOs de entrada disponíveis na lista.')
    if len(set(pins)) != 9:
        raise ValueError('Cada função precisa de um GPIO diferente.')
    return list(pins)

def validate_tilt_pin(pin):
    if type(pin) is not int or pin not in GPIO:
        raise ValueError('Escolha um GPIO de entrada disponível para a inclinação (Tilt).')
    return pin

def load(path=None):
    profile = defaults()
    try:
        stored = json.loads((path or data_dir() / 'profile.json').read_text())
        validate_pins(stored.get('pins', profile['pins']))
        if 'tilt_pin' in stored:
            validate_tilt_pin(stored['tilt_pin'])
        profile.update({k: v for k, v in stored.items() if k in profile})
    except (OSError, ValueError, TypeError):
        pass
    return profile

def save(profile, path=None):
    validate_pins(profile['pins'])
    if 'tilt_pin' in profile:
        validate_tilt_pin(profile['tilt_pin'])
    path = path or data_dir() / 'profile.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding='utf8')
    temp.replace(path)

def translated_mask(mask, reported_pins, assigned_pins):
    down = {pin for pin, bit in zip(reported_pins, BITS) if mask & bit}
    return sum(bit for pin, bit in zip(assigned_pins, BITS) if pin in down)

def swap_pin(pins, index, pin):
    pins = list(pins)
    if pin in pins:
        other = pins.index(pin)
        pins[other] = pins[index]
    pins[index] = pin
    return validate_pins(pins)

def swap_with_tilt(pins, tilt_pin, index, pin):
    pins = list(pins)
    tilt_pin = validate_tilt_pin(tilt_pin)
    if index == 9:
        validate_tilt_pin(pin)
        if pin in pins and tilt_pin not in pins:
            pins[pins.index(pin)] = tilt_pin
        return validate_pins(pins), pin
    old_pin = pins[index]
    new_pins = swap_pin(pins, index, pin)
    if pin == tilt_pin and old_pin not in new_pins:
        tilt_pin = old_pin
    return new_pins, tilt_pin
