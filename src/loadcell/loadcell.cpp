#include "loadcell/loadcell.h"

LoadCell::LoadCell(TwoWire& wirePortRef) {
    wirePort = &wirePortRef;
    zeroReading = 0;
}

void LoadCell::begin() {
    wirePort->begin();
    wirePort->setClock(400000); // 400kHz I2C

    if (!scale.begin(*wirePort)) {
        Serial.println("Load cell not detected on selected I2C bus!");
        while (1);
    }

    // Auto-calibrate (3s average)
    long sum = 0;
    int count = 0;
    unsigned long startTime = millis();

    while (millis() - startTime < 3000) {
        if (scale.available()) {
            sum += scale.getReading();
            count++;
        }
        delay(10);
    }

    zeroReading = (count > 0) ? sum / count : 0;
    Serial.print("Zero reading: ");
    Serial.println(zeroReading);
}

double LoadCell::getForce() {
    if (scale.available()) {
        int32_t currentReading = scale.getReading();
        int32_t difference = currentReading - zeroReading;
        lastForce = (double)difference * scaleFactor;
        return lastForce;
    }
    return lastForce;
}
