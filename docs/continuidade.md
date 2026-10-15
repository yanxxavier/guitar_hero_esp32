# Estado atual — 15/10/2026

Firmware v5: Green D15/GND e palhetada D13/GND, ambos validados no jogo por relato. B10K com extremos 3V3/GND e cursor D34 confirmado pelo usuário; leitura ADC e eixo ABS_Z implementados, teste de movimento/calibração/mapeamento ainda pendente. Ver [whammy](whammy.md). Completar bancada Zorin; Ally antes da construção impressa.

Registros abaixo são históricos.

# Estado de bancada — 14/10/2026

## Validado
- Zorin 18.1, ESP32-D0WD-V3 rev. 3.1, CH340, 4 MB de flash.
- Backup original completo antes da primeira gravação (somente local).
- Botão físico D15/GND: par de pernas corrigido com multímetro; apertos e solturas recebidos por serial e confirmados pelo usuário no dashboard.
- Usuário adicionado ao grupo dialout na configuração do sistema; sessão atual ainda sem o grupo. Nova sessão/reinício é necessário para os processos herdarem a mudança.

## Implementação desta etapa
- Firmware v2 envia mudanças e estado a cada 250 ms.
- Ponte cria Guitar Lab Virtual Controller e mapeia D15 para BTN_SOUTH.
- Liberação em desconexão, saída do programa e silêncio superior a 1,5 s.
- Dashboard distingue estado serial, saída do Linux e leitura independente do navegador.
- Capacidades de gamepad reservadas para detecção SDL; demais botões/eixos não têm hardware implementado.
- Dez testes de lógica aprovados. Isso não prova reconhecimento no Clone Hero.

## Próximo teste
Configurar permissões uinput, conferir criação do controle, apertar e soltar botão, abrir Clone Hero e mapear uma entrada. Repetir depois no ROG Ally. Não declarar M1 concluído antes do teste no jogo.

## Fontes técnicas
- [python-evdev: UInput e envio de eventos](https://python-evdev.readthedocs.io/en/latest/tutorial.html#injecting-input)
- [python-evdev: instalação binária oficial](https://python-evdev.readthedocs.io/en/latest/install.html#binary-wheels)

Histórico e decisões completos no Obsidian, em Pessoal/Projetos/GuitarHero/IA/GuitarHero.

## Resultado real desta etapa
Regras udev instaladas pelo usuário, uinput acessível à sessão ativa. Firmware v2 compilado e gravado com verificação de hash. Kernel criou `/dev/input/event18` e `js0` (nomes podem mudar ao reiniciar). Verificador independente leu três pares completos de BTN_SOUTH 1/0 após apertos físicos do usuário. O dashboard recebeu cinco pares na rodada anterior. Dez testes de lógica aprovados. Clone Hero e ROG Ally ainda não testados. Interface visual nova ainda depende de atualização/conferência pelo usuário.
