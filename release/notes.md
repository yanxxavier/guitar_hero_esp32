# Guitar Lab 0.1.0 beta 3

Adiciona o mapeamento e diagnóstico do **10º controle `Inclinação (Tilt)`** (`D15` por padrão) no Guitar Lab e no firmware `CONFIG v11`, corrige a abertura de porta serial exclusiva no Windows (`exclusive=True`) e sincroniza automaticamente a pinagem salva na NVS do ESP32 (`PINS 16,21,27,17,18,12,13,4,19` e `TILT 15`).

## Downloads

- **Windows x64:** baixe o ZIP, extraia tudo e abra `GuitarLab.exe`.
- **Linux x64:** baixe o TAR.GZ, extraia e abra `GuitarLab`.
- **Manual-GuitarLab.html:** manual completo offline, com imagens e passo a passo. Também incluído nos pacotes e acessível no app pelo menu Ajuda/F1.
- **SHA256SUMS.txt:** hashes dos downloads.

Mantenha a pasta `_internal` junto do executável. Os pacotes incluem o runtime e não exigem instalação de Python.

## Novidades da beta 3

- **Mapeamento do Sensor Tilt Interno (`Inclinação (Tilt)`):** 10º controle selecionável na guitarra visual e na tabela lateral, com leitura `TILT <pino>` / `TILT_STATE 0|1`, remapeamento por `CFG TILT <pino>` e troca automática de terminais sem colisão.
- **Saída separada Select × Tilt no Clone Hero:**
  - **Linux:** `Select` envia `BTN_SELECT` e `Inclinação (Tilt)` envia o eixo analógico `ABS_Y` (`Tilt Axis`).
  - **Windows / macOS:** `Select` envia `H` e `Inclinação (Tilt)` envia `T` (com Clone Hero em primeiro plano).
- **Windows Serial (`pyserial`):** corrigido `exclusive=True` para conexão imediata na porta `COM` do CH340 no Windows.
