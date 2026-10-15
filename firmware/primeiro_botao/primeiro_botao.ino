// ESP32-WROOM-32: chaves NO entre D15/GND (Green) e D23/GND (Strum Down).
// Mantenha Green solto ao ligar/reiniciar: GPIO15 é pino de configuração de boot.
constexpr uint8_t PINS[] = {15, 23};
constexpr uint32_t DEBOUNCE_MS = 5;
bool candidate[2];
bool stable[2];
uint32_t changedAt[2];
uint32_t lastReport;

void report() {
  // Quadro completo: bit 0 = Green, bit 1 = palhetada. 1 significa pressionado.
  const uint8_t mask = (stable[0] == LOW ? 1 : 0) | (stable[1] == LOW ? 2 : 0);
  Serial.print("STATE ");
  Serial.println(mask);
}

void setup() {
  for (uint8_t i = 0; i < 2; ++i) {
    pinMode(PINS[i], INPUT_PULLUP);
    candidate[i] = stable[i] = digitalRead(PINS[i]);
    changedAt[i] = millis();
  }
  Serial.begin(115200);
  Serial.println("GUITARHERO TWO-BUTTON v3 GPIO15 GPIO23");
  report();
  lastReport = millis();
}

void loop() {
  const uint32_t now = millis();
  bool changed = false;
  for (uint8_t i = 0; i < 2; ++i) {
    const bool level = digitalRead(PINS[i]);
    if (level != candidate[i]) {
      candidate[i] = level;
      changedAt[i] = now;
    }
    if (candidate[i] != stable[i] && uint32_t(now - changedAt[i]) >= DEBOUNCE_MS) {
      stable[i] = candidate[i];
      changed = true;
    }
  }
  if (changed || uint32_t(now - lastReport) >= 250) {
    report();
    lastReport = now;
  }
  delay(1);
}
