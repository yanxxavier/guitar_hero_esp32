// CONFIG v11. Optional upgrade: configurable pins + Tilt persisted in ESP32 NVS.
// Normally-open switches to GND. Keep GPIO12 and GPIO15 released at boot.
#include <Preferences.h>
Preferences prefs;
constexpr uint8_t N = 9;
constexpr uint8_t DEFAULTS[N] = {16,21,27,17,18,12,13,4,19};
constexpr uint8_t DEFAULT_TILT = 15;
constexpr uint16_t BITS[N] = {1,4,8,16,32,2,256,64,128};
uint8_t pins[N];
uint8_t tiltPin = DEFAULT_TILT;
bool candidate[N], stable[N];
bool tiltCandidate = HIGH, tiltStable = HIGH;
uint32_t changedAt[N], tiltChangedAt = 0, lastReport, lastSample;
uint16_t whammy, reportedWhammy;
String command;
bool validPin(int p) {
  // GPIO12 and GPIO15 are boot straps; keep switches released when the board resets.
  const uint8_t allowed[] = {4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33};
  for (uint8_t a : allowed) if (p == a) return true;
  return false;
}
bool validPins(const uint8_t *values) {
  for (int i=0;i<N;i++) {
    if (!validPin(values[i])) return false;
    for (int j=0;j<i;j++) if (values[i]==values[j]) return false;
  }
  return true;
}
void configure() {
  for (int i=0;i<N;i++) {
    pinMode(pins[i],INPUT_PULLUP);
    candidate[i]=stable[i]=digitalRead(pins[i]);
    changedAt[i]=millis();
  }
  pinMode(tiltPin,INPUT_PULLUP);
  tiltCandidate=tiltStable=digitalRead(tiltPin);
  tiltChangedAt=millis();
}
void reportPins() {
  Serial.print("PINS ");
  for (int i=0;i<N;i++) { if (i) Serial.print(','); Serial.print(pins[i]); }
  Serial.println();
}
void reportTilt() {
  Serial.printf("TILT %u\n", tiltPin);
}
void report() {
  uint16_t mask=0;
  for (int i=0;i<N;i++) if (stable[i]==LOW) mask|=BITS[i];
  Serial.printf("STATE %u %u\n",mask,whammy);
  Serial.printf("TILT_STATE %u\n", tiltStable == LOW ? 1 : 0);
  reportedWhammy=whammy;
  lastReport=millis();
}
void processCommand() {
  if (command=="GET PINS") { reportPins(); return; }
  if (command=="GET TILT") { reportTilt(); Serial.printf("TILT_STATE %u\n", tiltStable == LOW ? 1 : 0); return; }
  if (command.startsWith("CFG TILT ")) {
    String token = command.substring(9);
    if (!token.length() || token.length()>2) { Serial.println("ERR TILT"); return; }
    for (int j=0;j<token.length();j++) if (!isDigit(token[j])) { Serial.println("ERR TILT"); return; }
    int nextTilt = token.toInt();
    if (!validPin(nextTilt)) { Serial.println("ERR TILT"); return; }
    if (!prefs.putUChar("tilt", (uint8_t)nextTilt)) { Serial.println("ERR SAVE"); return; }
    pinMode(tiltPin, INPUT);
    tiltPin = (uint8_t)nextTilt;
    pinMode(tiltPin, INPUT_PULLUP);
    tiltCandidate = tiltStable = digitalRead(tiltPin);
    tiltChangedAt = millis();
    reportTilt();
    Serial.printf("TILT_STATE %u\n", tiltStable == LOW ? 1 : 0);
    return;
  }
  if (!command.startsWith("CFG PINS ")) { Serial.println("ERR COMMAND"); return; }
  uint8_t next[N]; int index=9;
  for (int i=0;i<N;i++) {
    int end=command.indexOf(',',index);
    if (i<N-1 && end<0) { Serial.println("ERR PINS"); return; }
    if (i==N-1) end=command.length();
    String token=command.substring(index,end);
    if (!token.length() || token.length()>2) { Serial.println("ERR PINS"); return; }
    for (int j=0;j<token.length();j++) if (!isDigit(token[j])) { Serial.println("ERR PINS"); return; }
    next[i]=token.toInt(); index=end+1;
  }
  if (!validPins(next)) { Serial.println("ERR PINS"); return; }
  if (prefs.putBytes("pins",next,N)!=N) { Serial.println("ERR SAVE"); return; }
  for (int i=0;i<N;i++) pinMode(pins[i],INPUT);
  memcpy(pins,next,N); configure();
  reportPins(); report();
}
void setup() {
  memcpy(pins,DEFAULTS,N);
  prefs.begin("guitarlab",false);
  uint8_t stored[N];
  if (prefs.getBytesLength("pins")==N && prefs.getBytes("pins",stored,N)==N && validPins(stored)) memcpy(pins,stored,N);
  uint8_t storedTilt = prefs.getUChar("tilt", DEFAULT_TILT);
  if (validPin(storedTilt)) tiltPin = storedTilt;
  configure(); analogReadResolution(12); analogSetPinAttenuation(34,ADC_11db);
  whammy=analogRead(34); lastSample=millis(); command.reserve(128);
  Serial.begin(115200);
  Serial.println("GUITARHERO CONFIG v11"); reportPins(); reportTilt(); report();
}
void loop() {
  uint32_t now=millis(); bool changed=false;
  for (int i=0;i<N;i++) {
    bool level=digitalRead(pins[i]);
    if (level!=candidate[i]) { candidate[i]=level; changedAt[i]=now; }
    if (candidate[i]!=stable[i] && uint32_t(now-changedAt[i])>=5) { stable[i]=candidate[i]; changed=true; }
  }
  bool tiltLevel = digitalRead(tiltPin);
  if (tiltLevel != tiltCandidate) { tiltCandidate = tiltLevel; tiltChangedAt = now; }
  if (tiltCandidate != tiltStable && uint32_t(now - tiltChangedAt) >= 200) { tiltStable = tiltCandidate; changed = true; }
  if (uint32_t(now-lastSample)>=5) { whammy=(3*uint32_t(whammy)+analogRead(34))/4; lastSample=now; }
  if (changed || (abs(int(whammy)-int(reportedWhammy))>=12 && uint32_t(now-lastReport)>=20) || uint32_t(now-lastReport)>=250) report();
  while (Serial.available()) {
    char c=Serial.read();
    if (c=='\n') { processCommand(); command=""; }
    else if (c!='\r') { if (command.length()<127) command+=c; else command=""; }
  }
  delay(1);
}
