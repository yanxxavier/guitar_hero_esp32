// PINSCAN v3: temporary raw GPIO diagnosis. No game output and no NVS writes.
// Normally open switches to GND, all released at reset. ESP32-WROOM only.
// Exclude flash GPIO6-11 and UART0 GPIO1/3. Input-only GPIO34-39 have no
// pullups: they may float, so only repeated press/release pairs are meaningful.
// GPIO0/2/5/12/15 are boot straps: leave switches released when resetting.
constexpr uint8_t PINS[] = {0,2,4,5,12,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33,34,35,36,39};
constexpr uint8_t N = sizeof(PINS)/sizeof(PINS[0]);
bool candidate[N], stable[N];
uint32_t changedAt[N], lastReport;
void report() {
  uint32_t mask=0;
  for (uint8_t i=0;i<N;i++) if (stable[i]==LOW) mask|=(uint32_t(1)<<i);
  Serial.print("SCAN "); Serial.println(mask);
  lastReport=millis();
}
void setup() {
  for (uint8_t i=0;i<N;i++) {
    pinMode(PINS[i],PINS[i]>=34 ? INPUT : INPUT_PULLUP);
    candidate[i]=stable[i]=digitalRead(PINS[i]);
    changedAt[i]=millis();
  }
  Serial.begin(115200);
  Serial.println("GUITARHERO PINSCAN v3");
  Serial.print("PINS ");
  for (uint8_t i=0;i<N;i++) { if(i) Serial.print(','); Serial.print(PINS[i]); }
  Serial.println(); report();
}
void loop() {
  uint32_t now=millis(); bool changed=false;
  for (uint8_t i=0;i<N;i++) {
    bool level=digitalRead(PINS[i]);
    if (level!=candidate[i]) { candidate[i]=level; changedAt[i]=now; }
    if (candidate[i]!=stable[i] && uint32_t(now-changedAt[i])>=5) {
      stable[i]=candidate[i]; changed=true;
    }
  }
  if (changed || uint32_t(now-lastReport)>=250) report();
  delay(1);
}
