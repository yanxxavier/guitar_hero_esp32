# Green + palhetada — firmware v3

## Ligações

| Função | GPIO | Chave normalmente aberta | Saída Linux |
| --- | --- | --- | --- |
| Green | D15 / GPIO15 | Entre D15 e GND | BTN_SOUTH |
| Strum Down | D23 / GPIO23 | Entre D23 e GND | BTN_EAST |

Terra comum às duas chaves. Em cada botão de quatro pernas, usar duas pernas que **não** têm continuidade em repouso e têm continuidade ao pressionar. GPIO15 participa do boot: manter Green solto ao ligar/reiniciar. Os desenhos D16 antigos não representam esta bancada.

## Protocolo

115200 baud, 8N1, texto ASCII terminado em newline:

- Identificação: `GUITARHERO TWO-BUTTON v3 GPIO15 GPIO23`.
- Estado completo: `STATE N`, onde N é máscara decimal de 0 a 3.

| Quadro | Green | Palhetada |
| --- | --- | --- |
| STATE 0 | solto | solta |
| STATE 1 | pressionado | solta |
| STATE 2 | solto | pressionada |
| STATE 3 | pressionado | pressionada |

Debounce independente de 5 ms por chave. Envio após mudanças estáveis e a cada 250 ms. Enviar ambos os estados no mesmo quadro preserva Green durante palhetadas. A ponte envia apenas mudanças de cada botão e sincroniza o quadro no uinput. Watchdog de 1,5 s, desconexão e encerramento liberam ambos.

## Teste em bancada e no jogo

1. Atualizar o dashboard. Em repouso, os dois indicadores devem mostrar **Solto**.
2. Apertar cada botão separadamente; verificar indicador e contador correspondentes.
3. Segurar Green e apertar/soltar palhetada várias vezes: Green deve continuar ativo.
4. Ler saída Linux com `.venv/bin/python tools/verify_virtual_input.py --seconds 60`: BTN_SOUTH acompanha D15; BTN_EAST acompanha D23.
5. No Clone Hero, manter Green mapeado como Button 0. Em Controller Remap, selecionar a célula **Controller** da linha **Strum Down** e apertar D23. Conferir identificação capturada, salvar em Done. Pode ser necessário reatribuir o controle após reinício da ponte.
6. Segurar Green e usar D23 para palhetar uma nota verde no tempo correto. O mapeamento D23 no jogo só é validado após esse teste real.

## Estado da implementação

Firmware v3 compilado e gravado com verificação de hash; 15 testes de lógica aprovados. Boot real confirmou identificação v3, Green solto e D23 inicialmente pressionado. Precisamos conferir D23 em repouso, transições físicas e mapeamento no jogo antes de declarar a segunda entrada validada.

Sequência confirmada pelo usuário: completar bancada no Zorin; validar ROG Ally entre as últimas etapas antes da construção impressa.
