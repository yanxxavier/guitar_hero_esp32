# Bancada com cinco cores — firmware v8

Montagem anterior relatada em 16/10/2026: braço impresso, cinco switches verde → vermelho → amarelo → azul → laranja. **Palhetada, Start e Select não instalados nesta montagem.** Testes anteriores de palhetada pertencem à bancada anterior.

| Cor | GPIO | Bit serial | Saída Linux |
| --- | --- | --- | --- |
| Verde | D21 | 1 | BTN_SOUTH |
| Vermelho | D18 | 4 | BTN_NORTH |
| Amarelo | D16 | 8 | BTN_WEST |
| Azul | D17 | 16 | BTN_TL |
| Laranja | D15 | 32 | BTN_TR |

Cada switch NO liga GPIO a GND comum com INPUT_PULLUP; sinal independente por cor. Não alimentar switches com 3V3/5V. Manter Laranja solto no boot. D34/B10K preservado para whammy, extremos 3V3/GND. Não confirmado novamente se potenciômetro permaneceu fisicamente instalado nesta montagem.

Identificação `GUITARHERO FRETS v8 GPIO21 GPIO18 GPIO16 GPIO17 GPIO15 ADC34`. Protocolo `STATE N A`, N entre 0 e 63; todos os frets apertados = 61. Bit 1 (valor decimal 2) reservado à palhetada histórica, nunca gerado pelo firmware v8. Ponte mantém compatibilidade com v4/v5; saídas BTN_SOUTH/BTN_EAST e ABS_Z anteriores preservadas, novos frets usam quatro botões antes neutros. D13 não é lido neste mapa; palhetada e menus não são lidos. Sem bits novos para Start/Select até etapa posterior.

Dashboard exibe cinco indicadores e contagem independente. Primeiro estado após conexão é referência; heartbeat não repete apertos. Desconexão remove estados atuais e watchdog libera todos os botões e eixo após 1,5 s sem quadros. Suporte a combinações simultâneas, sem exclusão entre cores. Zerar contagem reinicia contadores individuais também.

22 testes unitários aprovados incluindo cinco frets, acordes/soltura parcial, quadros inválidos, duplicatas e liberação segura. Teste simulado não substitui conferir apertos reais e ausência de acionamento em repouso.

Teste físico: apertar/soltar cada cor de verde a laranja, depois segurar duas juntas. Verificar indicadores corretos, um aperto/soltura por acionamento e retorno a Solto. Mapear as cinco cores separadamente no Clone Hero somente após conferir painel. Palhetada, Start/Select e testes da guitarra completa continuam pendentes.

Correção do usuário durante a preparação: não há D22 disponível na placa; laranja ligado em **D13**. D13 foi reaproveitado da palhetada anterior, atualmente ausente. v6 foi substituído por v7 antes do teste físico.

## Remapeamento confirmado em 18/10
Após fechar braço, fios religados em17/16/18/21/15 e identificados por PINSCAN: verde21, vermelho18, amarelo16, azul17, laranja15. Azul exige força extra segundo usuário; causa mecânica/elétrica ainda não confirmada, não marcar azul corrigido. Comparar botão impresso e switch direto com USB desconectado para intervenção; testar continuidade isolado da placa se necessário. Mapa anterior D13 foi substituído. Laranja usa GPIO15 strapping: deixar solto no boot. Quatro switches adicionais disponíveis/instalados por relato; ligações D25/D32/D26/D27 ainda não confirmadas.
