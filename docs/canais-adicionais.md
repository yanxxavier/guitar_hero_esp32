# Quatro canais adicionais — firmware v10

Usuário quer identificar os switches de palhetadas/Start/Select pelo painel. Atualização em 18/10: usuário confirmou ligação dos quatro fios em D13/D14/D27/D26 e reconectou ESP32. Correspondência função→canal ainda desconhecida. Canais preparados em D13, D14, D27 e D26, cada switch NO entre pino e GND comum, INPUT_PULLUP. Conferir rótulos físicos. USB desligado para conectar. Não ligar switches a 3V3/5V.

Cinco frets mantidos: verde21/vermelho18/amarelo16/azul17/laranja15. Laranja solto na inicialização. Azul D17 exige força maior mesmo sem botão impresso, por relato; causa em investigação, não corrigida e não atribuída automaticamente à peça impressa.

Identificação: `GUITARHERO CHANNELS v10 FRETS21,18,16,17,15 AUX13,14,26,27 ADC34`. Protocolo ASCII `STATE N A`, máscara de **9 bits**, decimal0–511 (uint16_t no ESP32); A=ADC0–4095. Bits dos frets preservados1/4/8/16/32; D13=64, D14=2, D26=128, D27=256. Todos os nove ativos=511.

Firmware lê os quatro canais, mas a função física ainda NÃO foi atribuída. Dashboard mostra pino, estado e contagem independente; primeiro quadro não conta aperto, heartbeat não duplica, desconexão remove estado, nova contagem zera contadores. Quadros de firmware antigo não apresentam os quatro canais como lidos; máscara>63 só aceita após identificação CHANNELS v10.

Enquanto sem funções confirmadas, ponte envia somente `mask & 61` (cinco frets) e whammy. Nenhum dos quatro canais é enviado ao jogo, incluindo D14 cujo bit2 decimal foi usado pela palhetada antiga. Não apresentar palhetadas e menus funcionando no Clone Hero nesta etapa. Após usuário apertar cada switch conhecido e associar pino, configurar as funções e saída virtual em etapa posterior.

Teste: conectar quatro sinais nos quatro GPIOs, sem precisar adivinhar inicialmente a função; GND comum identificado. Atualizar painel; apertar SOMENTE um switch físico e relatar sua função, observar canal ativado. Repetir quatro vezes e registrar mapa. Antes de jogos, conferir sinais em repouso e solturas. Ligação nesses quatro GPIOs informada pelo usuário; funcionamento individual ainda depende de apertos após v10.

28 testes unitários aprovados; novos testes verificam canais simultâneos, isolamento do jogo, duplicatas, baseline, desconexão e limite512 inválido. Testes não substituem os apertos físicos. Modo PINSCAN de cinco fios preservado como ferramenta independente.

A versão v9 usava D25/D32/D26/D27, substituída por v10. O parser não atribui rótulos novos aos canais do v9; exige identificação CHANNELS v10 antes de habilitar os quatro canais no painel. Saídas para jogo continuam bloqueadas para canais extras até identificar as funções.

## Funções confirmadas pelo usuário e eventos reais — 18/10

| Função | GPIO | Bit do protocolo |
| --- | --- | --- |
| Palhetada para cima | D14 | 2 |
| Palhetada para baixo | D27 | 256 |
| Start | D13 | 64 |
| Select / Star Power | D26 | 128 |

Cima identificada em rodada de três pares D27. Baixo identificado por relato e vários pares D14. Start D13 e Select D26 confirmados pelo usuário e por eventos recentes. Rótulos e contadores no dashboard atualizados, sem nova gravação (CHANNELS v10 continua ativo).

A correspondência física foi concluída; isso substitui a pendência de identificar funções nos parágrafos históricos acima. A ponte ainda filtra os quatro extras (mask & 61); atualização solicitada nesta etapa foi somente o painel. Saída dos quatro comandos Linux e mapeamento no jogo seguem como próxima etapa. Azul D17 com falha não resolvida.

## Inversão solicitada em20/10/2026
Usuário pediu trocar funções de cima/baixo: **CIMA D14, BAIXO D27**. StartD13 e SelectD26 permanecem. Firmware CHANNELS v10 transmite canais brutos; sem nova gravação ou troca de bits. Dashboard/logs/ordem visual atualizados. Testes físicos anteriores referem-se à orientação antiga; conferir nova orientação no painel. Extras continuam sem saída para jogo.
