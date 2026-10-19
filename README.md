# Guitar Lab — bancada ESP32

Projeto documentado em `/home/yanxxavier/Documents/SecondBrain/Pessoal/Projetos/GuitarHero`.

## Identificação temporária dos fios — 18/10/2026

Chicote do braço religado em D17/D16/D18/D21/D15 sem identificação de cores. Usar [modo PINSCAN](docs/identificar-fios.md) para apertar uma cor por vez e descobrir pino; ponte fica neutra durante diagnóstico. O mapa v7 abaixo é histórico e precisa ser atualizado antes de voltar ao jogo.

## Configuração anterior — firmware v7, cinco cores

- Montagem atual: switches no braço, na ordem verde a laranja, em **D15/D18/D19/D21/D13**, todos para GND comum com INPUT_PULLUP.
- **Palhetada, Start e Select não instalados nesta montagem.** Validação anterior de palhetada D13 é histórica.
- B10K/D34 continua suportado; estado da conexão física do whammy nesta montagem ainda não reconfirmado.
- Dashboard mostra cinco indicadores e contadores individuais; combinações de cores preservadas na ponte Linux.
- [Mapa, protocolo e teste das cinco cores](docs/cinco-cores.md). Green mantém BTN_SOUTH; quatro novas cores usam BTN_NORTH/WEST/TL/TR. Palhetada BTN_EAST reservado para compatibilidade.
- Relatos anteriores validaram Green/palhetada na bancada anterior, whammy no painel e captura Axis 2; ainda é preciso testar os cinco switches definitivos na montagem atual.

Demais seções abaixo registram etapas anteriores.

## Bancada em 14/10/2026

- Zorin OS 18.1; ESP32-D0WD-V3 rev. 3.1, flash de 4 MB, conversor CH340.
- Porta persistente: `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` (`/dev/ttyUSB0`).
- Usuário informou botão normalmente aberto entre **D15 e GND**. Imagens anteriores com D16 não correspondem à ligação atual.
- GPIO15 usa `INPUT_PULLUP`; manter botão solto ao ligar/reiniciar.
- Acesso serial liberado pelo usuário com ACL temporária. `/dev/uinput` ainda restrito a root.
- Firmware `firmware/primeiro_botao/primeiro_botao.ino`: debounce de 5 ms, 115200 baud; `BUTTON 1` pressionado e `BUTTON 0` solto.
- Compilação aprovada: Arduino ESP32 2.0.17, placa `esp32:esp32:esp32`; log em `logs/compile-primeiro-botao.log`.
- Ferramentas locais: `.tools/bin/arduino-cli` e `.venv/bin/python` (esptool 5.5.0, pyserial 3.5).
- Backup da flash original reservado em `backups/esp32-original-2026-10-14.bin`; conteúdo privado, ignorado pelo Git.

Monitor: `.venv/bin/python tools/monitor_botao.py`. Registro em `logs/botao-serial.log`.

Ainda não declarar botão validado até observar apertos e solturas reais. Ponte uinput, Clone Hero e ROG Ally continuam pendentes.

## Resultado de preparação
Backup completo salvo (4.194.304 bytes, SHA256 em arquivo ao lado). Firmware de teste gravado com verificação de hash aprovada em 14/10/2026. Monitor serial iniciado; aguardando interação do usuário para validar o botão.

## Guitar Lab — painel visual local

Abra **http://127.0.0.1:8765** no navegador do Zorin.

Para iniciar novamente, na pasta deste projeto:

```bash
.venv/bin/python dashboard/server.py
```

O painel assume a porta serial; feche `tools/monitor_botao.py`, Arduino Serial Monitor ou outro leitor antes de iniciar. Ele reinicia a placa ao conectar para obter identificação e estado inicial: mantenha o botão solto. Não grava firmware. Após reconectar o USB, a ACL pode precisar ser aplicada novamente com `sudo setfacl -m u:yanxxavier:rw /dev/ttyUSB0`.

- Teste ao vivo: estado físico do D15, apertos, solturas, mensagens e nova contagem.
- A primeira leitura após conexão é uma referência; não conta como aperto.
- Desconexão deixa o estado desconhecido; tentativa de reconexão a cada 2 segundos.
- Validação do projeto: marcações manuais persistidas em `logs/dashboard/checks.json`.
- Eventos persistidos em `logs/dashboard/events.jsonl`; a tela e a exportação mostram até 120 eventos da execução atual.
- Exportação JSON com estado, contagem, etapas e eventos atuais. Não mede latência ponta a ponta.
- Cinco frets, palhetas, Start/Select e whammy são apresentados como pendentes; só D15 está implementado.
- Serviço restrito a `127.0.0.1`; sem publicação externa. Ctrl+C no terminal encerra.

Verificações: ` .venv/bin/python -m unittest discover -s tests -v` valida estados iniciais, duplicatas, ruído e desconexão. Em 14/10/2026 o serviço recebeu identificação do firmware e `BUTTON 1` real. A inspeção visual automatizada foi bloqueada pela permissão do navegador; não foi concluída.

## Ponte para o controle virtual

Instale dependências com `.venv/bin/python -m pip install -r requirements.txt`. O pacote evdev-binary é a distribuição de wheels indicada na documentação do python-evdev; evita exigir headers Python no Zorin.

Uma vez, configure permissões:

```bash
sudo bash tools/setup-permissions.sh
```

O script instala `/etc/udev/rules.d/70-guitar-lab.rules`, ativa o módulo uinput e permite acesso à sessão gráfica local ativa. Não adiciona o usuário ao grupo input nem libera dispositivos de teclado. Para reverter: remover essa regra com sudo, recarregar udev e reiniciar. Em uma sessão sem desktop ativo, a regra uaccess pode não conceder acesso; não executar o dashboard como root como alternativa.

O servidor tenta criar **Guitar Lab Virtual Controller** automaticamente e mostra erro se faltar permissão. D15 emite **BTN_SOUTH**, primeiro botão/A, para mapeamento no jogo. Eixos X/Y e outros botões são anunciados para reconhecimento como gamepad, mas estão neutros e não representam hardware implementado.

Firmware **v2**: estado inicial, mudanças com debounce de 5 ms e heartbeat a cada 250 ms. A ponte libera o botão em desconexão, encerramento ou ausência de quadros por 1,5 s. Manter o botão apertado continua funcionando graças ao heartbeat; v1 não deve ser usada com esta ponte.

No dashboard, a saída Linux confirma chamadas de escrita, enquanto a seção de navegador usa Gamepad API quando disponível. Ausência nessa API não prova ausência no jogo. Ainda é necessário testar no Clone Hero: abrir o jogo depois de criar o controle, entrar no mapeamento e apertar o botão físico para atribuir uma entrada. Com um único botão só validamos detecção/mapeamento, não uma guitarra jogável.

## GitHub e documentação

Repositório privado: https://github.com/yanxxavier/guitar_hero_esp32

`AGENTS.md` descreve a continuidade. `docs/continuidade.md` mantém um resumo portátil; o contexto completo, decisões e sessões ficam no Obsidian em `Pessoal/Projetos/GuitarHero`. Backups e logs nunca devem ser enviados ao GitHub. As imagens D16 em docs são históricas; a ligação atual é D15/GND.

### Validação em 14/10/2026
Regras instaladas pelo usuário, firmware v2 gravado com hash verificado e controle virtual criado pelo kernel (`event18`/`js0` nesta execução). Três apertos e solturas físicos foram lidos de volta independentemente pelo Linux com BTN_SOUTH 1/0. O teste no Clone Hero permanece pendente. Para repetir a leitura independente: `.venv/bin/python tools/verify_virtual_input.py --seconds 60`.
