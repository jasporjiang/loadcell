#ifndef LOADCELL_H
#define LOADCELL_H

#include <Wire.h>
#include "SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h"

class LoadCell {
private:
    NAU7802 scale;
    int32_t zeroReading;
    double scaleFactor = 0.1 * 9.8 / (23.02 + 0.65) / 10000.0 * 0.98 / 1.21; // N per ADC unit
    TwoWire* wirePort; // Pointer to selected I2C port
    double lastForce = 0.0;

public:
    LoadCell(TwoWire& wirePortRef = Wire); // constructor allows choosing I2C bus
    void begin();
    double getForce();
};

#endif
