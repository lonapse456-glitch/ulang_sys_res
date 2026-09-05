#ifndef TB6612FNG_XCR_H
#define TB6612FNG_XCR_H

#include "Arduino.h"

class TB6612FNG_XCR {
public:
    TB6612FNG_XCR();

    void attach(int pwmPin, int in1Pin, int in2Pin, const char* name = "");
    void setStandbyPin(int stbyPin);

    void write(int speed);
    void stop();
    void brake();
    int read();

    void invert(bool inv = true);
    void setMaxSpeed(int maxSpeed);
    void setMinSpeed(int minSpeed);

    void disable();
    void enable();

    void debugOn();
    void debugOff();

    void manual(uint8_t in1State, uint8_t in2State, uint8_t pwm, unsigned long duration);

    void enableSumoMode(TB6612FNG_XCR* leftMotor, TB6612FNG_XCR* rightMotor);
    void disableSumoMode();
    void sumoControl(int leftSpeed, int rightSpeed);

private:
    int _pwmPin, _in1Pin, _in2Pin;
    int _stbyPin = -1;

    bool _attached;
    bool _inverted;
    bool _enabled;

    int _currentSpeed;
    int _maxSpeed;
    int _minSpeed;

    const char* _name;
    bool _debug;

    bool _sumoMode;
    TB6612FNG_XCR* _leftMotor;
    TB6612FNG_XCR* _rightMotor;

    void drive(int speed);
};

#endif
