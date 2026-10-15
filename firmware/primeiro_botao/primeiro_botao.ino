// ESP32-WROOM-32: botão normalmente aberto entre D15 (GPIO15) e GND.
// Mantenha o botão solto ao ligar ou reiniciar a placa.
constexpr uint8_t BUTTON_PIN = 15;
constexpr uint32_t DEBOUNCE_MS = 5;
bool candidate;
bool stable;
uint32_t changedAt;
uint32_t lastReport;

void report(bool level) {
  Serial.println(level == LOW ? "BUTTON 1" : "BUTTON 0");
}

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  candidate = stable = digitalRead(BUTTON_PIN);
  changedAt = millis();
  Serial.println("GUITARHERO BUTTON-TEST v2 GPIO15");
  report(stable);
  lastReport = millis();
}

void loop() {
  const uint32_t now = millis();
  const bool level = digitalRead(BUTTON_PIN);
  if (level != candidate) {
    candidate = level;
    changedAt = now;
  }
  if (candidate != stable && uint32_t(now - changedAt) >= DEBOUNCE_MS) {
    stable = candidate;
    report(stable);
    lastReport = now;
  }
  // Heartbeat: lets the host release virtual input if the firmware stops.
  if (uint32_t(now - lastReport) >= 250) {
    report(stable);
    lastReport = now;
  }
  delay(1);
}
