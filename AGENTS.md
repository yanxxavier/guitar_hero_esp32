# Guitar Lab — continuidade

Este projeto constrói uma guitarra por cabo com ESP32, ponte Linux e dashboard local.

- Documentação principal e histórico: `/home/yanxxavier/Documents/SecondBrain/Pessoal/Projetos/GuitarHero`. Leia o `AGENTS.md` do cofre, Contexto e última sessão antes de retomar. Esse caminho pode mudar em outra máquina.
- Ao concluir cada etapa, atualize Contexto e salve sessão no Obsidian. Diferencie código, teste simulado, teste físico e teste no jogo.
- Preserve dados por cabo. Decisão de 14/10/2026: completar bancada no Zorin primeiro; validar ROG Ally em uma das últimas etapas de bancada, obrigatoriamente antes de começar a construção impressa. Não exigir Ally antes de expandir entradas.
- Ligação atual de bancada: D15/GPIO15 para Green e D13/GPIO13 para palhetada, cada chave normalmente aberta ligada a GND, INPUT_PULLUP. Botão solto na inicialização. Desenhos D16 são históricos.
- Nunca publique backups de flash, logs de execução, credenciais ou dependências locais.
- Registre mudanças no GitHub `yanxxavier/guitar_hero_esp32` após verificações. Não force atualizações sobre trabalho remoto.
- Não execute o servidor web como root. O script de permissões exige sudo somente para configurar udev.
- Firmware v5 implementa D15 (Green), D13 (palhetada) e B10K no D34 (whammy; extremos 3V3/GND). Green e palhetada validados no jogo por relato; whammy implementado, curso/calibração e mapeamento no jogo pendentes. Protocolo STATE N A, saída ABS_Z 0–4095. Não apresentar outros controles como validados.

- Atualização 16/10/2026: montagem atual tem somente cinco cores no braço, D15/D18/D19/D21/D13 para GND; palhetada, Start e Select não instalados. Firmware v7 lê cinco frets, mantendo protocolo STATE N A e whammy D34. Testes físicos dos cinco switches definitivos pendentes. Relatos anteriores D13 são da bancada anterior. Ver docs/cinco-cores.md.
- Correção 16/10: D22 não disponível; laranja usa D13. Não configurar palhetada no D13 enquanto laranja estiver ali. Escolher outro GPIO para palhetada futura.

- 18/10: fios dos cinco frets religados sem identificação de cores em D17/D16/D18/D21/D15. Mapa anterior perdeu validade. Modo temporário PINSCAN identifica pinos, sem comandos para o jogo; não atribuir cores antes do teste sequencial. Ver docs/identificar-fios.md. Quatro switches extras disponíveis/instalados por relato, ligações ainda não confirmadas.

- Mapa identificado pelo usuário em 18/10 após PINSCAN: verde D21, vermelho D18, amarelo D16, azul D17, laranja D15. Firmware v8 e dashboard usam este mapa; substitui mapas anteriores. Manter LARANJA solto no boot (GPIO15). Azul só responde com força maior: causa ainda não diagnosticada, não apresentar como corrigido. Quatro switches extras ainda sem ligação elétrica confirmada, sem implementação no firmware v8. PINSCAN é ferramenta de diagnóstico opcional, não firmware ativo após v8.

- Atualização 18/10: CHANNELS v9 mantém cores21/18/16/17/15 e lê canais adicionais D25/D32/D26/D27 sem função atribuída. Usuário ainda NÃO ligou esses quatro fios ao ESP32. Dashboard serve para identificar; ponte envia apenas cinco frets (mask & 61) e whammy, extras neutros para jogo até confirmação. STATE suporta0–511 apenas no v9. Ver docs/canais-adicionais.md. Azul falha mesmo sem botão impresso, causa pendente.

- Correção posterior 18/10: usuário conectou quatro sinais em D13/D14/D27/D26 e reconectou ESP32. CHANNELS v10 lê esses canais; funções ainda não identificadas. Substitui D25/D32 do v9. Não habilitar extras para jogo até confirmar correspondência física.

- Funções dos quatro extras confirmadas posteriormente em18/10: cima D27, baixo D14, Start D13, Select/Star Power D26. Dashboard com rótulos funcionais e contadores; CHANNELS v10 continua ativo sem nova gravação. Ponte ainda filtra extras (mask & 61); habilitação Linux e teste no jogo pendentes. Azul D17 segue com falha, sem reparo confirmado.

- Atualização20/10/2026: usuário solicitou inverter palhetadas: **CIMA D14, BAIXO D27**. StartD13/SelectD26 mantidos. CHANNELS v10 lê GPIOs brutos, sem alteração/gravação; rótulos e ordem visual atualizados no dashboard. Extras ainda filtrados da ponte, teste no jogo pendente. Substitui orientação cima27/baixo14 dos registros anteriores.

- Primeira gameplay20/10: ponte habilitada para nove comandos em CHANNELS v10 (sem novo upload); cimaD14→BTN_MODE, baixoD27→BTN_EAST, StartD13→BTN_START, SelectD26→BTN_SELECT. Máscara completa0–511, todos liberados em timeout/desconexão. Cinco cores/whammy mantidos; nome/capacidades do controle preservados. Testes de mapeamento/saída real/jogo devem ser documentados, não presumir gameplay concluída nem azul corrigido. Ver docs/primeira-gameplay.md.

- Desktop20/10: `desktop.app` v0.1 substitui o painel como interface principal. Instaladores/atalhos Linux e Windows; pinagem visual, identificação, configuração de áudio e músicas online. No Linux usa a ponte existente; Windows usa teclas restritas ao CloneHero em foco, sem eixo whammy analógico e sem validação física Windows ainda. Nunca apresentar Windows/Ally como testado por ter código/CI. Whammy físico desativado por padrão; usuário confirmou som normal após desativar WhammySFX. Azul segue pendente.
- Firmware ativo continua CHANNELS v10; CONFIG v11 em `firmware/configuravel` é opcional e foi apenas compilado. Permite novosGPIOs por CFG/PINS e persiste no ESP32; gravação exige ação explícita pela interface. Não usar dashboard legado com v11/pinagem personalizada. Aplicativo e dashboard agora compartilham trava de propriedade; não abrir serial em paralelo. GUI renderizada em teste offscreen não comprova interação física na janela do usuário. Ver `docs/aplicativo.md`.
- Validação posterior20/10: usuário confirmou que a janela desktop abriu, conectou e verde acendeu. CI Linux/Windows passou no run39407567932 (código/interface/ABI, sem hardware). Isso não valida os demais switches/remapeamento físico, partida noapp, firmwarev11 ou guitarra noWindows/Ally. Aplicativo permaneceu aberto noZorin, dashboard web antigo encerrado.
