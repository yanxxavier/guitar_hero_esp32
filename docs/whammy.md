# Whammy D34 — firmware v5

## Ligação
Potenciômetro **B10K**, três terminais: extremos em **3V3** e GND comum; cursor no **D34/GPIO34**. Usuário confirmou ligação. Inverter extremos inverte sentido. Não alimentar em 5 V. Manter Green D15 e palhetada D13; deixar botões soltos ao reiniciar.

## Leitura e protocolo
Identificação `GUITARHERO WHAMMY v5 GPIO15 GPIO13 GPIO34`. Quadros ASCII `STATE N A`, 115200/8N1, newline. N: máscara 0–3 dos dois botões; A: ADC 12 bits, 0–4095. ADC com atenuação 11 dB; leitura a cada 5 ms, filtro IIR 3/4 anterior + 1/4 amostra, variação mínima de 12 unidades e intervalo de 20 ms para envio apenas analógico. Botões mantêm debounce independente 5 ms e envio imediato após estabilização. Heartbeat completo no máximo a cada 250 ms. Valores são posição bruta filtrada, não tensão calibrada; ADC pode saturar perto dos extremos.

Ponte apresenta **ABS_Z**, faixa 0–4095, sem calibração mecânica nem inversão automática. Outros eixos permanecem neutros. Mudanças do eixo preservam botões segurados, valores inválidos rejeitam quadro inteiro. Desconexão, silêncio >1,5 s e encerramento liberam botões e zeram eixo. Dispositivo mantém nome; capacidades mudaram ao adicionar eixo, então pode ser necessário reatribuir no jogo.

Dashboard mostra barra, percentual da escala 0–4095 e menor/maior observados nesta contagem. Nova contagem reinicia extremos observados; isso não calibra a saída. Não grava eventos analógicos continuamente no histórico para evitar excesso de logs. Firmware antigo segue aceito, mas indica ausência de leitura analógica.

## Teste
Atualizar painel e girar lentamente de uma ponta à outra. Conferir variação e limites. Depois conferir estabilidade com eixo parado. Testar botões segurados enquanto gira. Definir posição mecânica de repouso, sentido e curso antes de mapear **Whammy** no Clone Hero. Leitura Linux não comprova funcionamento no jogo. Testes completos/Ally continuam pendentes.

## Verificação desta implementação
20 testes unitários cobrem botões, quadros inválidos, extremos analógicos, duplicatas, preservação simultânea e retorno seguro. Firmware compilado e gravado com hash verificado no ESP32; firmware v5 identificado na serial, eixo ABS_Z criado no kernel. No início da verificação, posição lida foi zero; curso físico e jogo aguardam teste do usuário.

Fonte: [Espressif — ADC Arduino-ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/adc.html). Implementação compilada com core ESP32 2.0.17.
