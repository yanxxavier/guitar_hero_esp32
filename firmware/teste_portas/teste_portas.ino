// Temporary interactive diagnostic for classic ESP32-WROOM-32 (no PSRAM).
// Switches between GPIO and GND. No game commands, WiFi, NVS or mapping writes.
// Do not use on S2/S3/C3/WROVER. GPIO6-11 are flash; 1/3 are USB serial UART.
#include <Arduino.h>
#if !defined(CONFIG_IDF_TARGET_ESP32)
#error "Este diagnostico exige o ESP32 classico, nao S2/S3/C3."
#endif
constexpr uint8_t PINS[] = {0,2,4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33,34,35,36,39};
constexpr size_t N = sizeof(PINS) / sizeof(PINS[0]);
constexpr uint32_t DEBOUNCE_MS = 25;
bool candidate[N], stable[N];
uint32_t changedAt[N];
bool showUnbiased = false;

void printPin(size_t i, bool initial) {
  Serial.print(initial ? "ESTADO " : "EVENTO ");
  Serial.print("GPIO"); Serial.print(PINS[i]);
  if (PINS[i] >= 34) {
    Serial.print(stable[i] == LOW ? " LOW" : " HIGH");
    Serial.println(" [SEM PULLUP: pode ser ruido se nao houver resistor externo]");
  } else {
    Serial.println(stable[i] == LOW ? " FECHADO / APERTADO" : " ABERTO / SOLTO");
  }
}
void snapshot() {
  Serial.println("--- Estados atuais (LOW inicial nao identifica botao) ---");
  for (size_t i=0; i<N; ++i) if (PINS[i]<34 || showUnbiased) printPin(i,true);
}
void help() {
  Serial.println("GUITAR LAB - TESTE PORTAS v1 - 115200 baud");
  Serial.println("Aperte e solte UM botao por vez, repetindo 3 vezes.");
  Serial.println("GPIOs: 0,2,4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33.");
  Serial.println("34,35,36,39: lidos como INPUT, exibicao opcional com R.");
  Serial.println("R alterna entradas sem pullup; S lista estados; H repete ajuda.");
  Serial.println("6-11: memoria flash. 1/3: serial. 37/38: nao expostos no WROOM.");
  Serial.println("20,24,28-31,40: nao sao GPIOs deste ESP32.");
  Serial.println("Solte os botoes ao reiniciar (especialmente 0,2,5,12,15).");
  Serial.println("Nao atribui cores, nao salva mapa e nao controla o jogo.");
}
void setup() {
  Serial.begin(115200);
  for (size_t i=0; i<N; ++i) {
    pinMode(PINS[i], PINS[i]>=34 ? INPUT : INPUT_PULLUP);
    candidate[i]=stable[i]=digitalRead(PINS[i]);
    changedAt[i]=millis();
  }
  delay(500); help(); snapshot();
}
void loop() {
  while (Serial.available()) {
    char c=Serial.read();
    if (c=='s'||c=='S') snapshot();
    if (c=='h'||c=='H') help();
    if (c=='r'||c=='R') {
      showUnbiased=!showUnbiased;
      Serial.println(showUnbiased ? "Entradas sem pullup VISIVEIS: use pullup externo de 10k para 3V3 para teste confiavel." : "Entradas sem pullup OCULTAS.");
      snapshot();
    }
  }
  uint32_t now=millis();
  for (size_t i=0; i<N; ++i) {
    bool level=digitalRead(PINS[i]);
    if (level!=candidate[i]) { candidate[i]=level; changedAt[i]=now; }
    if (candidate[i]!=stable[i] && uint32_t(now-changedAt[i])>=DEBOUNCE_MS) {
      stable[i]=candidate[i];
      if (PINS[i]<34 || showUnbiased) printPin(i,false);
    }
  }
  delay(1);
}
