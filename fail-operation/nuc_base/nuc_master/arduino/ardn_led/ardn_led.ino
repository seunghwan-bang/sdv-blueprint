#include <Adafruit_NeoPixel.h>
#define PIN 6
#define N_LEDS 8

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, PIN, NEO_GRB + NEO_KHZ800);

const uint32_t RED = Adafruit_NeoPixel::Color(255, 0, 0);
const uint32_t GREEN = Adafruit_NeoPixel::Color(0, 255, 0);
const uint32_t OFF = 0;

void showAll(uint32_t c) {
    for (uint16_t i = 0; i < strip.numPixels(); i++) {
        strip.setPixelColor(i, c);
    }
    strip.show();
}

void setup() {
    strip.setBrightness(100);
    strip.begin();
    showAll(OFF);
    Serial.begin(115200);
    while (!Serial) { }
}

void loop() {
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        
        if (cmd == "GREEN") {
            showAll(GREEN);
        } else if (cmd == "RED") {
            showAll(RED);
        } else if (cmd == "OFF") {
            showAll(OFF);
        }
    }
    delay(10);
}
