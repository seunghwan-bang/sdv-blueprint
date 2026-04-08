int pin = 7;
int value = 0;

void setup() {
    pinMode(pin, INPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop() {
    value = digitalRead(pin);
    Serial.println(value);
    delay(500);
}
