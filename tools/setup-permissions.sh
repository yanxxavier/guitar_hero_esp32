#!/usr/bin/env bash
# Execute: sudo bash tools/setup-permissions.sh
# Concede uinput à sessão gráfica ativa e acesso somente ao controle deste projeto.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Execute com sudo para instalar as regras udev.' >&2
  exit 1
fi
modprobe uinput
cat > /etc/udev/rules.d/70-guitar-lab.rules <<'RULES'
SUBSYSTEM=="misc", KERNEL=="uinput", TAG+="uaccess", OPTIONS+="static_node=uinput"
SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="Guitar Lab Virtual Controller", ENV{ID_INPUT_JOYSTICK}="1", TAG+="uaccess"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", TAG+="uaccess"
RULES
udevadm control --reload-rules
udevadm trigger --action=change --subsystem-match=misc --sysname-match=uinput
udevadm trigger --action=change --subsystem-match=input
udevadm trigger --action=change --subsystem-match=tty --sysname-match='ttyUSB*'
udevadm settle
echo 'Regras instaladas. A sessão gráfica ativa deve ter acesso ao uinput.'
echo 'Guitar Lab tentará conectar a serial e criar o controle automaticamente.'
