# Guitar Lab 0.1.0 beta 2

Atualiza o Guitar Lab e o firmware CONFIG v11 para a nova pinagem da guitarra por cabo. Inclui D12 como entrada configurável e mantém o manual ilustrado/offline, configuração do Clone Hero e busca de músicas.

## Downloads

- **Windows x64:** baixe o ZIP, extraia tudo e abra `GuitarLab.exe`.
- **Linux x64:** baixe o TAR.GZ, extraia e abra `GuitarLab`.
- **Manual-GuitarLab.html:** manual completo offline, com imagens e passo a passo. Também incluído nos pacotes e acessível no app pelo menu Ajuda/F1.
- **SHA256SUMS.txt:** hashes dos downloads.

Mantenha a pasta `_internal` junto do executável. Os pacotes incluem o runtime e não exigem instalação de Python. Não incluem Clone Hero, músicas, dados pessoais, flash de bancada ou o modelo3MF.

## Estado desta beta

Linux: nove entradas identificadas por três apertos/solturas na leitura direta do ESP32. O firmware v11 atualizado foi gravado, confirmou e persistiu o mapa D16/D18/D26/D33/D14/D15/D12/D13/D25, na ordem Verde/Vermelho/Amarelo/Azul/Laranja/Cima/Baixo/Start/Select. Usuário confirmou que o teste visual no Guitar Lab deu certo. Linux e Windows: testes automáticos de código e abertura dos executáveis empacotados. Uma partida completa com esta pinagem ainda precisa de validação específica.

Windows ainda precisa de teste com a guitarra física/ROG Ally. A saída usa as teclas A/S/J/K/L, ↑/↓, Enter e H, somente com Clone Hero em primeiro plano. Whammy analógico não está disponível no Windows. Partida completa pelo aplicativo ainda precisa de validação física.

CONFIG v11 incluído aceita D12 e já foi gravado nesta guitarra por solicitação do usuário. Em novas instalações, a atualização só acontece quando acionada e confirmada. D12 e D15 são pinos de boot; mantenha os botões ligados a eles soltos ao ligar/reiniciar. PINSCAN foi diagnóstico temporário, substituído pelo firmware da guitarra após o mapeamento. O azul D33 respondeu no diagnóstico; a falha mecânica histórica no azul não foi declarada resolvida.

Linux: Ubuntu22.04+/glibc2.35 ou mais recente, x86_64. Windows:10/11 x64. Pacotes beta sem assinatura de editor.

O repositório permanece privado: faça login no GitHub para acessar os downloads. Perfis, backups e músicas ficam separados da pasta do programa.
