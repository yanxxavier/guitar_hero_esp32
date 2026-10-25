# Teste livre de portas — ESP32-WROOM-32

Sketch temporário: `firmware/teste_portas/teste_portas.ino`. Somente para ESP32 clássico WROOM sem PSRAM. Identifica GPIOs brutos, sem salvar funções/NVS e sem saída para jogo. Não substitui o PINSCAN v3 usado pelo leitor Python; protocolo deste sketch é texto humano no Monitor Serial.

## Uso
1. Feche Guitar Lab/dashboard e qualquer leitor serial para liberar a porta.
2. Arduino IDE: abra o sketch, selecione ESP32 Dev Module e a porta do ESP. Upload substitui temporariamente o firmware de jogo; faça essa ação explicitamente, sem apagar toda a flash.
3. Deixe todos os botões soltos durante gravação/reset, especialmente GPIO0/2/5/12/15. Mantenha tilt na posição de contato aberto se ligado a algum desses GPIOs.
4. Monitor Serial: 115200 baud. Aperte e solte um botão por vez, três vezes. Anote função física e GPIO mostrado. Não atribua funções com base só em LOW inicial.
5. Envie S para listar estados, H para ajuda, R para alternar visualização de34/35/36/39. Esses quatro são somente entrada, sem pullup interno: use10k entre GPIO e3V3 para leitura confiável de chave paraGND. Ruído não identifica botão. VP=36 eVN=39 nas placas que usam esses rótulos.
6. Depois do teste, restaurar CONFIG v11 e aplicar apenas o mapa confirmado. O sketch não escreve NVS, mas durante o diagnóstico não há controle de jogo. A pinagem anterior não representa necessariamente o chicote de teste novo.

Entradas com pullup:0,2,4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33. Lê34,35,36,39 em INPUT, exibidos apenas quando habilitados. Dn refere-se ao GPIO, não ao número físico do terminal. GPIO6–11 são flash, não conectar botões. GPIO1/3 ficam para a serial USB. GPIO20/24/28–31/40 não existem neste ESP32;37/38 não são expostos no módulo WROOM. Não testar alimentação, EN, VIN ou3V3 como GPIO.

Chaves normalmente abertas ligadas entre GPIO eGND. Não injetar5V. LOW significa contato fechado/nível baixo, não prova que houve aperto: tilt, curto ou ligação fixa também podem gerar LOW. Debounce25ms, sem contagem automática nem gravação de mapeamento.

Validação: compilação com esp32:esp32:esp32/core2.0.17; teste físico e gravação deste diagnóstico ainda pendentes. Fonte técnica: https://docs.espressif.com/projects/esp-idf/en/release-v4.3/esp32/api-reference/peripherals/gpio.html
