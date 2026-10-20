"""Windows keyboard fallback, restricted to the foreground Clone Hero process.

No global hooks, drivers, administrator privileges or input to other programs.
Hardware validation on Windows is still required.
"""
import ctypes
from ctypes import wintypes as w
import os
from .config import BITS

KEYS = (0x41, 0x53, 0x4A, 0x4B, 0x4C, 0x26, 0x28, 0x0D, 0x48)

class WindowsOutput:
    def __init__(self):
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        ptr = ctypes.c_size_t
        class KEYBOARD(ctypes.Structure):
            _fields_ = [('vk', w.WORD), ('scan', w.WORD), ('flags', w.DWORD), ('time', w.DWORD), ('extra', ptr)]
        class MOUSE(ctypes.Structure):
            _fields_ = [('dx', w.LONG), ('dy', w.LONG), ('data', w.DWORD), ('flags', w.DWORD), ('time', w.DWORD), ('extra', ptr)]
        class HARDWARE(ctypes.Structure):
            _fields_ = [('msg', w.DWORD), ('low', w.WORD), ('high', w.WORD)]
        class UNION(ctypes.Union):
            _fields_ = [('ki', KEYBOARD), ('mi', MOUSE), ('hi', HARDWARE)]
        class INPUT(ctypes.Structure):
            _anonymous_ = ('value',)
            _fields_ = [('type', w.DWORD), ('value', UNION)]
        self.INPUT, self.KEYBOARD = INPUT, KEYBOARD
        self.user.SendInput.argtypes = (w.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        self.user.SendInput.restype = w.UINT
        self.user.GetForegroundWindow.restype = w.HWND
        self.user.GetWindowThreadProcessId.argtypes = (w.HWND, ctypes.POINTER(w.DWORD))
        self.kernel.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = (w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD))
        self.kernel.CloseHandle.argtypes = (w.HANDLE,)
        self.mask = 0
        self.desired = 0
        self.error = None
        self.sent = 0

    def focused(self):
        pid = w.DWORD()
        self.user.GetWindowThreadProcessId(self.user.GetForegroundWindow(), ctypes.byref(pid))
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return False
        try:
            size = w.DWORD(32768)
            name = ctypes.create_unicode_buffer(size.value)
            return bool(self.kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)) and
                        os.path.basename(name.value).lower() == 'clonehero.exe')
        finally:
            self.kernel.CloseHandle(handle)

    def _send(self, mask):
        for bit, key in zip(BITS, KEYS):
            if bool(self.mask & bit) == bool(mask & bit):
                continue
            scan = self.user.MapVirtualKeyW(key, 0)
            flags = 0x0008 | (0x0001 if key in (0x26, 0x28) else 0) | (0 if mask & bit else 0x0002)
            event = self.INPUT(type=1)
            event.ki = self.KEYBOARD(0, scan, flags, 0, 0)
            if self.user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
                self.error = 'Windows recusou uma tecla. Execute jogo e aplicativo sem administrador.'
                # Retain the previous bit so releases are retried rather than forgotten.
                continue
            self.mask = (self.mask | bit) if mask & bit else (self.mask & ~bit)
            self.sent += 1

    def frame(self, mask, whammy=0):
        self.desired = mask
        self.tick()

    def tick(self):
        self._send(self.desired if self.focused() else 0)

    def release(self):
        self.desired = 0
        self._send(0)

    close = release

    def snapshot(self):
        return dict(ready=True, mask=self.mask, whammy=0, error=self.error, sent=self.sent,
                    mode='Teclado · somente Clone Hero em primeiro plano', event_path=None)
