"""Keep bundled Qt libraries out of programs launched outside the bundle."""
import os
import subprocess
import sys
import threading

_launch_lock = threading.Lock()

def external_env():
    env = os.environ.copy()
    if getattr(sys, 'frozen', False):
        for key in ('LD_LIBRARY_PATH', 'LIBPATH'):
            if key + '_ORIG' in env:
                env[key] = env[key + '_ORIG']
            else:
                env.pop(key, None)
    return env

def external(args, *, spawn=False, **kwargs):
    kwargs.setdefault('env', external_env())
    with _launch_lock:
        restore = None
        if getattr(sys, 'frozen', False) and sys.platform == 'win32':
            import ctypes
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.GetDllDirectoryW.argtypes = (ctypes.c_uint, ctypes.c_wchar_p)
            kernel.SetDllDirectoryW.argtypes = (ctypes.c_wchar_p,)
            buf = ctypes.create_unicode_buffer(32768)
            kernel.GetDllDirectoryW(len(buf), buf)
            restore = (kernel, buf.value)
            kernel.SetDllDirectoryW(None)
        try:
            return (subprocess.Popen if spawn else subprocess.run)(args, **kwargs)
        finally:
            if restore:
                restore[0].SetDllDirectoryW(restore[1] or None)
