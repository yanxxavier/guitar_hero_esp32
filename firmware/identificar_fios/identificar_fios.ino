// Diagnóstico temporário: descobrir fios sem atribuir cores ou gerar comandos de jogo.
constexpr uint8_t PINS[] = {17, 16, 18, 21, 15};
bool candidate[5], stable[5];
uint32_t changedAt[5], lastReport;
void report() {
  uint8_t mask = 0;
  for (uint8_t i=0; i<5; ++i) if (stable[i] == LOW) mask |= (1 << i);
  Serial.print("SCAN "); Serial.println(mask);
  lastReport = millis();
}
void setup() {
  for (uint8_t i=0; i<5; ++i) {
    pinMode(PINS[i], INPUT_PULLUP);
    candidate[i] = stable[i] = digitalRead(PINS[i]);
    changedAt[i] = millis();
  }
  Serial.begin(115200);
  Serial.println("GUITARHERO PINSCAN v1 GPIO17 GPIO16 GPIO18 GPIO21 GPIO15");
  report();
}
void loop() {
  uint32_t now = millis(); bool changed = false;
  for (uint8_t i=0; i<5; ++i) {
    bool level = digitalRead(PINS[i]);
    if (level != candidate[i]) {candidate[i]=level; changedAt[i]=now;}
    if (candidate[i] != stable[i] && uint32_t(now-changedAt[i]) >= 5) {
      stable[i]=candidate[i]; changed=true;
    }
  }
  if (changed || uint32_t(now-lastReport) >= 250) report();
  delay(1);
}
