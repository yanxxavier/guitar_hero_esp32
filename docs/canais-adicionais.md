# Quatro canais adicionais — firmware v9

Usuário quer identificar os switches de palhetadas/Start/Select pelo painel. Em 18/10 confirmou que os quatro fios ainda NÃO estão conectados ao ESP32. Canais preparados em D25, D32, D26 e D27, cada switch NO entre pino e GND comum, INPUT_PULLUP. Conferir rótulos físicos. USB desligado para conectar. Não ligar switches a 3V3/5V.

Cinco frets mantidos: verde21/vermelho18/amarelo16/azul17/laranja15. Laranja solto na inicialização. Azul D17 exige força maior mesmo sem botão impresso, por relato; causa em investigação, não corrigida e não atribuída automaticamente à peça impressa.

Identificação: `GUITARHERO CHANNELS v9 FRETS21,18,16,17,15 AUX25,32,26,27 ADC34`. Protocolo ASCII `STATE N A`, máscara de **9 bits**, decimal0–511 (uint16_t no ESP32); A=ADC0–4095. Bits dos frets preservados1/4/8/16/32; D25=64, D32=2, D26=128, D27=256. Todos os nove ativos=511.

Firmware lê os quatro canais, mas a função física ainda NÃO foi atribuída. Dashboard mostra pino, estado e contagem independente; primeiro quadro não conta aperto, heartbeat não duplica, desconexão remove estado, nova contagem zera contadores. Quadros de firmware antigo não apresentam os quatro canais como lidos; máscara>63 só aceita após identificação CHANNELS v9.

Enquanto sem funções confirmadas, ponte envia somente `mask & 61` (cinco frets) e whammy. Nenhum dos quatro canais é enviado ao jogo, incluindo D32 cujo bit2 decimal foi usado pela palhetada antiga. Não apresentar palhetadas e menus funcionando no Clone Hero nesta etapa. Após usuário apertar cada switch conhecido e associar pino, configurar as funções e saída virtual em etapa posterior.

Teste: conectar quatro sinais nos quatro GPIOs, sem precisar adivinhar inicialmente a função; GND comum identificado. Atualizar painel; apertar SOMENTE um switch físico e relatar sua função, observar canal ativado. Repetir quatro vezes e registrar mapa. Antes de jogos, conferir sinais em repouso e solturas. Disponibilidade de D25/D32/D26/D27 ainda precisa ser conferida fisicamente pelo usuário.

27 testes unitários aprovados; novos testes verificam canais simultâneos, isolamento do jogo, duplicatas, baseline, desconexão e limite512 inválido. Testes não substituem os apertos físicos. Modo PINSCAN de cinco fios preservado como ferramenta independente.
