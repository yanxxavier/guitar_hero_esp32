# Primeira gameplay — nove comandos habilitados em20/10/2026

Firmware CHANNELS v10 continua, sem nova gravação. Ponte passou a aceitar/enviar máscara0–511 completa após funções físicas identificadas. Capacidades/nome do controle virtual preservados; nove botões antes anunciados agora recebem entradas reais. Watchdog1,5s, desconexão e encerramento liberam todos e zeram whammy. Testes de lógica não comprovam aceitação pelo jogo.

| Função | GPIO | Bit serial | Saída Linux |
| --- | --- | --- | --- |
| Verde | D21 | 1 | BTN_SOUTH |
| Vermelho | D18 | 4 | BTN_NORTH |
| Amarelo | D16 | 8 | BTN_WEST |
| Azul | D17 | 16 | BTN_TL |
| Laranja | D15 | 32 | BTN_TR |
| Palhetada cima | D14 | 2 | BTN_MODE |
| Palhetada baixo | D27 | 256 | BTN_EAST |
| Start | D13 | 64 | BTN_START |
| Select / Star Power | D26 | 128 | BTN_SELECT |
| Whammy | D34 | ADC | ABS_Z0–4095 |

Palhetada baixo mantém saída BTN_EAST antiga, mas agora vem do D27; cima usa BTN_MODE antes neutro. Não inferir botão do jogo só pelo nome Linux: mapear acionando comando físico no Controller Remap. Perfil do jogo pode precisar reatribuir controle após reinício da ponte. Não editar configurações do jogo enquanto ele está aberto.

Procedimento: abrir mapeamento com Espaço no menu principal, Player1, selecionar/atribuir Guitar Lab Virtual Controller. Conferir cinco cores, Strum Up, Strum Down, Start Button e Select Button/Star Power na coluna Controller, uma função por vez. Whammy Axis capturou Axis2 anteriormente; conferir antes de remapear. Salvar Done. Jogar dificuldade Easy, escolhendo música lenta conhecida; primeira rodada avalia notas, palhetada e pausa/menus. Não exigir whammy na mesma rodada. Se controle não reaparecer, fechar/reabrir jogo com dashboard rodando.

Azul D17 teve falha mesmo sem botão impresso; reparo não confirmado. Não marcar corrigido por estar solto em leitura inicial. Primeira rodada Easy reduz necessidade de azul/laranja, sem comprovar confiabilidade das cinco cores. ROG Ally e reconexão/reinício/sessão longa permanecem pendentes.

30 testes unitários passaram incluindo nove saídas, combinações, limites e liberação. Leitura independente real do Linux e resultado dentro da música devem ser registrados separadamente.
