//*******************************************************************************
// Project : 11 Buzzer in Sensor Kit
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
    digitalWrite(DigitalPin, HIGH);
    delay(100);
    digitalWrite(DigitalPin, LOW);
    delay(10000);
}
