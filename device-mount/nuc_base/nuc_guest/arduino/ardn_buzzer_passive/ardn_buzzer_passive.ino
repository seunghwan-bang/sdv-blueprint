//*******************************************************************************
// Project : 12 Passive Buzzer in Sensor Kit
// Board : Arduino Uno 
// By : Kit Plus
//*******************************************************************************
#include <Adafruit_NeoPixel.h>

#define BUZZER_PIN 7
#define LED_PIN 6
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const uint32_t RED = Adafruit_NeoPixel::Color(255, 0, 0);
const uint32_t OFF = 0;

void setup()
{
    strip.setBrightness(100);
    strip.begin();
    showAll(OFF);

    pinMode(BUZZER_PIN, OUTPUT);
    Serial.begin(115200);
    while (!Serial) { }
}

void showAll(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void showHalf(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels() / 2; i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void loop()
{
    if (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '1') {
            tone(BUZZER_PIN, 1000); // 1000Hz ON
            showHalf(RED);
        } else if (c == '0') {
            noTone(BUZZER_PIN);     // OFF
            showAll(OFF);
        }
    }

    delay(1);
}
