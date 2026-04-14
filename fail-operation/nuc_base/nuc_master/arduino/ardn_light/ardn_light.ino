int analogPin = A0;
int digitalPin = 7;

void setup() {
    pinMode(digitalPin, OUTPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop() {
    float cds = analogRead(analogPin);
    cds = map(cds,0,1023,0,100);
    cds = constrain(cds, 0, 100);
    Serial.print("value: ");
    Serial.println(cds);
    
    if (cds > 30) {
        digitalWrite(digitalPin, HIGH);
    } else {
        digitalWrite(digitalPin, LOW);
    }
    
    delay(250);
}
