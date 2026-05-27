//*******************************************************************************
// Project : LED Control for normal sleep-based scheduling
// Board : Arduino Uno R4 WiFi
// Description : Receives signal from container (sleep-based) and toggles LED
//               This device runs without TIMPANI RT scheduling
//*******************************************************************************
#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

const uint32_t GREEN = Adafruit_NeoPixel::Color(0, 255, 0);  // 일반용은 초록색
const uint32_t OFF = 0;

bool ledOn = false;

void setup() {
    strip.setBrightness(100);
    strip.begin();
    showAll(OFF);

    Serial.begin(115200);
    while (!Serial) { }
    Serial.println("LED Normal Ready - Waiting for signals...");
}

void showAll(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void loop() {
    if (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '1') {
            ledOn = !ledOn;  // 토글
            showAll(ledOn ? GREEN : OFF);
        } else if (c == '0') {
            ledOn = false;
            showAll(OFF);
        }
    }
    delay(1);
}
