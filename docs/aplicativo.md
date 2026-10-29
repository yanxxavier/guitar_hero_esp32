# Guitar Lab — aplicativo Linux, Windows e macOS

## macOS (execução pelo código-fonte)

Crie um ambiente virtual e instale `requirements-desktop.txt` e `requirements.txt`; depois execute `python -m desktop.app`. É necessária conexão à internet para baixar as dependências na primeira instalação. A serial USB aparece no seletor de portas. O macOS usa saída por teclado apenas enquanto Clone Hero está em primeiro plano (A/S/J/K/L, ↑/↓, Enter e H); configure essas teclas no jogo. Autorize Automação e Acessibilidade para o terminal/Python que executa o app, se solicitado. Whammy analógico não está disponível no macOS. A gravação de firmware é suportada pela preparação do Arduino CLI ARM64 ou Intel, mas ainda requer download do core ESP32.

O aplicativo substitui a página de bancada por uma janela local. A aba Guitarra funciona sem internet; Músicas consulta o catálogo público Chorus Encore online.

## Instalação

Para usar sem ambiente de desenvolvimento, prefira os pacotes em [Releases](https://github.com/yanxxavier/guitar_hero_esp32/releases): ZIP Windows x64 e TAR.GZ Linux x64. Extraia a pasta inteira e mantenha `_internal` junto do executável. Leia o [manual ilustrado](manual.md), também incluído como HTML offline e acessível por **Ajuda → Manual do aplicativo (F1)**. O Linux é compilado em Ubuntu22.04/glibc2.35; Windows permanece experimental, sem teste físico e sem eixo whammy.

As instruções abaixo são para executar a partir do código-fonte.

Linux/Zorin: execute `bash tools/install-desktop.sh` na pasta do projeto. Depois abra **Guitar Lab** pelo menu de aplicativos. O instalador usa o ambiente `.venv`; não execute o aplicativo como root. Permissões udev: botão **Configurar permissões do Linux** apresenta o pedido de autenticação do sistema para o script existente.

O script concede acesso da sessão gráfica ativa a uinput, ao dispositivo virtual deste projeto e à serial CH340 VID1a86/PID7523. Não adiciona o usuário ao grupo input nem concede acesso a teclados. Reaplique pelo botão se este computador ainda usar as regras antigas sem a linha da serial.

Em Ubuntu/Zorin, se faltar libxcb-cursor0, o instalador baixa o pacote do repositório do sistema e extrai a biblioteca em `.tools/qt-runtime`, sem instalação global ou sudo. Outras distribuições devem fornecer essa dependência pelo próprio gerenciador de pacotes.

Windows pelo código-fonte: instale Python 3.10+ de [python.org](https://www.python.org/downloads/windows/), execute `tools/install-desktop.bat` e depois `tools/start-guitar-lab.bat`. Instala dependências em `.venv`, sem evdev no Windows. A saída Windows precisa de teste real nessa plataforma. Se o conversor USB CH340 não aparecer, o botão de driver abre o fabricante WCH; nenhum driver é instalado silenciosamente.

Não abra o antigo dashboard e o aplicativo simultaneamente. Ambos usam a mesma trava de propriedade; a serial também é exclusiva. Fechar o aplicativo encerra a ponte e libera os comandos. Deixe-o aberto durante o jogo. Ao remover o USB, os comandos são liberados e a conexão é tentada novamente enquanto Conectar estiver ativo.

## Guitarra visual e terminais

Clique na seta de uma função na guitarra. **Identificar pelo botão físico** atribui o próximo pino pressionado; clique somente no switch solicitado. **Usar este terminal** salva o GPIO escolhido. Quando o terminal já pertence a outra função, ambas trocam de lugar, preservando nove sinais únicos. LEDs e contadores refletem o estado recebido, e a coluna Segurado mostra a duração atual/última de cada acionamento.

Firmware v10 ativo: pode reatribuir as funções entre os nove terminais já lidos:21/18/16/17/15/14/27/13/26. Um GPIO fora desse conjunto exige o firmware opcional CONFIG v11, disponível em Configuração. A gravação é uma ação explícita do usuário; não ocorre ao abrir o app. Não abrir monitor serial paralelo.

CONFIG v11 aceita GPIO4/12/13/14/15/16/17/18/19/21/22/23/25/26/27/32/33, nove entradas únicas; debounce5ms, heartbeat250ms e protocolo STATE0–511. `CFG PINS p0,...,p8` altera e persiste a pinagem, `PINS p0,...,p8` confirma. Num primeiro perfil sem arquivo salvo, o app importa a ordem `PINS` do firmware; perfis existentes são preservados. Ordem: verde/vermelho/amarelo/azul/laranja/cima/baixo/Start/Select. `GET PINS` consulta. GPIO12 e GPIO15 devem estar soltos ao ligar/reiniciar, pois são pinos de boot. Ligações NO entre GPIO e GND, nunca5V nas entradas. Desconecte USB para mudar fios; após ligar, confira o painel antes do jogo.

O botão **Preparar ferramentas de gravação · online** verifica Arduino CLI e o core ESP32. Se faltarem, baixa Arduino CLI1.5.1 oficial para Linux/Windows x86_64, confere SHA256 publicado e instala core2.0.17 numa área do aplicativo, sem substituir core de outro projeto. O botão de gravação também prepara essas ferramentas se necessário. Não grava firmware apenas ao preparar ferramentas. Reutiliza `.tools/bin/arduino-cli` ou PATH quando disponíveis. Placa `esp32:esp32:esp32`. Outras arquiteturas exigem instalação manual. [Arduino CLI](https://docs.arduino.cc/arduino-cli/installation/), [core ESP32](https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html).

O dashboard legado é histórico e espera v10; use o aplicativo para v11/pinagem personalizada. A versão ativa do ESP32 não é alterada pela instalação do aplicativo.

Os pacotes portáteis incluem firmware CONFIGv11 compilado deste repositório, manifesto SHA256 e esptool. A gravação opcional usa esses arquivos sem exigir Arduino/Python externos. O modo código-fonte mantém a preparação Arduino CLI descrita acima. Não são incluídos backups de flash. Compilar/distribuir v11 não comprova gravação ou validação física.

## Configuração do jogo e whammy

Escolha executável, pasta de dados (contém settings.ini) e pasta de músicas. O botão de configuração inicial salva backup local e ajusta somente `[audio] whammy_sfx`. Recusa edição enquanto Clone Hero estiver aberto. Mapeamento do perfil do jogador continua sendo feito dentro do jogo.

Whammy físico vem desativado: a saída analógica permanece neutra mesmo se ADC34 oscilar. Ative somente quando o B10K estiver instalado. O efeito sonoro é uma opção separada, desativada por padrão porque o usuário confirmou normalização do som após `whammy_sfx=0` em20/10. Isso não comprova reparo do azulD17 nem avaliação completa da guitarra.

Linux usa Guitar Lab Virtual Controller com o mesmo nome/capacidades do dashboard: Green/SOUTH, Red/NORTH, Yellow/WEST, Blue/TL, Orange/TR, cima/MODE, baixo/EAST, Start/START e Select/SELECT. Whammy opcional ABS_Z0–4095.

Windows usa teclas A/S/J/K/L,↑/↓,Enter,H para essas nove funções, somente com clonehero.exe em primeiro plano, e libera as teclas ao perder foco/desconectar. Não exige ViGEm ou outro driver de gamepad. Configure essas teclas no jogo; whammy analógico Windows ainda não disponível, portanto o checkbox não deve ser entendido como eixo implementado no Windows. [Microsoft SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput). Teste real no Windows/Ally permanece pendente.

## Músicas

Busque por banda/música, filtre dificuldade, marque uma ou várias linhas e baixe. Pode haver charts diferentes da mesma música: confira dificuldades e charter. A fila mostra sucessos e erros individualmente; quota do Drive/arquivo removido não é contornada. SNG, ZIP e pastas individuais de origem suportados; pacotes7z e fontes grandes devem ser abertos manualmente ou substituídos por outro chart.

Instalação usa pasta temporária na biblioteca, valida SNG ou chart/áudio e título/artista, não sobrescreve músicas existentes e bloqueia caminhos de ZIP que saiam da pasta. Não executa arquivos baixados. Os nomes incluem ChartID para evitar colisão de versões. Depois execute **Settings → General → Scan Songs** no jogo. O app não automatiza a interface do jogo. [Manual oficial](https://wiki.clonehero.net/books/clone-hero-manual/page/scanning-songs), [Encore](https://www.enchor.us/), [Bridge/API de catálogo](https://github.com/Geomitron/Bridge), [gdown](https://github.com/wkentaro/gdown).

Perfil, backups e manifestos ficam em `~/.config/guitar-lab` no Linux ou `%APPDATA%/GuitarLab` no Windows. Músicas ficam somente na pasta escolhida. Nenhum desses dados, flash ou logs deve ser publicado no GitHub.
