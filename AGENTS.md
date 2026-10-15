# Guitar Lab — continuidade

Este projeto constrói uma guitarra por cabo com ESP32, ponte Linux e dashboard local.

- Documentação principal e histórico: `/home/yanxxavier/Documents/SecondBrain/Pessoal/Projetos/GuitarHero`. Leia o `AGENTS.md` do cofre, Contexto e última sessão antes de retomar. Esse caminho pode mudar em outra máquina.
- Ao concluir cada etapa, atualize Contexto e salve sessão no Obsidian. Diferencie código, teste simulado, teste físico e teste no jogo.
- Preserve dados por cabo. Decisão de 14/10/2026: completar bancada no Zorin primeiro; validar ROG Ally em uma das últimas etapas de bancada, obrigatoriamente antes de começar a construção impressa. Não exigir Ally antes de expandir entradas.
- Ligação atual de bancada: D15/GPIO15 para botão normalmente aberto e GND, INPUT_PULLUP. Botão solto na inicialização. Desenhos D16 são históricos.
- Nunca publique backups de flash, logs de execução, credenciais ou dependências locais.
- Registre mudanças no GitHub `yanxxavier/guitar_hero_esp32` após verificações. Não force atualizações sobre trabalho remoto.
- Não execute o servidor web como root. O script de permissões exige sudo somente para configurar udev.
- Apenas o botão D15 está implementado no hardware. Não apresentar outros controles como validados.
