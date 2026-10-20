// CONFIG v11. Optional upgrade: configurable pins persisted in ESP32 NVS.
// Normally-open switches to GND. Keep GPIO15 released at boot.
#include <Preferences.h>
Preferences prefs;
constexpr uint8_t N = 9;
constexpr uint8_t DEFAULTS[N] = {21,18,16,17,15,14,27,13,26};
constexpr uint16_t BITS[N] = {1,4,8,16,32,2,256,64,128};
uint8_t pins[N];
bool candidate[N], stable[N];
uint32_t changedAt[N], lastReport, lastSample;
uint16_t whammy, reportedWhammy;
String command;
bool validPin(int p) {
  const uint8_t allowed[] = {13,14,15,16,17,18,19,21,22,23,25,26,27,32,33};
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
}
void reportPins() {
  Serial.print("PINS ");
  for (int i=0;i<N;i++) { if (i) Serial.print(','); Serial.print(pins[i]); }
  Serial.println();
}
void report() {
  uint16_t mask=0;
  for (int i=0;i<N;i++) if (stable[i]==LOW) mask|=BITS[i];
  Serial.printf("STATE %u %u\n",mask,whammy);
  reportedWhammy=whammy;
  lastReport=millis();
}
void processCommand() {
  if (command=="GET PINS") { reportPins(); return; }
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
  configure(); analogReadResolution(12); analogSetPinAttenuation(34,ADC_11db);
  whammy=analogRead(34); lastSample=millis(); command.reserve(128);
  Serial.begin(115200);
  Serial.println("GUITARHERO CONFIG v11"); reportPins(); report();
}
void loop() {
  uint32_t now=millis(); bool changed=false;
  for (int i=0;i<N;i++) {
    bool level=digitalRead(pins[i]);
    if (level!=candidate[i]) { candidate[i]=level; changedAt[i]=now; }
    if (candidate[i]!=stable[i] && uint32_t(now-changedAt[i])>=5) { stable[i]=candidate[i]; changed=true; }
  }
  if (uint32_t(now-lastSample)>=5) { whammy=(3*uint32_t(whammy)+analogRead(34))/4; lastSample=now; }
  if (changed || (abs(int(whammy)-int(reportedWhammy))>=12 && uint32_t(now-lastReport)>=20) || uint32_t(now-lastReport)>=250) report();
  while (Serial.available()) {
    char c=Serial.read();
    if (c=='\n') { processCommand(); command=""; }
    else if (c!='\r') { if (command.length()<127) command+=c; else command=""; }
  }
  delay(1);
}
