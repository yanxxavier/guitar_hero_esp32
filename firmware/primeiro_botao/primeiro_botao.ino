// ESP32-WROOM-32: cinco switches NO para GND, na ordem verde a laranja.
// Mantenha Laranja solto ao ligar/reiniciar: GPIO15 é pino de configuração de boot.
constexpr uint8_t PINS[] = {21, 18, 16, 17, 15};
constexpr uint8_t BITS[] = {1, 4, 8, 16, 32};
constexpr uint8_t INPUT_COUNT = sizeof(PINS) / sizeof(PINS[0]);
constexpr uint32_t DEBOUNCE_MS = 5;
constexpr uint8_t WHAMMY_PIN = 34;
uint16_t whammy, reportedWhammy;
uint32_t lastSample;
bool candidate[INPUT_COUNT];
bool stable[INPUT_COUNT];
uint32_t changedAt[INPUT_COUNT];
uint32_t lastReport;

void report() {
  // Bits 0,2,3,4,5 = frets. Bit 1 reservado à palhetada histórica, ausente nesta bancada.
  uint8_t mask = 0;
  for (uint8_t i = 0; i < INPUT_COUNT; ++i)
    if (stable[i] == LOW) mask |= BITS[i];
  Serial.print("STATE ");
  Serial.print(mask);
  Serial.print(" ");
  Serial.println(whammy);
  reportedWhammy = whammy;
}

void setup() {
  for (uint8_t i = 0; i < INPUT_COUNT; ++i) {
    pinMode(PINS[i], INPUT_PULLUP);
    candidate[i] = stable[i] = digitalRead(PINS[i]);
    changedAt[i] = millis();
  }
  analogReadResolution(12);
  analogSetPinAttenuation(WHAMMY_PIN, ADC_11db);
  whammy = analogRead(WHAMMY_PIN);
  lastSample = millis();
  Serial.begin(115200);
  Serial.println("GUITARHERO FRETS v8 GPIO21 GPIO18 GPIO16 GPIO17 GPIO15 ADC34");
  report();
  lastReport = millis();
}

void loop() {
  const uint32_t now = millis();
  bool changed = false;
  for (uint8_t i = 0; i < INPUT_COUNT; ++i) {
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
  if (uint32_t(now - lastSample) >= 5) {
    whammy = (3 * uint32_t(whammy) + analogRead(WHAMMY_PIN)) / 4;
    lastSample = now;
  }
  const bool analogChanged = abs(int(whammy) - int(reportedWhammy)) >= 12;
  if (changed || (analogChanged && uint32_t(now - lastReport) >= 20) || uint32_t(now - lastReport) >= 250) {
    report();
    lastReport = now;
  }
  delay(1);
}
