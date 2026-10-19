# Identificar fios do braço fechado

18/10/2026: usuário fechou braço e perdeu identificação dos cinco fios de sinal. Ligou-os em **D17, D16, D18, D21 e D15**, ordem de cores desconhecida. Terra comum deve permanecer identificado e ligado a GND. Não presumir mapa v7 nem mapa antigo D13.

Firmware temporário `firmware/identificar_fios`: cinco INPUT_PULLUP com debounce 5 ms; identificação `GUITARHERO PINSCAN v1 GPIO17 GPIO16 GPIO18 GPIO21 GPIO15`. Quadros `SCAN N`, N 0–31, bits na ordem 17/16/18/21/15, heartbeat 250 ms. Não lê whammy/menus/palhetada e não gera protocolo de jogo. Botões soltos no reinício, especialmente D15.

Dashboard reconhece identificação PINSCAN, libera ponte, apaga estados antigos de cores e mostra pinos sem atribuir cores. SCAN não é enviado ao controle virtual; STATE/BUTTON também são ignorados enquanto modo diagnóstico ativo. Indicação dos pinos expira após 1,5 s sem SCAN ou desconexão. Transições reais ficam em logs/dashboard/events.jsonl, nunca publicar logs.

Procedimento: apertar e soltar SOMENTE verde, observar qual pino muda e anotar. Repetir vermelho, amarelo, azul, laranja, um por vez. Se vários pinos mudarem, investigar ligação/curto antes de atribuir cor. Depois atualizar firmware de jogo e metadados/UI com o mapa confirmado, restaurar entradas extras em GPIOs separados e testar todos. Não usar firmware v7 com o chicote novo sem remapear.

Compilar/upload com --fqbn esp32:esp32:esp32, --output-dir build/identificar_fios e --input-dir build/identificar_fios; servidor deve liberar serial antes de upload. Não executar web server como root. Firmware de jogo anterior preservado no repositório.

24 testes de lógica cobrem também isolamento entre modo diagnóstico/jogo, quadro inválido e desconexão. Identificação de cores requer apertos reais e confirmação da cor pelo usuário.
