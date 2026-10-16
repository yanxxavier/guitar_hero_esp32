# Bancada com cinco cores — firmware v7

Montagem atual relatada em 16/10/2026: braço impresso, cinco switches verde → vermelho → amarelo → azul → laranja. **Palhetada, Start e Select não instalados nesta montagem.** Testes anteriores de palhetada pertencem à bancada anterior.

| Cor | GPIO | Bit serial | Saída Linux |
| --- | --- | --- | --- |
| Verde | D15 | 1 | BTN_SOUTH |
| Vermelho | D18 | 4 | BTN_NORTH |
| Amarelo | D19 | 8 | BTN_WEST |
| Azul | D21 | 16 | BTN_TL |
| Laranja | D13 | 32 | BTN_TR |

Cada switch NO liga GPIO a GND comum com INPUT_PULLUP; sinal independente por cor. Não alimentar switches com 3V3/5V. Manter Green solto no boot. D34/B10K preservado para whammy, extremos 3V3/GND. Não confirmado novamente se potenciômetro permaneceu fisicamente instalado nesta montagem.

Identificação `GUITARHERO FRETS v7 GPIO15 GPIO18 GPIO19 GPIO21 GPIO13 ADC34`. Protocolo `STATE N A`, N entre 0 e 63; todos os frets apertados = 61. Bit 1 (valor decimal 2) reservado à palhetada histórica, nunca gerado pelo firmware v7. Ponte mantém compatibilidade com v4/v5; saídas BTN_SOUTH/BTN_EAST e ABS_Z anteriores preservadas, novos frets usam quatro botões antes neutros. D13 é lido como laranja; palhetada e menus não são lidos. Sem bits novos para Start/Select até etapa posterior.

Dashboard exibe cinco indicadores e contagem independente. Primeiro estado após conexão é referência; heartbeat não repete apertos. Desconexão remove estados atuais e watchdog libera todos os botões e eixo após 1,5 s sem quadros. Suporte a combinações simultâneas, sem exclusão entre cores. Zerar contagem reinicia contadores individuais também.

22 testes unitários aprovados incluindo cinco frets, acordes/soltura parcial, quadros inválidos, duplicatas e liberação segura. Teste simulado não substitui conferir apertos reais e ausência de acionamento em repouso.

Teste físico: apertar/soltar cada cor de verde a laranja, depois segurar duas juntas. Verificar indicadores corretos, um aperto/soltura por acionamento e retorno a Solto. Mapear as cinco cores separadamente no Clone Hero somente após conferir painel. Palhetada, Start/Select e testes da guitarra completa continuam pendentes.

Correção do usuário durante a preparação: não há D22 disponível na placa; laranja ligado em **D13**. D13 foi reaproveitado da palhetada anterior, atualmente ausente. v6 foi substituído por v7 antes do teste físico.
