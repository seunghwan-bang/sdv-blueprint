//*******************************************************************************
// Project : 11 Buzzer in Sensor Kit
// Board : Arduino Uno 
// By : Kit Plus
//*******************************************************************************

int DigitalPin = 7;  // Digital input
bool condition = true;

void setup()
{
    pinMode(DigitalPin, OUTPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop()
{
    if (Serial.available() > 0) {
        condition = !condition;
        Serial.println(condition);
    }

    if (!condition) {
        digitalWrite(DigitalPin, LOW);
        delay(1000);
    } else {
        digitalWrite(DigitalPin, HIGH);
        delay(1000);
    }
}