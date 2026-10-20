import os
import sys

# Windows GUI bundles do not supply console streams. Libraries such as esptool
# still expect file-like streams even when their output is shown in our GUI.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf8')

from desktop.app import main

if __name__ == '__main__':
    raise SystemExit(main())
