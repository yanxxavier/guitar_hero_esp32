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
# Aplicativo desktop — 20/10/2026

Distribuição beta0.1.0-beta.1: manual ilustrado em `docs/manual.md`, HTML offline incluído e aberto por Ajuda/F1. Workflow `release.yml` prepara firmware próprio v11, pacotes portáteis x64 Linux/Windows, testa inicialização sem hardware e publica em GitHub Releases com SHA256. Windows segue experimental por teclado em primeiro plano, sem whammy analógico ou teste físico. Linux validou conexão e verde na janela; demais entradas/jogo peloapp ainda pendentes. O firmware ativo não é alterado pela criação dos pacotes. Não incluir dados locais nem o3MF; empacotamento usa lista explícita de arquivos.

Guitar Lab0.1 em `desktop/`, inicialização `python -m desktop.app`; instaladores e atalhos em `tools/install-desktop.*` e `tools/start-guitar-lab.*`. Guia `docs/aplicativo.md`. Quatro abas: guitarra visual/pinagem/testes, configuração, músicas online e diagnóstico. Reutiliza Linuxuinput; Windows tem implementação por teclas A/S/J/K/L/↑/↓/Enter/H apenas com CloneHero em foco, mas precisa de validação real nessa plataforma e não oferece whammy analógico.

Firmware ativo ainda v10. Novo CONFIGv11 foi compilado, não gravado; instalação pela GUI é opcional para GPIOs novos. Preserva mapa21/18/16/17/15/14/27/13/26, salvo quando usuário remapear. Não apresentar falha azul como corrigida. Whammy desativado por padrão; som de sustains voltou ao normal por relato apósWhammySFX0. Dashboard antigo e aplicativo não devem disputar a porta. Trava compartilhada protege novas instâncias; processos antigos anteriores à mudança precisam ser encerrados uma vez na migração.

Verificação20/10:46 testes locais (um ABIWindows pulado noLinux), GUI offscreen, conexão real ao ESP32v10 e criação de controle Linux, busca online e downloadSNG real para diretório temporário. Usuário confirmou janela aberta/conectada e verde acendendo. CI Linux e Windows passou no run39407567932, incluindo construção da interface e ABIWindows, sem hardware. Demais controles/remapeamento na janela, partida usandoapp, gravaçãov11 e Windows/Ally físicos ainda pendentes. Não publicar logs, perfis, músicas ou3MF do usuário.
