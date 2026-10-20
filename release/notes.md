# Guitar Lab 0.1.0 beta 1

Aplicativo para configurar e testar a guitarra ESP32 por cabo, com guitarra visual e setas, identificação/remapeamento de terminais, configuração inicial do Clone Hero e busca online de músicas.

## Downloads

- **Windows x64:** baixe o ZIP, extraia tudo e abra `GuitarLab.exe`.
- **Linux x64:** baixe o TAR.GZ, extraia e abra `GuitarLab`.
- **Manual-GuitarLab.html:** manual completo offline, com imagens e passo a passo. Também incluído nos pacotes e acessível no app pelo menu Ajuda/F1.
- **SHA256SUMS.txt:** hashes dos downloads.

Mantenha a pasta `_internal` junto do executável. Os pacotes incluem o runtime e não exigem instalação de Python. Não incluem Clone Hero, músicas, dados pessoais, flash de bancada ou o modelo3MF.

## Estado desta beta

Linux: conexão real e botão verde na janela confirmados no Zorin. Linux e Windows: testes automáticos de lógica/interface/ABI e inicialização dos executáveis empacotados.

Windows ainda precisa de teste com a guitarra física/ROG Ally. A saída usa as teclas A/S/J/K/L, ↑/↓, Enter e H, somente com Clone Hero em primeiro plano. Whammy analógico não está disponível no Windows. Demais entradas/remapeamento e partida completa pelo aplicativo ainda precisam de validação física.

O firmware v10 atual continua compatível. CONFIG v11 incluído é opcional para GPIOs novos; só grava quando o usuário aciona a opção e confirma. O firmware foi compilado do código do projeto; sua gravação/pinagem configurável ainda está em teste.

Linux: Ubuntu22.04+/glibc2.35 ou mais recente, x86_64. Windows:10/11 x64. Pacotes beta sem assinatura de editor.

O repositório permanece privado: faça login no GitHub para acessar os downloads. Perfis, backups e músicas ficam separados da pasta do programa.
