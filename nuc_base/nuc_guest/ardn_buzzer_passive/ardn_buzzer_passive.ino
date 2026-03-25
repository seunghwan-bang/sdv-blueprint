//*******************************************************************************
// Project : 12 Passive Buzzer in Sensor Kit
// Board : Arduino Uno 
// By : Kit Plus
//*******************************************************************************

int DigitalPin = 7;  // Digital input

void setup()
{
    pinMode(DigitalPin, OUTPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop()
{
    int i;
    for (i = 0; i <80; i++) {
        digitalWrite(DigitalPin, HIGH);
        delay (1); // Delay 1ms
        digitalWrite(DigitalPin, LOW);
        delay (1); // delay 1ms
    }
    delay(1000);

    for (i = 0; i <100; i++) {
        digitalWrite(DigitalPin, HIGH) ;
        delay(2); // delay 2ms
        digitalWrite(DigitalPin, LOW) ;
        delay(2); // delay 2ms
    }
    delay(1000);
}