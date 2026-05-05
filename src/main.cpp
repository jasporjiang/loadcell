#include <Arduino.h>
#include "loadcell/loadcell.h"

LoadCell loadCell;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000) {
    delay(10);
  }

  Serial.println("Starting load cell...");
  Serial.println("Keep the load cell unloaded for zero calibration.");
  loadCell.begin();
  Serial.println("Load cell ready.");
}

void loop() {
  double forceN = loadCell.getForce();

  Serial.print("Force: ");
  Serial.print(forceN, 4);
  Serial.println(" N");

  delay(100);
}
