"""Send keyboard events only while Clone Hero is the frontmost macOS app."""
import ctypes
import subprocess
import threading
import time

from .config import BITS

# A/S/J/K/L, Up, Down, Return, H using macOS virtual key codes.
KEYS = (0, 1, 38, 40, 37, 126, 125, 36, 4)
FOREGROUND_SCRIPT = (
    'tell application "System Events" to get name of '
    'first application process whose frontmost is true'
)


class MacOSOutput:
    def __init__(self):
        self.mask = 0
        self.desired = 0
        self.sent = 0
        self.error = None
        self.frontmost = False
        self._lock = threading.Lock()
        self._closed = threading.Event()
        self._focus_thread = threading.Thread(target=self._watch_frontmost, daemon=True)
        try:
            self._cg = ctypes.CDLL(
                "/System/Library/Frameworks/ApplicationServices.framework/"
                "Frameworks/CoreGraphics.framework/CoreGraphics"
            )
            self._cf = ctypes.CDLL(
                "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
            )
            self._cg.CGEventCreateKeyboardEvent.argtypes = (
                ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool
            )
            self._cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
            self._cg.CGEventPost.argtypes = (ctypes.c_uint32, ctypes.c_void_p)
            self._cg.CGEventPost.restype = None
            self._cf.CFRelease.argtypes = (ctypes.c_void_p,)
            self._cf.CFRelease.restype = None
        except OSError as exc:
            self.error = f"Não foi possível iniciar eventos de teclado do macOS: {exc}"
            self._cg = self._cf = None
        self._focus_thread.start()

    def _watch_frontmost(self):
        while not self._closed.is_set():
            try:
                result = subprocess.run(
                    ["/usr/bin/osascript", "-e", FOREGROUND_SCRIPT],
                    capture_output=True, text=True, timeout=1,
                )
                if result.returncode:
                    with self._lock:
                        self.frontmost = False
                        self.error = (
                            "Permita que o Terminal/Python controle o System Events em "
                            "Ajustes do Sistema → Privacidade e Segurança → Automação."
                        )
                else:
                    name = result.stdout.strip().casefold().replace(" ", "")
                    with self._lock:
                        self.frontmost = "clonehero" in name
                        self.error = None
            except (OSError, subprocess.SubprocessError) as exc:
                with self._lock:
                    self.frontmost = False
                    self.error = f"Não consegui detectar o aplicativo em primeiro plano: {exc}"
            self._closed.wait(.25)

    def _send(self, mask):
        if not self._cg:
            return
        for bit, key in zip(BITS, KEYS):
            if bool(self.mask & bit) == bool(mask & bit):
                continue
            event = self._cg.CGEventCreateKeyboardEvent(None, key, bool(mask & bit))
            if not event:
                self.error = "O macOS não criou um evento de teclado."
                continue
            self._cg.CGEventPost(0, event)  # kCGHIDEventTap
            self._cf.CFRelease(event)
            self.mask = self.mask | bit if mask & bit else self.mask & ~bit
            self.sent += 1

    def frame(self, mask, whammy=0):
        self.desired = mask
        self.tick()

    def tick(self):
        with self._lock:
            allowed = self.frontmost
        self._send(self.desired if allowed else 0)

    def release(self):
        self.desired = 0
        self._send(0)

    def snapshot(self):
        return dict(
            ready=self._cg is not None, mask=self.mask, whammy=0,
            error=self.error, sent=self.sent,
            mode="Teclado · somente Clone Hero em primeiro plano",
            event_path=None,
        )

    def shutdown(self):
        self.release()
        self._closed.set()

    def close(self):
        self.shutdown()
