"""One serial/virtual-output owner across the desktop and legacy dashboard."""
import os
import sys
from .config import data_dir

class Ownership:
    def __init__(self):
        self.file = None

    def acquire(self):
        root = data_dir()
        root.mkdir(parents=True, exist_ok=True)
        self.file = (root / 'device.lock').open('a+b')
        try:
            if sys.platform == 'win32':
                import msvcrt
                self.file.seek(0)
                if not self.file.read(1):
                    self.file.write(b'0'); self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.close()
            raise RuntimeError('A guitarra está aberta em outra instância. Feche o dashboard ou outro Guitar Lab.')
        return self

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
